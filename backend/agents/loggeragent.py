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


async def call_logger(agent_name: str, thoughts: str, output_summary: str) -> str:
    """
    Directly calls the logger LLM with the agent's thinking chain and output summary.
    Returns 2-3 plain English sentences for the sidebar.
    """
    prompt = (
        f"Agent: {agent_name}\n\n"
        f"Internal Reasoning (thinking tokens):\n{thoughts[:3000]}\n\n"
        f"Final Output Summary:\n{output_summary[:600]}\n\n"
        "Based on the above, write your 2-3 sentence interpretation."
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
