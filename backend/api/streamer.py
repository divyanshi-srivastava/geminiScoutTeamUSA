"""
SSE Streamer — Real-time event generator for the Gemini Scout pipeline.
Supports two modes:
  - INTERVIEW: Yields a narrator question (with compliance review)
  - SCOUTING:  Full 5-agent pipeline yielding traces + final result

Both modes use the same SSE format, [DONE] signal, and async flush logic.
"""
import json
import uuid
import asyncio
import datetime
import logging
import os

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.pipeline import scouting_pipeline, interview_pipeline, time_travel_pipeline
from agents.logger_agent import call_logger, call_compliance_diff
from agents.eval_agent import call_eval
from api.models import StoryRequest
from api.context import active_agent

logger = logging.getLogger("scout-streamer")

# ── Content rules loaded once at startup ──
_CONTENT_RULES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "agents", "data", "content_rules.json"
)
with open(_CONTENT_RULES_PATH) as _f:
    _CONTENT_RULES: dict = json.load(_f)

_FORBIDDEN_TERMS: list[str] = _CONTENT_RULES.get("forbidden_terms", [])
_EVAL_CRITERIA: list[dict] = _CONTENT_RULES.get("eval_criteria", [])

session_service = InMemorySessionService()

_GAMES_DISPLAY_NAME: dict[int, str] = {
    1960: "The Rome 1960 Games",
    1964: "The Tokyo 1964 Games",
    1968: "The Mexico City 1968 Games",
    1972: "The Munich 1972 Games",
    1976: "The Montreal 1976 Games",
    1980: "The Moscow 1980 Games",
    1984: "The Los Angeles 1984 Games",
    1988: "The Seoul 1988 Games",
    1992: "The Barcelona 1992 Games",
    1996: "The Atlanta 1996 Games",
    2000: "The Sydney 2000 Games",
    2002: "The Salt Lake City 2002 Games",
    2004: "The Athens 2004 Games",
    2006: "The Turin 2006 Games",
    2008: "The Beijing 2008 Games",
    2010: "The Vancouver 2010 Games",
    2012: "The London 2012 Games",
    2014: "The Sochi 2014 Games",
    2016: "The Rio 2016 Games",
    2018: "The PyeongChang 2018 Games",
    2020: "The Tokyo 2020 Games",
    2022: "The Beijing 2022 Games",
    2024: "The Paris 2024 Games",
    2026: "The Milano Cortina 2026 Games",
    2028: "The LA28 Games",
    2030: "The French Alps 2030 Games",
    2032: "The Brisbane 2032 Games",
    2034: "The Salt Lake City 2034 Games",
    2036: "The Ahmedabad 2036 Games",
    2040: "The Doha 2040 Games",
    2044: "The Istanbul 2044 Games",
}


def _games_name(year: int) -> str:
    return _GAMES_DISPLAY_NAME.get(year, f"The {year} Games")

def _sse(data: dict | str) -> str:
    if isinstance(data, dict):
        return f"data: {json.dumps(data)}\n\n"
    return f"data: {data}\n\n"


def _trace(
    agent: str,
    event: str,
    detail: str | None = None,
    before: str | None = None,
    after: str | None = None,
) -> str:
    payload: dict = {
        "type": "trace",
        "agent": agent,
        "event": event,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
    }
    if detail:
        payload["detail"] = detail
    if before is not None:
        payload["before"] = before
    if after is not None:
        payload["after"] = after
    return _sse(payload)


def _json_equal(a: str, b: str) -> bool:
    """Semantic JSON equality — ignores whitespace/formatting differences."""
    try:
        return json.loads(a) == json.loads(b)
    except Exception:
        return a.strip() == b.strip()


def _output_shape(text: str) -> str:
    """Classify the structural shape of an agent output for hallucination detection.

    Compliance should preserve narrator's response shape. If shapes diverge,
    compliance has invented content and we must fall back to narrator's draft.
    """
    if not text or not text.strip():
        return "empty"
    try:
        d = json.loads(text)
    except Exception:
        return "non-json"
    if isinstance(d, list):
        if d and isinstance(d[0], dict) and "matched_profile_id" in d[0]:
            return "scout-array"
        return "array"
    if isinstance(d, dict):
        if "era_ready_to_scout" in d:
            return "era-signal"
        if "question" in d:
            return "question"
        if "matched_profile_id" in d:
            return "scout-object"
        return "object"
    return "scalar"


