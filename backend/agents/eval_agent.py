"""
Eval Agent — "The Authenticator"
Called directly by the streamer after the full scouting pipeline completes.
Receives biometrics + conversation history + final result JSON and returns a structured evaluation score.
"""
import os
import json
import datetime
from google import genai
from google.genai import types

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-3.1-pro-preview"

try:
    with open(os.path.join(AGENTS_DIR, "instructions", "eval.md"), "r") as f:
        EVAL_INSTRUCTION = f.read()
except FileNotFoundError:
    EVAL_INSTRUCTION = "Evaluate this scouting report and return a JSON score object."

_client = genai.Client()


async def call_eval(
    height_cm: float | None,
    weight_kg: float | None,
    birth_year: int | None,
    conversation_history: list,
    final_result_json: str,
    target_game_year: int | None = None,
    gender: str | None = None,
) -> dict | None:
    """
    Calls the eval LLM with the full pipeline context.
    Returns parsed evaluation dict or None on failure.
    """
    current_age = (datetime.datetime.now().year - birth_year) if birth_year else None
    age = current_age or "unknown"

    def _life_stage(a: int) -> str:
        if a < 20:   return "Rising Star"
        if a <= 32:  return "Elite Peak"
        if a <= 45:  return "Veteran"
        return "Legacy"

    time_travel_header = ""
    if target_game_year and birth_year:
        age_at_game = target_game_year - birth_year
        age = age_at_game
        life_stage = _life_stage(age_at_game)
        time_travel_header = (
            f"[SYSTEM: TIME_TRAVEL | Destination: The {target_game_year} Games "
            f"| User age at destination: {age_at_game} | Life stage: {life_stage}]\n"
            f"[SYSTEM: AGE_OVERRIDE | {age_at_game} (at The {target_game_year} Games)]\n"
        )

    history_text = ""
    for turn in conversation_history:
        role = turn.role if hasattr(turn, "role") else turn.get("role", "unknown")
        content = turn.content if hasattr(turn, "content") else turn.get("content", "")
        history_text += f"  {role.upper()}: {content}\n"

    prompt = (
        time_travel_header
        + f"BIOMETRIC PROFILE\n"
        f"Height: {height_cm}cm | Weight: {weight_kg}kg | Age at evaluation: {age}"
        + (f" | Gender: {gender}" if gender else "")
        + f"\n\n"
        f"CONVERSATION HISTORY\n{history_text or '(no history provided)'}\n\n"
        f"FINAL PIPELINE RESULT (compliance-approved JSON)\n{final_result_json}\n\n"
        "Now evaluate this scouting report and return your JSON score."
    )

    try:
        response = await _client.aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=EVAL_INSTRUCTION,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True,
                    thinking_budget=8192,
                ),
                max_output_tokens=4096,
            ),
        )
        raw = response.text.strip() if response.text else ""
        # Strip markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        # Fallback: find the outermost JSON object in case the model wraps it in prose
        brace_start = raw.find("{")
        brace_end = raw.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            raw = raw[brace_start:brace_end + 1]
        return json.loads(raw)
    except Exception as e:
        import logging
        logging.getLogger("scout-eval").error(f"Eval failed: {e}", exc_info=True)
        return None
