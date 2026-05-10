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
from api.models import StoryRequest

logger = logging.getLogger("scout-streamer")

# Shared session service (in-memory; fine for single-instance Cloud Run)
session_service = InMemorySessionService()


def _sse(data: dict | str) -> str:
    """Format a payload as an SSE data line with double-newline terminator."""
    if isinstance(data, dict):
        return f"data: {json.dumps(data)}\n\n"
    return f"data: {data}\n\n"


def _trace(agent: str, event: str, detail: str | None = None) -> str:
    """Build and format an SSE trace event."""
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
    """
    Build the system header block that the Supervisor uses to determine
    which orchestration mode to execute.
    """
    user_age = (
        datetime.datetime.now().year - request.birth_year
        if request.birth_year
        else 25
    )

    # ── Mode selection ──
    mode = "SCOUTING" if request.is_ready_to_scout else "INTERVIEW"
    header = f"[SYSTEM: MODE | {mode}]\n"

    # ── Biometrics (always include if available) ──
    header += (
        f"[SYSTEM: BIOMETRIC_DATA | Height: {request.height_cm}cm "
        f"| Weight: {request.weight_kg}kg | Age: {user_age}]\n"
    )

    # ── Age Override for Time-Travel ──
    if request.target_game_year and request.birth_year:
        age_at_game = request.target_game_year - request.birth_year
        header += f"[SYSTEM: AGE_OVERRIDE | {age_at_game} (at The {request.target_game_year} Games)]\n"

    # ── Conversation History ──
    if request.conversation_history:
        header += "\n[SYSTEM: CONVERSATION_HISTORY]\n"
        for turn in request.conversation_history:
            header += f"  {turn.role.upper()}: {turn.content}\n"
        header += "[END CONVERSATION_HISTORY]\n"

    header += "\n"
    return header


async def event_generator(request: StoryRequest):
    """
    Async generator that yields SSE events for either INTERVIEW or SCOUTING mode.
    Each yield is followed by asyncio.sleep(0.01) for real-time UI updates.
    """
    mode = "SCOUTING" if request.is_ready_to_scout else "INTERVIEW"

    try:
        # ── 0. Orchestration Intro ──
        if mode == "INTERVIEW":
            intro = (
                "INTERVIEW MODE: The Narrator Agent is reviewing your conversation "
                "and preparing the next question. Compliance will verify it's safe and encouraging."
            )
        else:
            intro = (
                "SCOUTING MODE: Initializing 5-Agent Supervisor Architecture. "
                "The Scout Agent handles biometric cluster-matching, "
                "the Narrator Agent personalizes your story, "
                "the Compliance Agent enforces inclusive standards, "
                "and the Logger Agent narrates each step in real-time."
            )

        yield _trace("supervisor_agent", "OrchestrationIntro", detail=intro)
        await asyncio.sleep(0.01)

        # ── 1. Handshake ──
        yield _trace("supervisor_agent", "RequestReceived")
        await asyncio.sleep(0.01)

        # ── 2. Prepare runner and message ──
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

        yield _trace("supervisor_agent", "AssemblingContext", detail=f"Mode: {mode}")
        await asyncio.sleep(0.01)

        # ── 3. Stream agent events ──
        final_response_text = ""

        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=request.session_id,
            new_message=message,
        ):
            event_type = type(event).__name__

            # Emit trace for named agent events
            if hasattr(event, "agent_name") and event.agent_name:
                yield _trace(event.agent_name, event_type)
                await asyncio.sleep(0.01)
            elif event_type in ("StepEvent", "ContentEvent"):
                yield _trace("supervisor_agent", event_type)
                await asyncio.sleep(0.01)

            # Accumulate content
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_response_text += part.text

        # ── 4. Final result ──
        yield _trace("supervisor_agent", "ResponseFormulated")
        await asyncio.sleep(0.01)

        # Use different type tags so the frontend knows how to handle the response
        result_type = "interview" if mode == "INTERVIEW" else "result"
        yield _sse({"type": result_type, "response": final_response_text})
        await asyncio.sleep(0.01)

        # ── 5. SSE completion signal ──
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"STREAM ERROR: {str(e)}", exc_info=True)
        yield _sse({"type": "error", "detail": str(e)})
        yield "data: [DONE]\n\n"