# Pipeline contract: which SSE event type each pipeline is permitted to emit.
# This is the single source of truth for emit type — never derived from output shape.
_PIPELINE_EMIT_TYPE = {
    "scouting_pipeline":     "result",
    "interview_pipeline":    "interview",
    "time_travel_pipeline":  "interview",
}


def _get_life_stage(age: int) -> str:
    if age < 20:   return "Rising Star"
    if age <= 32:  return "Elite Peak"
    if age <= 45:  return "Veteran"
    return "Legacy"


def _build_system_header(request: StoryRequest) -> str:
    user_age = (
        datetime.datetime.now().year - request.birth_year
        if request.birth_year
        else 25
    )

    # Mode resolution: time travel mini-interview takes priority
    if request.target_game_year and not request.is_ready_to_scout:
        mode = "TIME_TRAVEL_INTERVIEW"
    elif request.is_ready_to_scout:
        mode = "SCOUTING"
    else:
        mode = "INTERVIEW"

    header = f"[SYSTEM: MODE | {mode}]\n"
    gender_str = f" | Gender: {request.gender}" if request.gender else ""
    header += (
        f"[SYSTEM: BIOMETRIC_DATA | Height: {request.height_cm}cm "
        f"| Weight: {request.weight_kg}kg | Age: {user_age}{gender_str}]\n"
    )

    if request.target_game_year and request.birth_year:
        age_at_game = request.target_game_year - request.birth_year
        life_stage = _get_life_stage(age_at_game)
        games_display = _games_name(request.target_game_year)
        header += (
            f"[SYSTEM: TIME_TRAVEL | Destination: {games_display} "
            f"| User age at destination: {age_at_game} | Life stage: {life_stage}]\n"
        )
        if request.is_ready_to_scout:
            header += f"[SYSTEM: AGE_OVERRIDE | {age_at_game} (at {games_display})]\n"

    if hasattr(request, 'era_history') and request.era_history:
        header += "[SYSTEM: ERA_HISTORY]\n"
        for year, summary in request.era_history.items():
            header += f"  {year} Games: {summary}\n"
        header += "[END ERA_HISTORY]\n"

    if hasattr(request, 'era_context_summary') and request.era_context_summary:
        cs = request.era_context_summary
        header += "[SYSTEM: ERA_CONTEXT]\n"
        if cs.get('life_context'):
            header += f"  Life context: {cs['life_context']}\n"
        if cs.get('physical_context'):
            header += f"  Physical context: {cs['physical_context']}\n"
        if cs.get('athletic_engagement'):
            header += f"  Athletic engagement: {cs['athletic_engagement']}\n"
        if cs.get('signals'):
            header += f"  Signals: {', '.join(cs['signals'])}\n"
        header += "[END ERA_CONTEXT]\n"

    if request.conversation_history:
        header += "\n[SYSTEM: CONVERSATION_HISTORY]\n"
        for turn in request.conversation_history:
            header += f"  {turn.role.upper()}: {turn.content}\n"
        header += "[END CONVERSATION_HISTORY]\n"

    header += f"\n[SYSTEM: CONTENT_RULES]\n"
    header += f"  FORBIDDEN_TERMS: {', '.join(_FORBIDDEN_TERMS)}\n"
    if mode == "SCOUTING":
        criteria_ids = [c["id"] for c in _EVAL_CRITERIA]
        header += f"  EVAL_CRITERIA: {', '.join(criteria_ids)}\n"
    header += "[END CONTENT_RULES]\n"

    header += "\n"
    return header


def _quick_summary(agent_name: str, content: str, question_num: int = 0) -> str:
    """Extract key facts from agent output to feed the logger as context."""
    try:
        data = json.loads(content)
        if agent_name == "scout_agent" and isinstance(data, list) and data:
            p1 = data[0]
            p2 = data[1] if len(data) > 1 else data[0]
            return (
                f"Standing match: {p1.get('matched_profile_name')} | "
                f"pathway: {p1.get('pathway_standing')} | "
                f"Adaptive match: {p2.get('matched_profile_name')} | "
                f"pathway: {p2.get('pathway_adaptive')}"
            )
        if agent_name == "narrator_agent":
            if isinstance(data, list) and data:
                v = data[0].get("scout_verdict", "")
                return (
                    f"Narratives written for: {data[0].get('matched_profile_name')}. "
                    f"Verdict preview: {v[:120]}"
                )
            if isinstance(data, dict) and data.get("question"):
                q_label = f"Q{question_num}: " if question_num else ""
                feedback = data.get("feedback", "")
                ready = data.get("ready_to_proceed", False)
                return (
                    f"{q_label}Question: \"{data['question'][:100]}\" | "
                    f"Feedback given: \"{feedback[:60]}\" | "
                    f"Ready-to-proceed offered: {'yes' if ready else 'no'}"
                )
        if agent_name == "compliance_agent":
            if isinstance(data, list) and data:
                names = [p.get("matched_profile_name", "?") for p in data]
                return f"Compliance approved {len(data)} profiles: {names}"
            if isinstance(data, dict) and data.get("question"):
                return (
                    f"Question approved: \"{data['question'][:80]}\" | "
                    f"Options: {len(data.get('options', []))}"
                )
    except Exception:
        pass
    return content[:300]


