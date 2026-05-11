"""
Answer Agent — picks the most authentic answer to a narrator question for a given persona.
Uses gemini-3.1-flash-lite for speed: this is called once per interview turn per persona.
"""
import logging
from google import genai
from google.genai import types

MODEL = "gemini-3.1-flash-lite"

_client: genai.Client | None = None
logger = logging.getLogger("benchmark.answer_agent")


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client()
    return _client

_SYSTEM = """You are a benchmark user simulator for a sports scouting app.

Given a persona description and a narrator question, you produce the most authentic answer that person would give.

Rules:
- If options are provided, respond with EXACTLY one option verbatim — copy it character-for-character
- If no options, write one natural sentence (max 25 words) in the persona's voice
- Never add explanation, quotes, or preamble — just the answer itself
- Pick the option that best fits the persona's background and preferences
- If multiple options seem equal, prefer the one that reveals more about the persona's sport history"""


async def pick_answer(persona: dict, question: dict, conversation_so_far: list) -> str:
    """
    Returns the answer this persona would give to the narrator's question.
    For multi-choice questions, returns one option text verbatim.
    For free-text questions, returns a short natural sentence.
    """
    options = question.get("options", [])

    # Last 3 exchanges for context (avoid over-long prompts)
    recent = conversation_so_far[-6:]
    history_text = "\n".join(
        f"  {t['role'].upper()}: {t['content'][:200]}" for t in recent
    )

    options_block = ""
    if options:
        options_block = "\nOptions (pick ONE verbatim):\n" + "\n".join(
            f"  [{i+1}] {opt}" for i, opt in enumerate(options)
        )

    prompt = (
        f"PERSONA\n"
        f"  Label: {persona['label']}\n"
        f"  Description: {persona['description']}\n"
        f"  Biometrics: {persona['height_cm']}cm, {persona['weight_kg']}kg, "
        f"born {persona['birth_year']}, gender: {persona.get('gender', 'not specified')}\n\n"
        f"RECENT CONVERSATION\n{history_text or '  (none yet)'}\n\n"
        f"NARRATOR ASKS: {question['question']}"
        f"{options_block}\n\n"
        f"Answer as this persona:"
    )

    try:
        response = await _get_client().aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM,
                max_output_tokens=150,
                temperature=0.3,
            ),
        )
        answer = response.text.strip() if response.text else ""

        # If options were given, validate the answer matches one of them (fuzzy)
        if options and answer:
            for opt in options:
                if opt.strip().lower() in answer.lower() or answer.lower() in opt.strip().lower():
                    return opt  # return the canonical option text
            # If no match, return first option as safe fallback
            logger.warning("Answer '%s' didn't match any option — using first option", answer[:60])
            return options[0]

        return answer or (options[0] if options else "I'm not sure.")

    except Exception as e:
        logger.error("pick_answer failed: %s", e)
        return options[0] if options else "I'm open to seeing what you suggest."
