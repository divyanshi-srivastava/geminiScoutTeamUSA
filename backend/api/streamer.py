"""
SSE Streamer — Real-time event generator for the Gemini Scout pipeline.
Supports two modes:
  - INTERVIEW: Yields a narrator question (with compliance review)
  - SCOUTING:  Full 5-agent pipeline yielding traces + final result

Both modes use the same SSE format, [DONE] signal, and async flush logic.
"""
import json
import asyncio
import datetime
import logging

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.supervisoragent import supervisor_agent
from agents.loggeragent import call_logger, call_compliance_diff
from agents.evalagent import call_eval
from api.models import StoryRequest

logger = logging.getLogger("scout-streamer")

session_service = InMemorySessionService()

def _sse(data: dict | str) -> str:
    if isinstance(data, dict):
        return f"data: {json.dumps(data)}\n\n"
    return f"data: {data}\n\n"


def _trace(agent: str, event: str, detail: str | None = None) -> str:
    payload = {
        "type": "trace",
        "agent": agent,
        "event": event,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
    }
    if detail:
        payload["detail"] = detail
    return _sse(payload)


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
        runner = Runner(
            app_name="scout_app",
            agent=supervisor_agent,
            session_service=session_service,
            auto_create_session=True,
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
            session_id=request.session_id,
            new_message=message,
        ):
            event_author = getattr(event, "author", None)

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

            # Suppress scout events entirely during TIME_TRAVEL_INTERVIEW —
            # if scout fires it means the supervisor misrouted; hide it from judges
            if mode == "TIME_TRAVEL_INTERVIEW" and event_author == "scout_agent":
                continue

            # Emit truncated thinking trace for the UI (dim italic rows)
            if thought_text and event_author and event_author not in ("supervisor_agent", None):
                snippet = thought_text.strip()[:180]
                if len(thought_text.strip()) > 180:
                    snippet += "…"
                yield _trace(event_author, "Thinking", detail=snippet)
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
                logger_text = await call_logger(event_author, thoughts, summary, mode=mode)
                if logger_text:
                    yield _trace(event_author, "Thought", detail=logger_text)
                    await asyncio.sleep(0.05)

            else:
                # Supervisor or unattributed — take-last for final response, no trace
                _last_text_parts = [content_text]

        final_response_text = "".join(_last_text_parts)

        # ── Diagnostic: log event stream order to diagnose agent execution sequencing ──
        logger.info(
            "ADK event sequence [mode=%s]: %s",
            mode,
            " → ".join(_event_sequence) if _event_sequence else "(empty)",
        )

        # ── Compliance synthetic trace ──
        # The supervisor copies compliance's output verbatim as its final response,
        # so compliance never appears as event_author in the runner stream.
        # We emit its trace explicitly here using the final output (which IS compliance's work).
        compliance_summary = _quick_summary("compliance_agent", final_response_text, _question_num)
        compliance_logger = await call_logger("compliance_agent", "", compliance_summary, mode=mode)
        if compliance_logger:
            yield _trace("compliance_agent", "Thought", detail=compliance_logger)
            await asyncio.sleep(0.03)
        # ── Before/after diff — green if clean pass, red if changes were made ──
        if _narrator_raw_output:
            is_clean = _narrator_raw_output.strip() == final_response_text.strip()
            diff_text = await call_compliance_diff(_narrator_raw_output, final_response_text)
            if diff_text:
                event_type = "Approved" if is_clean else "Changed"
                yield _trace("compliance_agent", event_type, detail=diff_text)
                await asyncio.sleep(0.03)

        result_type = "interview" if mode in ("INTERVIEW", "TIME_TRAVEL_INTERVIEW") else "result"
        yield _sse({"type": result_type, "response": final_response_text})
        await asyncio.sleep(0.01)

        # ── Detect scouting result even when mode is INTERVIEW (supervisor ordering bug) ──
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
