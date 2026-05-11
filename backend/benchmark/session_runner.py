"""
Session Runner — drives one persona through the full interview → scout → time travel flow
by hitting the live backend HTTP API. Parses SSE events from the /scout endpoint.

Flow per persona:
  Phase 1: Full interview (max_questions turns via INTERVIEW mode)
  Phase 2: Initial scouting + eval (SCOUTING mode, no era context)
  Phase 3: For each hop in time_travel_hops:
    - Era interview loop (TIME_TRAVEL_INTERVIEW mode until era_ready_to_scout: true)
    - Era scouting + eval (SCOUTING mode with target_game_year + era_context_summary)
    - Accumulate era_history for subsequent hops
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
        "interview":           <parsed question dict> | None,
        "era_context_summary": <dict> | None,   # present when era interview completes
        "result":              <scouting list> | None,
        "eval":                <eval dict> | None,
        "error":               <str> | None,
      }
    """
    collected = {
        "interview": None,
        "era_context_summary": None,
        "result": None,
        "eval": None,
        "error": None,
    }

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
                    q = json.loads(event["response"])
                except Exception:
                    q = None
                if not isinstance(q, dict):
                    logger.warning(
                        "  interview event response is %s, not dict — wrapping as fallback",
                        type(q).__name__,
                    )
                    q = {
                        "question": event.get("response", "") if not isinstance(q, list) else "",
                        "options": q if isinstance(q, list) else [],
                        "ready_to_proceed": False,
                    }
                collected["interview"] = q
                # era_context_summary is embedded in the interview payload when the
                # narrator signals era_ready_to_scout: true
                if q.get("era_context_summary"):
                    collected["era_context_summary"] = q["era_context_summary"]
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
    """Appends a narrator turn with options inline so eval can see question quality."""
    options = question.get("options", [])
    option_strs = []
    for opt in options:
        if isinstance(opt, str):
            option_strs.append(opt)
        elif isinstance(opt, dict):
            # Narrator may return {label, value} or {text, value} objects
            option_strs.append(
                opt.get("label") or opt.get("text") or opt.get("value") or str(opt)
            )
    options_text = (
        "\nOptions: [" + " | ".join(option_strs) + "]"
        if option_strs else ""
    )
    history.append({
        "role": "narrator",
        "content": question.get("question", "") + options_text,
    })


async def _run_era_interview(
    client: httpx.AsyncClient,
    scout_url: str,
    persona: dict,
    session_id: str,
    user_id: str,
    main_history: list,
    hop_year: int,
    era_history: dict,
    era_log: list,
) -> dict | None:
    """
    Drives a full TIME_TRAVEL_INTERVIEW loop for one hop year.
    Accumulates turns in era_log. Returns era_context_summary dict or None on failure.

    Each request sends the full accumulated conversation (main interview + era turns so far)
    so the narrator remembers what it already asked.
    """
    # Working copy of conversation history — grows with each era turn
    full_history = list(main_history)

    def _era_body(story: str = "") -> dict:
        return {
            "story": story,
            "session_id": session_id,
            "user_id": user_id,
            "height_cm": persona["height_cm"],
            "weight_kg": persona["weight_kg"],
            "birth_year": persona["birth_year"],
            "gender": persona.get("gender"),
            "conversation_history": [dict(t) for t in full_history],
            "is_ready_to_scout": False,
            "target_game_year": hop_year,
            "era_history": era_history if era_history else None,
        }

    # Trigger the era interview
    events = await _stream_request(client, scout_url, _era_body(""))
    era_q = events.get("interview")

    if not era_q:
        logger.warning(
            "  ERA INTERVIEW: no initial question received for year %d  persona=%s",
            hop_year, persona["id"],
        )
        return None

    _append_narrator_turn(era_log, era_q)
    _append_narrator_turn(full_history, era_q)

    for attempt in range(5):  # safety cap — narrator rarely needs more than 2 turns
        if era_q.get("era_ready_to_scout"):
            era_ctx = events.get("era_context_summary") or era_q.get("era_context_summary")
            logger.info(
                "  ERA INTERVIEW COMPLETE  year=%d  signals=%s  persona=%s",
                hop_year,
                (era_ctx.get("signals") or []) if era_ctx else "none",
                persona["id"],
            )
            return era_ctx

        answer = await pick_answer(persona, era_q, full_history)
        era_log.append({"role": "user", "content": answer})
        full_history.append({"role": "user", "content": answer})
        logger.info("  ERA Q%-2d  year=%d  a=%s", attempt + 1, hop_year, answer[:60])

        events = await _stream_request(client, scout_url, _era_body(answer))
        era_q = events.get("interview")

        if not era_q:
            # Narrator may have returned era_context_summary without a follow-up question
            era_ctx = events.get("era_context_summary")
            if era_ctx:
                logger.info("  ERA INTERVIEW COMPLETE (no follow-up Q)  year=%d", hop_year)
            else:
                logger.warning("  ERA INTERVIEW: no follow-up at attempt %d  year=%d", attempt + 1, hop_year)
            return era_ctx

        _append_narrator_turn(era_log, era_q)
        _append_narrator_turn(full_history, era_q)

    logger.warning("  ERA INTERVIEW: safety cap reached  year=%d  persona=%s", hop_year, persona["id"])
    return None


