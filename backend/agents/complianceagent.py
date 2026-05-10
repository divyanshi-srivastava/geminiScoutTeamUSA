"""
Compliance Agent — "The Guard"
Final quality gate enforcing hackathon rules: NIL, branding, terminology, parity.
"""
import os
from google.adk import Agent

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCOUT_MODEL = "gemini-2.5-pro"

# ── Load instruction markdown ──
with open(os.path.join(AGENTS_DIR, "instructions", "compliance.md"), "r") as f:
    _compliance_instruction = f.read()

compliance_agent = Agent(
    name="compliance_agent",
    description="The Guard: Enforces hackathon compliance, terminology, parity, and safety standards.",
    instruction=_compliance_instruction,
    model=SCOUT_MODEL,
)
