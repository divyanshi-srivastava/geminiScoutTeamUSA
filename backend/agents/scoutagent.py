import os
from google.adk import Agent

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCOUT_MODEL = "gemini-2.5-pro"

with open(os.path.join(AGENTS_DIR, "instructions", "scout.md"), "r") as f:
    _instruction = f.read()

# Append pathway manifest to instructions so scout has context
manifest_path = os.path.join(os.path.dirname(os.path.dirname(AGENTS_DIR)), "frontend", "src", "assets", "data", "pathway_manifest.json")
with open(manifest_path, "r") as f:
    _manifest = f.read()
_instruction += f"\n\nPATHWAY MANIFEST:\n{_manifest}"

scout_agent = Agent(
    name="scout_agent",
    description="The Analyst: Maps user biometrics to pathway archetypes.",
    instruction=_instruction,
    model=SCOUT_MODEL,
)
