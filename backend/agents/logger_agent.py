"""
Logger Agent — "The Interpreter"
Called directly by the streamer (not via the Supervisor) after each sub-agent completes.
Receives the agent's thinking tokens + final output and produces a 2-3 sentence plain-English summary.
"""
import os
from google import genai
from google.genai import types

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-3.1-flash-lite"

try:
    with open(os.path.join(AGENTS_DIR, "instructions", "logger.md"), "r") as f:
        LOGGER_INSTRUCTION = f.read()
except FileNotFoundError:
    LOGGER_INSTRUCTION = "Translate this agent's reasoning into 2-3 plain English sentences for a judge watching live."

_client = genai.Client()


async def call_compliance_diff(before: str, after: str) -> str:
    """
    Given the narrator's raw draft and the compliance-approved final,
    returns 1-2 sentences in first person describing exactly what was changed.
    """
    if before.strip() == after.strip():
        return "I reviewed the Narrator's draft and found nothing to change — it passed all checks clean."
    prompt = (
        "You are the compliance_agent.\n\n"
        f"NARRATOR'S ORIGINAL DRAFT:\n{before[:1000]}\n\n"
        f"YOUR COMPLIANCE-APPROVED FINAL VERSION:\n{after[:1000]}\n\n"
        "In 1-2 sentences using 'I', describe ONLY the specific edits you made. "
        "Quote the exact phrase you changed and what you replaced it with. "
        "If multiple changes, list them concisely. "
        "Do NOT summarize content — only describe the edits. No markdown."
    )
    try:
        response = await _client.aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=LOGGER_INSTRUCTION,
                max_output_tokens=256,
            ),
        )
        return response.text.strip() if response.text else ""
    except Exception:
        return ""


async def call_logger(agent_name: str, thoughts: str, output_summary: str, mode: str = "") -> str:
    """
    Directly calls the logger LLM with the agent's thinking chain and output summary.
    Returns 2-3 plain English sentences for the sidebar.
    """
    mode_context = f"Pipeline mode: {mode}\n\n" if mode else ""
    prompt = (
        f"Agent: {agent_name}\n\n"
        f"{mode_context}"
        f"Internal Reasoning (thinking tokens):\n{thoughts[:3000]}\n\n"
        f"Final Output Summary:\n{output_summary[:600]}\n\n"
        f"Write 2-3 sentences in first person as if you ARE the {agent_name}. "
        "Use 'I' — never refer to yourself in third person."
    )
    try:
        response = await _client.aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=LOGGER_INSTRUCTION,
                max_output_tokens=256,
            ),
        )
        return response.text.strip() if response.text else ""
    except Exception:
        return ""