async def event_generator(request: StoryRequest):
    if request.target_game_year and not request.is_ready_to_scout:
        mode = "TIME_TRAVEL_INTERVIEW"
    elif request.is_ready_to_scout:
        mode = "SCOUTING"
    else:
        mode = "INTERVIEW"

    try:
        if mode == "SCOUTING":
            pipeline = scouting_pipeline
        elif mode == "TIME_TRAVEL_INTERVIEW":
            pipeline = time_travel_pipeline
        else:
            pipeline = interview_pipeline

        active_agent.set(pipeline.name)
        _pipeline_agents = [sa.name for sa in getattr(pipeline, "sub_agents", [])]
        _chain_str = " → ".join(_pipeline_agents) if _pipeline_agents else pipeline.name
        logger.info(
            "\n%s\n"
            "  ▶▶ PIPELINE START\n"
            "     mode        → %s\n"
            "     pipeline    → %s\n"
            "     chain       → %s\n"
            "     session     → %s\n"
            "     story_len   → %d chars\n"
            "     q_num       → will be Q%d (narrator turns so far)\n"
            "%s",
            "━" * 64,
            mode,
            pipeline.name,
            _chain_str,
            request.session_id,
            len(request.story or ""),
            sum(1 for t in request.conversation_history if t.role == "narrator") + 1,
            "━" * 64,
        )

        # Pre-create session so we can seed scout_report="" for non-scouting modes.
        # narrator's instruction template uses {scout_report}; the key must exist in
        # session.state or ADK leaves the placeholder unreplaced.
        fresh_session_id = str(uuid.uuid4())
        initial_state = {} if mode == "SCOUTING" else {"scout_report": ""}
        await session_service.create_session(
            app_name="scout_app",
            user_id=request.user_id,
            session_id=fresh_session_id,
            state=initial_state,
        )

        runner = Runner(
            app_name="scout_app",
            agent=pipeline,
            session_service=session_service,
            auto_create_session=False,
        )

        system_header = _build_system_header(request)
        user_text = request.story if request.story else "(No additional input)"
        message = types.Content(
            role="user",
            parts=[types.Part(text=system_header + user_text)],
        )

        # Count how many narrator turns are already in history to label questions
        _question_num = sum(
            1 for t in request.conversation_history if t.role == "narrator"
        ) + 1

        _last_text_parts: list[str] = []
        _seen_agents: set[str] = set()
        _agent_thoughts: dict[str, str] = {}  # accumulated thought tokens per agent
        _event_sequence: list[str] = []  # ordered stream of agent event authors for diagnosis
        _narrator_raw_output: str = ""  # narrator's pre-compliance draft, for before/after diff

        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=fresh_session_id,
            new_message=message,
        ):
            event_author = getattr(event, "author", None)

            # Update ContextVar so every log line printed during this event is labelled
            if event_author:
                active_agent.set(event_author)

            # Record every event for post-loop ordering diagnosis
            if event_author:
                _event_sequence.append(event_author)

            # Extract content — split thought tokens from final text
            content_text = ""
            thought_text = ""
            if hasattr(event, "content") and event.content:
                for p in event.content.parts:
                    if not getattr(p, "text", None):
                        continue
                    if getattr(p, "thought", False):
                        thought_text += p.text
                    else:
                        content_text += p.text

            # Accumulate thoughts per agent for logger
            if thought_text and event_author:
                _agent_thoughts[event_author] = (
                    _agent_thoughts.get(event_author, "") + thought_text
                )

            # Log first activation of each agent
            if event_author and event_author not in _seen_agents:
                _pos = _pipeline_agents.index(event_author) + 1 if event_author in _pipeline_agents else "?"
                _total = len(_pipeline_agents)
                logger.info(
                    "┌─ [%s/%s] AGENT START: %s %s\n"
                    "│  chain    → %s\n"
                    "│  pipeline → %s\n"
                    "└%s",
                    _pos, _total, event_author, "▲" * 3,
                    _chain_str,
                    pipeline.name,
                    "─" * 55,
                )

            # Print full thought to backend terminal
            if thought_text and event_author:
                logger.debug(
                    "\n─── THOUGHT [%s] ───\n%s\n────────────────────",
                    event_author,
                    thought_text.strip(),
                )

            # Emit full thinking trace for the UI (dim italic rows, scrollable in sidebar)
            if thought_text and event_author and event_author is not None:
                yield _trace(event_author, "Thinking", detail=thought_text.strip())
                await asyncio.sleep(0.05)

            # Track first appearance of each agent (used to guard synthetic traces)
            if event_author and event_author not in _seen_agents:
                _seen_agents.add(event_author)

            if not content_text:
                continue

            if event_author in ("scout_agent", "narrator_agent", "compliance_agent"):
                _last_text_parts = [content_text]
                # Capture narrator's raw pre-compliance draft for before/after diff
                if event_author == "narrator_agent":
                    _narrator_raw_output = content_text
                # Call logger directly — interprets accumulated thoughts + output
                thoughts = _agent_thoughts.get(event_author, "")
                summary = _quick_summary(event_author, content_text, _question_num)
                _thought_chars = len(_agent_thoughts.get(event_author, ""))
                _pos = _pipeline_agents.index(event_author) + 1 if event_author in _pipeline_agents else "?"
                _total = len(_pipeline_agents)
                logger.info(
                    "┌─ [%s/%s] AGENT OUTPUT: %s\n"
                    "│  output_chars  → %d\n"
                    "│  thought_chars → %d\n"
                    "│  summary       → %s\n"
                    "│  preview       → %s\n"
                    "└%s",
                    _pos, _total, event_author,
                    len(content_text),
                    _thought_chars,
                    summary[:160],
                    content_text[:200].replace("\n", " ↵ "),
                    "─" * 55,
                )
                logger_text = await call_logger(event_author, thoughts, summary, mode=mode)
                if logger_text:
                    yield _trace(event_author, "Thought", detail=logger_text)
                    await asyncio.sleep(0.05)

            else:
                # Supervisor or unattributed — take-last for final response, no trace
                _last_text_parts = [content_text]

        active_agent.set("—")
        final_response_text = "".join(_last_text_parts)

        # ── Diagnostic: log event stream order ──
        _unique_seq = []
        for _a in _event_sequence:
            if not _unique_seq or _unique_seq[-1] != _a:
                _unique_seq.append(_a)
        logger.info(
            "\n%s\n"
            "  ◀◀ PIPELINE COMPLETE\n"
            "     mode           → %s\n"
            "     pipeline       → %s\n"
            "     agent sequence → %s\n"
            "     events_total   → %d\n"
            "     agents_seen    → %s\n"
            "     output_chars   → %d\n"
            "%s",
            "━" * 64,
            mode,
            pipeline.name,
            " → ".join(_unique_seq) if _unique_seq else "(empty)",
            len(_event_sequence),
            ", ".join(sorted(_seen_agents)) if _seen_agents else "(none)",
            len(final_response_text),
            "━" * 64,
        )

        # ── Compliance synthetic trace (fallback only) ──
        # With SequentialAgent, compliance now appears as its own event_author and is
        # already logged in the event loop. Only emit synthetic trace if it was absorbed.
        active_agent.set("compliance_agent")
        if "compliance_agent" not in _seen_agents:
            compliance_summary = _quick_summary("compliance_agent", final_response_text, _question_num)
            compliance_logger = await call_logger("compliance_agent", "", compliance_summary, mode=mode)
            if compliance_logger:
                yield _trace("compliance_agent", "Thought", detail=compliance_logger)
                await asyncio.sleep(0.03)

        # ── Shape validation: detect compliance hallucinations ──
        # Compliance must preserve narrator's response shape. If it transformed a
        # question/era-signal into a scout-array (or any other shape change), it
        # invented content — discard it and fall back to narrator's pre-compliance draft.
        # The frontend's signalEraReadyToScout/looksLikeResult parsers will then handle
        # the recovered narrator output correctly.
        _compliance_hallucinated = False
        if _narrator_raw_output:
            _narr_shape = _output_shape(_narrator_raw_output)
            _final_shape = _output_shape(final_response_text)
            if _narr_shape != _final_shape and _narr_shape not in ("empty", "non-json"):
                _compliance_hallucinated = True
                logger.warning(
                    "\n%s\n"
                    "  ⚠⚠ COMPLIANCE HALLUCINATION DETECTED\n"
                    "     pipeline          → %s\n"
                    "     narrator_shape    → %s\n"
                    "     compliance_shape  → %s\n"
                    "     action            → discarding compliance, reverting to narrator draft\n"
                    "     narrator preview  → %s\n"
                    "     compliance preview→ %s\n"
                    "%s",
                    "!" * 64,
                    pipeline.name,
                    _narr_shape, _final_shape,
                    _narrator_raw_output[:200].replace("\n", " ↵ "),
                    final_response_text[:200].replace("\n", " ↵ "),
                    "!" * 64,
                )
                yield _trace(
                    "compliance_agent",
                    "Hallucination",
                    detail=(
                        f"Compliance changed response shape ({_narr_shape} → {_final_shape}). "
                        f"Reverted to narrator's pre-compliance draft to prevent fabricated output."
                    ),
                    before=_narrator_raw_output,
                    after=final_response_text,
                )
                await asyncio.sleep(0.03)
                final_response_text = _narrator_raw_output

        # ── Before/after diff — only when compliance behaved (preserved shape) ──
        if _narrator_raw_output and not _compliance_hallucinated:
            # Use JSON-semantic equality so whitespace/formatting differences
            # from compliance's re-serialization don't trigger false "Changed" events.
            is_clean = _json_equal(_narrator_raw_output, final_response_text)
            diff_text = await call_compliance_diff(_narrator_raw_output, final_response_text)
            if diff_text:
                event_type = "Approved" if is_clean else "Changed"
                if not is_clean:
                    logger.info(
                        "◉ COMPLIANCE CHANGE DETECTED\n"
                        "  BEFORE: %s\n"
                        "  AFTER:  %s",
                        _narrator_raw_output[:500].replace("\n", " ↵ "),
                        final_response_text[:500].replace("\n", " ↵ "),
                    )
                yield _trace(
                    "compliance_agent",
                    event_type,
                    detail=diff_text,
                    before=_narrator_raw_output if not is_clean else None,
                    after=final_response_text if not is_clean else None,
                )
                await asyncio.sleep(0.03)

        # ── Emit type is determined by pipeline architecture, NOT output shape ──
        # Each pipeline has a contract about what it produces. Shape-based heuristics
        # are dangerous: a hallucinated scout-array inside time_travel_pipeline used to
        # be re-emitted as type:"result", which let fabricated archetypes reach the UI.
        # Pipeline name is the single source of truth.
        result_type = _PIPELINE_EMIT_TYPE.get(pipeline.name, "interview")
        _is_scouting_result = (result_type == "result")
        logger.info(
            "◀ SSE EMIT  type=%-12s  chars=%-6d  pipeline=%s  hallucinated=%s",
            result_type, len(final_response_text), pipeline.name, _compliance_hallucinated,
        )
        yield _sse({"type": result_type, "response": final_response_text})
        await asyncio.sleep(0.01)

        # ── Eval Agent — runs after any confirmed scouting result ──
        if _is_scouting_result:
            active_agent.set("eval_agent")
            logger.info(
                "┌─ [post-pipeline] AGENT START: eval_agent ▲▲▲\n"
                "│  triggered by → scouting result confirmed (is_scouting_result=True)\n"
                "│  pipeline     → %s  (eval runs outside the chain)\n"
                "└%s",
                pipeline.name,
                "─" * 55,
            )
            yield _trace("eval_agent", "Thought", detail="I'm reviewing the pipeline's archetype match quality, narrative personalization, and compliance integrity.")
            await asyncio.sleep(0.05)
            eval_result = await call_eval(
                height_cm=request.height_cm,
                weight_kg=request.weight_kg,
                birth_year=request.birth_year,
                conversation_history=request.conversation_history,
                final_result_json=final_response_text,
                target_game_year=request.target_game_year,
                gender=request.gender,
            )
            if eval_result:
                yield _sse({"type": "eval", "result": eval_result})
                await asyncio.sleep(0.01)

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(
            "\n%s\n"
            "  ✖✖ STREAM ERROR\n"
            "     pipeline → %s\n"
            "     mode     → %s\n"
            "     error    → %s\n"
            "%s",
            "!" * 64,
            pipeline.name if "pipeline" in dir() else "unknown",
            mode if "mode" in dir() else "unknown",
            str(e),
            "!" * 64,
            exc_info=True,
        )
        yield _sse({"type": "error", "detail": str(e)})
        yield "data: [DONE]\n\n"
