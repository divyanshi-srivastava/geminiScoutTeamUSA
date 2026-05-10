import os
from google.adk import Agent

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCOUT_MODEL = "gemini-2.5-pro"

try:
    with open(os.path.join(AGENTS_DIR, "instructions", "logger.md"), "r") as f:
        _instruction = f.read()
except FileNotFoundError:
    _instruction = "You are the Logger Agent. You generate short, narrative traces for the UI."

logger_agent = Agent(
    name="logger_agent",
    description="The Trace: Real-time narrator of the orchestration pipeline.",
    instruction=_instruction,
    model=SCOUT_MODEL,
)
