import os
from google.adk import Agent
from google.adk.tools import google_search
from google.genai import types

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-3.1-pro-preview"

with open(os.path.join(AGENTS_DIR, "instructions", "scout.md"), "r") as f:
    _instruction = f.read()

manifest_path = os.path.join(AGENTS_DIR, "data", "pathway_manifest.json")
with open(manifest_path, "r") as f:
    _manifest = f.read()
_instruction += f"\n\nPATHWAY MANIFEST:\n{_manifest}"

scout_agent = Agent(
    name="scout_agent",
    description="The Analyst: Maps user biometrics to pathway archetypes.",
    instruction=_instruction,
    model=MODEL,
    tools=[google_search],
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=8192,
        ),
    ),
)
