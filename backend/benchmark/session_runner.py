"""
Session Runner — drives one persona through the full interview → scouting → eval flow
by hitting the live backend HTTP API. Parses SSE events from the /scout endpoint.

Time travel personas: after `time_travel_trigger_after` normal interview questions,
the runner sends one TIME_TRAVEL_INTERVIEW request (target_game_year set, is_ready_to_scout=False),
answers the era question, then scouts with target_game_year.
"""
import json
import uuid
import logging
import httpx

from benchmark.answer_agent import pick_answer

logger = logging.getLogger("benchmark.session_runner")

_HTTPX_TIMEOUT = httpx.Timeout(180.0, connect=10.0)


async def _stream_request(client: httpx.AsyncClient, url: str, body: dict) -> dict:
    """
    Opens one SSE connection, drains all events, returns:
      {
        "interview": <parsed Question dict> | None,
        "result":    <parsed scouting list> | None,
        "eval":      <eval dict> | None,
      }
    Traces are discarded (they're UI-only).
    """
    collected = {"interview": None, "result": None, "eval": None, "error": None}

    async with client.stream("POST", url, json=body, timeout=_HTTPX_TIMEOUT) as resp:
        resp.raise_for_status()
        async for raw_line in resp.aiter_lines():
            if not raw_line.startswith("data: "):
                continue
            payload = raw_line[6:]
            if payload == "[DONE]":
                break
            try:
                event = json.loads(payload)
            except Exception:
                continue

            etype = event.get("type")
            if etype == "interview":
                try:
                    collected["interview"] = json.loads(event["response"])
                except Exception:
                    collected["interview"] = {
                        "question": event.get("response", ""),
                        "options": [],
                        "ready_to_proceed": False,
                    }
            elif etype == "result":
                try:
                    collected["result"] = json.loads(event["response"])
                except Exception:
                    collected["result"] = event.get("response")
            elif etype == "eval":
                collected["eval"] = event.get("result")
            elif etype == "error":
                collected["error"] = event.get("detail", "unknown backend error")
                logger.error("  BACKEND ERROR: %s", collected["error"])

    return collected


def _append_narrator_turn(history: list, question: dict) -> None:
    """Adds narrator turn with options inline (so eval can see question quality)."""
    options = question.get("options", [])
    options_text = (
        "\nOptions: [" + " | ".join(options) + "]"
        if options else ""
    )
    history.append({
        "role": "narrator",
        "content": question["question"] + options_text,
    })


