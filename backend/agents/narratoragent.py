import os
from google.adk import Agent
from google.genai import types

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-3.1-flash-lite"

with open(os.path.join(AGENTS_DIR, "instructions", "narrator.md"), "r") as f:
    _instruction = f.read()

narrator_agent = Agent(
    name="narrator_agent",
    description="The Voice: Conducts the interview and writes the final living legacy story.",
    instruction=_instruction,
    model=MODEL,
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=4096,
        )
    ),
)
