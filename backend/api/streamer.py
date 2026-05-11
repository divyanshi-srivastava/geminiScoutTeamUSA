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

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.pipeline import scouting_pipeline, interview_pipeline, time_travel_pipeline
from agents.logger_agent import call_logger, call_compliance_diff
from agents.eval_agent import call_eval
from api.models import StoryRequest
from api.context import active_agent

logger = logging.getLogger("scout-streamer")

session_service = InMemorySessionService()

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
        header += (
            f"[SYSTEM: TIME_TRAVEL | Destination: The {request.target_game_year} Games "
            f"| User age at destination: {age_at_game} | Life stage: {life_stage}]\n"
        )
        if request.is_ready_to_scout:
            header += f"[SYSTEM: AGE_OVERRIDE | {age_at_game} (at The {request.target_game_year} Games)]\n"

    if hasattr(request, 'era_history') and request.era_history:
        header += "[SYSTEM: ERA_HISTORY]\n"
        for year, summary in request.era_history.items():
            header += f"  {year} Games: {summary}\n"
        header += "[END ERA_HISTORY]\n"

    if request.conversation_history:
        header += "\n[SYSTEM: CONVERSATION_HISTORY]\n"
        for turn in request.conversation_history:
            header += f"  {turn.role.upper()}: {turn.content}\n"
        header += "[END CONVERSATION_HISTORY]\n"
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
        logger.info("▶ PIPELINE START  mode=%-24s pipeline=%s", mode, pipeline.name)

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
                logger.info("◆ AGENT ACTIVATED  %s", event_author)

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
                logger.info("◉ OUTPUT SUMMARY   %s → %s", event_author, summary[:120])
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
        logger.info(
            "◀ EVENT SEQUENCE   [mode=%s] %s",
            mode,
            " → ".join(_event_sequence) if _event_sequence else "(empty)",
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
        # ── Before/after diff — green if clean pass, red if changes were made ──
        if _narrator_raw_output:
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

        result_type = "interview" if mode in ("INTERVIEW", "TIME_TRAVEL_INTERVIEW") else "result"
        yield _sse({"type": result_type, "response": final_response_text})
        await asyncio.sleep(0.01)

        # ── Detect scouting result even when mode flag disagrees with actual output ──
        _is_scouting_result = mode == "SCOUTING"
        if not _is_scouting_result:
            try:
                _d = json.loads(final_response_text)
                if isinstance(_d, list) and len(_d) > 0 and "matched_profile_id" in _d[0]:
                    _is_scouting_result = True
            except Exception:
                pass

        # ── Eval Agent — runs after any confirmed scouting result ──
        if _is_scouting_result:
            active_agent.set("eval_agent")
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
        logger.error(f"STREAM ERROR: {str(e)}", exc_info=True)
        yield _sse({"type": "error", "detail": str(e)})
        yield "data: [DONE]\n\n"
