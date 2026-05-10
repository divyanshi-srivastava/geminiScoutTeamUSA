import os
from google.adk import Agent
from google.adk.tools import google_search
from google.genai import types

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-3.1-pro-preview"

_manifest_version = os.environ.get("MANIFEST_VERSION", "v2")
_instruction_file = "scout_v2.md" if _manifest_version == "v2" else "scout.md"
_manifest_file = "pathway_manifest_v2.json" if _manifest_version == "v2" else "pathway_manifest.json"

with open(os.path.join(AGENTS_DIR, "instructions", _instruction_file), "r") as f:
    _instruction = f.read()

manifest_path = os.path.join(AGENTS_DIR, "data", _manifest_file)
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

print(f"Scout Agent loaded: manifest={_manifest_file}, instruction={_instruction_file}")
