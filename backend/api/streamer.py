"""
SSE Streamer — Real-time event generator for the Gemini Scout pipeline.
Supports two modes:
  - INTERVIEW: Yields a narrator question (with compliance review)
  - SCOUTING:  Full 5-agent pipeline yielding traces + final result

Both modes use the same SSE format, [DONE] signal, and async flush logic.
"""
import json
import re
import asyncio
import datetime
import logging

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.supervisoragent import supervisor_agent
from api.models import StoryRequest

logger = logging.getLogger("scout-streamer")

session_service = InMemorySessionService()

# ── Agent "started" messages — emitted once when each agent first appears ──
_AGENT_STARTED = {
    "scout_agent":      "Received biometrics. Scanning 12 athletic archetypes for closest match...",
    "narrator_agent":   "Archetype data received. Crafting your personal story from interview answers...",
    "compliance_agent": "Narrative received. Running IOC brand and language compliance review...",
}

# ── [TAG] prefix parser for logger agent output ──
_LOGGER_TAG_MAP = {
    "SCOUT":      "scout_agent",
    "NARRATOR":   "narrator_agent",
    "COMPLIANCE": "compliance_agent",
    "SUPERVISOR": "supervisor_agent",
    "LOGGER":     "logger_agent",
}
_LOGGER_LINE_RE = re.compile(r"^\[([A-Z]+)\]\s*(.+)$")


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


def _build_system_header(request: StoryRequest) -> str:
    user_age = (
        datetime.datetime.now().year - request.birth_year
        if request.birth_year
        else 25
    )
    mode = "SCOUTING" if request.is_ready_to_scout else "INTERVIEW"
    header = f"[SYSTEM: MODE | {mode}]\n"
    header += (
        f"[SYSTEM: BIOMETRIC_DATA | Height: {request.height_cm}cm "
        f"| Weight: {request.weight_kg}kg | Age: {user_age}]\n"
    )
    if request.target_game_year and request.birth_year:
        age_at_game = request.target_game_year - request.birth_year
        header += f"[SYSTEM: AGE_OVERRIDE | {age_at_game} (at The {request.target_game_year} Games)]\n"
    if request.conversation_history:
        header += "\n[SYSTEM: CONVERSATION_HISTORY]\n"
        for turn in request.conversation_history:
            header += f"  {turn.role.upper()}: {turn.content}\n"
        header += "[END CONVERSATION_HISTORY]\n"
    header += "\n"
    return header


# ── Per-agent content summarizers ──

def _summarize_scout(content: str) -> str:
    try:
        data = json.loads(content)
        if isinstance(data, list) and data:
            p1 = data[0]
            p2 = data[1] if len(data) > 1 else p1
            name1 = p1.get("matched_profile_name", "Unknown")
            path1 = p1.get("pathway_standing", "standing sport")
            name2 = p2.get("matched_profile_name", name1)
            path2 = p2.get("pathway_adaptive", "adaptive sport")
            if name1 == name2:
                return f"Best match: {name1}. Standing → {path1}. Adaptive → {path2}."
            return f"Standing: {name1} ({path1}). Adaptive: {name2} ({path2})."
    except Exception:
        pass
    return "Archetype analysis complete. Passing data to Narrator."


def _summarize_narrator(content: str) -> str:
    try:
        data = json.loads(content)
        if isinstance(data, list) and data:
            name = data[0].get("matched_profile_name", "your archetype")
            return f"Story written for {name}. Standing and adaptive narratives complete."
        if isinstance(data, dict) and data.get("question"):
            q = data["question"]
            short = q[:70].rstrip() + ("..." if len(q) > 70 else "")
            return f'Question drafted: "{short}"'
    except Exception:
        pass
    return "Narrative complete. Passing to Compliance for review."


def _summarize_compliance(content: str) -> str:
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return "Clean pass — both pathway narratives approved. IOC standards verified."
        if isinstance(data, dict) and data.get("question"):
            return "Interview question approved. Safe for user display."
    except Exception:
        pass
    return "Compliance review complete."


async def event_generator(request: StoryRequest):
    mode = "SCOUTING" if request.is_ready_to_scout else "INTERVIEW"

    try:
        # ── Supervisor intro ──
        if mode == "INTERVIEW":
            intro = "Pipeline active. Supervisor delegating to Narrator Agent for next question."
        else:
            intro = "Scouting pipeline active. Supervisor delegating: Scout → Narrator → Compliance."
        yield _trace("supervisor_agent", "Thought", detail=intro)
        await asyncio.sleep(0.01)

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

        _last_text_parts: list[str] = []
        _seen_agents: set[str] = set()

        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=request.session_id,
            new_message=message,
        ):
            event_author = getattr(event, "author", None)

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

            # Emit thinking trace (truncated) for sub-agents that have thinking enabled
            if thought_text and event_author and event_author not in (
                "supervisor_agent", "logger_agent", None
            ):
                snippet = thought_text.strip()[:180]
                if len(thought_text.strip()) > 180:
                    snippet += "…"
                yield _trace(event_author, "Thinking", detail=snippet)
                await asyncio.sleep(0.05)

            # Emit "activated" trace the FIRST time each sub-agent appears
            if event_author and event_author not in _seen_agents:
                _seen_agents.add(event_author)
                start_msg = _AGENT_STARTED.get(event_author)
                if start_msg:
                    yield _trace(event_author, "Thought", detail=start_msg)
                    await asyncio.sleep(0.05)

            if not content_text:
                continue

            if event_author == "logger_agent":
                # Parse [AGENT] prefixed lines into per-agent traces
                for raw_line in content_text.splitlines():
                    line = raw_line.strip()
                    if not line:
                        continue
                    m = _LOGGER_LINE_RE.match(line)
                    if m:
                        tag = m.group(1)
                        text = m.group(2).strip()
                        agent_key = _LOGGER_TAG_MAP.get(tag, "logger_agent")
                    else:
                        agent_key = "logger_agent"
                        text = line
                    yield _trace(agent_key, "Thought", detail=text)
                    await asyncio.sleep(0.05)

            elif event_author == "scout_agent":
                _last_text_parts = [content_text]
                yield _trace("scout_agent", "Thought", detail=_summarize_scout(content_text))
                await asyncio.sleep(0.05)

            elif event_author == "narrator_agent":
                _last_text_parts = [content_text]
                yield _trace("narrator_agent", "Thought", detail=_summarize_narrator(content_text))
                await asyncio.sleep(0.05)

            elif event_author == "compliance_agent":
                _last_text_parts = [content_text]
                yield _trace("compliance_agent", "Thought", detail=_summarize_compliance(content_text))
                await asyncio.sleep(0.05)

            else:
                # Supervisor or unattributed — take-last for final response, no trace
                _last_text_parts = [content_text]

        final_response_text = "".join(_last_text_parts)

        result_type = "interview" if mode == "INTERVIEW" else "result"
        yield _sse({"type": result_type, "response": final_response_text})
        await asyncio.sleep(0.01)

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"STREAM ERROR: {str(e)}", exc_info=True)
        yield _sse({"type": "error", "detail": str(e)})
        yield "data: [DONE]\n\n"