async def run_persona(persona: dict, backend_url: str) -> dict:
    """
    Drives one persona through the full benchmark flow. Returns a result dict with:
      persona_id, persona_label, biometrics,
      conversation_log      — main interview turns
      scouting_result       — initial (non-era) scout result
      eval_result           — initial scout eval
      backend_error         — initial scout error or None
      time_travel_results   — list of per-hop dicts (one per time_travel_hops entry)
    """
    scout_url = f"{backend_url.rstrip('/')}/scout"
    session_id = str(uuid.uuid4())
    user_id = f"benchmark_{persona['id']}"

    conversation_history: list = []
    question_count = 0
    max_questions = persona.get("max_questions", 4)
    time_travel_hops: list = persona.get("time_travel_hops", [])

    def _body(
        story: str,
        *,
        is_scout: bool = False,
        target_game_year: int | None = None,
        era_context_summary: dict | None = None,
        era_history: dict | None = None,
    ) -> dict:
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
        if target_game_year is not None:
            b["target_game_year"] = target_game_year
        if era_context_summary is not None:
            b["era_context_summary"] = era_context_summary
        if era_history:
            b["era_history"] = era_history
        return b

    logger.info(
        "▶ START  persona=%-40s  hops=%s",
        persona["id"],
        time_travel_hops if time_travel_hops else "—",
    )

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

            q_text = question.get("question", "")
            logger.info(
                "  Q%-2d  q=%-55s  a=%s",
                question_count,
                (q_text[:55] + "…") if len(q_text) > 55 else q_text,
                answer[:50],
            )

            if question.get("ready_to_proceed") and question_count >= 2:
                logger.info("  ready_to_proceed at Q%d — moving to scouting", question_count)
                break

            if question_count >= max_questions:
                break

            events = await _stream_request(client, scout_url, _body(answer))
            question = events.get("interview")
            if not question:
                logger.warning("  No follow-up at Q%d — moving to scouting", question_count)
                break
            _append_narrator_turn(conversation_history, question)

        # ── Phase 3: Initial scouting ──
        logger.info(
            "  ◆ Initial Scouting  history=%d turns  persona=%s",
            len(conversation_history), persona["id"],
        )
        scout_events = await _stream_request(client, scout_url, _body("", is_scout=True))

        scouting_result = scout_events.get("result")
        eval_result = scout_events.get("eval")
        backend_error = scout_events.get("error")

        _log_scout_outcome(persona["id"], scouting_result, eval_result, backend_error, label="Initial")

        # ── Phase 4: Time travel hops ──
        time_travel_results: list = []
        era_history: dict = {}

        for hop_year in time_travel_hops:
            logger.info(
                "  ⏳ Time Travel hop  year=%d  persona=%s",
                hop_year, persona["id"],
            )
            era_interview_log: list = []

            era_context_summary = await _run_era_interview(
                client=client,
                scout_url=scout_url,
                persona=persona,
                session_id=session_id,
                user_id=user_id,
                main_history=conversation_history,
                hop_year=hop_year,
                era_history=era_history,
                era_log=era_interview_log,
            )

            # Scout for this era
            logger.info(
                "  ◆ Era Scouting  year=%d  era_ctx=%s  persona=%s",
                hop_year,
                "yes" if era_context_summary else "no (scouting without era context)",
                persona["id"],
            )
            era_scout_events = await _stream_request(
                client, scout_url,
                _body(
                    "",
                    is_scout=True,
                    target_game_year=hop_year,
                    era_context_summary=era_context_summary,
                    era_history=era_history if era_history else None,
                ),
            )

            hop_result = era_scout_events.get("result")
            hop_eval = era_scout_events.get("eval")
            hop_error = era_scout_events.get("error")

            _log_scout_outcome(persona["id"], hop_result, hop_eval, hop_error, label=f"Era {hop_year}")

            time_travel_results.append({
                "target_game_year": hop_year,
                "era_interview_log": era_interview_log,
                "era_context_summary": era_context_summary,
                "scouting_result": hop_result,
                "eval_result": hop_eval,
                "backend_error": hop_error,
            })

            # Accumulate era_history so subsequent hops know what earlier hops revealed
            if era_context_summary:
                life = era_context_summary.get("life_context", "")
                physical = era_context_summary.get("physical_context", "")
                era_history[str(hop_year)] = f"{life} | {physical}".strip(" |")

    overall = eval_result.get("overall", "—") if eval_result else "N/A"
    tt_evals = sum(1 for h in time_travel_results if h.get("eval_result"))
    logger.info(
        "✓ DONE  persona=%-40s  overall=%s  tt_hops=%d  tt_evals=%d",
        persona["id"], overall, len(time_travel_results), tt_evals,
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
        "time_travel_results": time_travel_results,
    }


def _log_scout_outcome(pid: str, result, eval_result, error, label: str = "") -> None:
    prefix = f"  [{label}]" if label else " "
    if error:
        logger.error("%s SCOUTING FAILED  persona=%s  error=%s", prefix, pid, error)
    elif result is None:
        logger.warning("%s SCOUTING RETURNED NOTHING  persona=%s", prefix, pid)
    elif eval_result is None:
        logger.warning("%s EVAL MISSING  persona=%s  (scouting OK but no eval event)", prefix, pid)


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
        "backend_error": message,
        "time_travel_results": [],
    }
