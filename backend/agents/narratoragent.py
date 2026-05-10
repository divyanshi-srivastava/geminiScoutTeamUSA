import os
from google.adk import Agent

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCOUT_MODEL = "gemini-2.5-pro"

with open(os.path.join(AGENTS_DIR, "instructions", "narrator.md"), "r") as f:
    _instruction = f.read()

narrator_agent = Agent(
    name="narrator_agent",
    description="The Voice: Conducts the interview and writes the final living legacy story.",
    instruction=_instruction,
    model=SCOUT_MODEL,
)
