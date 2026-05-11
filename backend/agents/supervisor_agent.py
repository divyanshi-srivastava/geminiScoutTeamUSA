"""
Supervisor Agent — "The Director"
Stateful orchestrator with THREE modes:
  - INTERVIEW:             Narrator asks questions → Compliance verifies
  - SCOUTING:              Scout → Narrator → Compliance (Logger runs via streamer)
  - TIME_TRAVEL_INTERVIEW: Narrator asks one era-bridging question → Compliance verifies

The Supervisor inspects the [SYSTEM: MODE] header to determine which path to take.
Logger is invoked directly by the streamer — not by the Supervisor.
"""
import os
from google.adk import Agent

from agents.scout_agent import scout_agent
from agents.narrator_agent import narrator_agent
from agents.compliance_agent import compliance_agent
from google.genai import types


AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-3.1-flash-lite"

with open(os.path.join(AGENTS_DIR, "instructions", "supervisor.md"), "r") as f:
    _instruction = f.read()

supervisor_agent = Agent(
    name="supervisor_agent",
    description="The Director: Stateful orchestrator for interview, scouting, and time travel pipelines.",
    instruction=_instruction,
    sub_agents=[scout_agent, narrator_agent, compliance_agent],
    model=MODEL,
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=8192,
        ),
    ),
)

print("SUCCESS: 4-Agent Supervisor loaded (Scout, Narrator, Compliance). Logger runs via streamer.")