async def run_persona(persona: dict, backend_url: str) -> dict:
    """
    Returns a result dict with keys:
      persona_id, persona_label, biometrics,
      conversation_log, scouting_result, eval_result,
      error (only on failure)
    """
    scout_url = f"{backend_url.rstrip('/')}/scout"
    session_id = str(uuid.uuid4())
    user_id = f"benchmark_{persona['id']}"

    conversation_history: list = []
    question_count = 0
    max_questions = persona.get("max_questions", 4)
    target_game_year = persona.get("target_game_year")
    time_travel_trigger = persona.get("time_travel_trigger_after", 9999)

    def _body(story: str, *, is_scout: bool = False, include_era: bool = False) -> dict:
        b: dict = {
            "story": story,
            "session_id": session_id,
            "user_id": user_id,
            "height_cm": persona["height_cm"],
            "weight_kg": persona["weight_kg"],
            "birth_year": persona["birth_year"],
            "gender": persona.get("gender"),
            "conversation_history": [dict(t) for t in conversation_history],
            "is_ready_to_scout": is_scout,
        }
        if include_era and target_game_year:
            b["target_game_year"] = target_game_year
        if is_scout and target_game_year:
            b["target_game_year"] = target_game_year
        return b

    logger.info("▶ START  persona=%-40s  target_era=%s", persona["id"], target_game_year or "—")

    async with httpx.AsyncClient() as client:

        # ── Phase 1: Initial metrics → first narrator question ──
        events = await _stream_request(client, scout_url, _body("Initial metrics provided."))
        question = events.get("interview")

        if not question:
            msg = "No initial question received from backend"
            logger.error("  FAIL %s: %s", persona["id"], msg)
            return _error_result(persona, msg)

        _append_narrator_turn(conversation_history, question)

        # ── Phase 2: Interview loop ──
        while question_count < max_questions:
            answer = await pick_answer(persona, question, conversation_history)
            conversation_history.append({"role": "user", "content": answer})
            question_count += 1

            logger.info(
                "  Q%-2d  q=%-55s  a=%s",
                question_count,
                (question["question"][:55] + "…") if len(question["question"]) > 55 else question["question"],
                answer[:50],
            )

            # After time_travel_trigger questions: send TIME_TRAVEL_INTERVIEW turn
            if target_game_year and question_count >= time_travel_trigger:
                logger.info("  ⏳ Triggering TIME_TRAVEL_INTERVIEW (era=%d)", target_game_year)
                events = await _stream_request(
                    client, scout_url,
                    _body(answer, include_era=True)
                )
                era_q = events.get("interview")
                if era_q:
                    _append_narrator_turn(conversation_history, era_q)
                    era_answer = await pick_answer(persona, era_q, conversation_history)
                    conversation_history.append({"role": "user", "content": era_answer})
                    logger.info("  ERA Q  a=%s", era_answer[:60])
                break  # era question answered — move straight to scouting

            # Narrator offered ready-to-proceed and we've had enough turns: scout now
            if question.get("ready_to_proceed") and question_count >= 2:
                logger.info("  ready_to_proceed offered at Q%d — moving to scouting", question_count)
                break

            # Hit max_questions: scout now
            if question_count >= max_questions:
                break

            # Continue interview
            events = await _stream_request(client, scout_url, _body(answer))
            question = events.get("interview")
            if not question:
                logger.warning("  No follow-up question at Q%d — moving to scouting", question_count)
                break
            _append_narrator_turn(conversation_history, question)

        # ── Phase 3: Scouting ──
        logger.info(
            "  ◆ Scouting  history=%d turns  era=%s",
            len(conversation_history),
            target_game_year or "—",
        )
        scout_events = await _stream_request(
            client, scout_url,
            _body("", is_scout=True)
        )

    scouting_result = scout_events.get("result")
    eval_result = scout_events.get("eval")
    backend_error = scout_events.get("error")

    if backend_error:
        logger.error("  SCOUTING FAILED  persona=%s  error=%s", persona["id"], backend_error)
    elif scouting_result is None:
        logger.warning("  SCOUTING RETURNED NOTHING  persona=%s  (no result or error event received)", persona["id"])
    elif eval_result is None:
        logger.warning("  EVAL MISSING  persona=%s  (scouting OK but no eval event — eval agent likely failed)", persona["id"])

    overall = eval_result.get("overall", "—") if eval_result else "N/A"
    iq = (eval_result.get("interview_quality") or {}).get("score", "—") if eval_result else "—"
    logger.info(
        "✓ DONE  persona=%-40s  overall=%s  IQ=%s",
        persona["id"], overall, iq,
    )

    return {
        "persona_id": persona["id"],
        "persona_label": persona["label"],
        "biometrics": {
            "height_cm": persona["height_cm"],
            "weight_kg": persona["weight_kg"],
            "birth_year": persona["birth_year"],
            "gender": persona.get("gender"),
        },
        "conversation_log": conversation_history,
        "scouting_result": scouting_result,
        "eval_result": eval_result,
        "backend_error": backend_error,
    }


def _error_result(persona: dict, message: str) -> dict:
    return {
        "persona_id": persona["id"],
        "persona_label": persona["label"],
        "biometrics": {
            "height_cm": persona["height_cm"],
            "weight_kg": persona["weight_kg"],
            "birth_year": persona["birth_year"],
            "gender": persona.get("gender"),
        },
        "conversation_log": [],
        "scouting_result": None,
        "eval_result": None,
        "error": message,
    }
