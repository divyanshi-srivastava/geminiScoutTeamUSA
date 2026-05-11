"""
Compliance Agent — "The Guard"
Final quality gate enforcing hackathon rules: NIL, branding, terminology, parity.
"""
import os
from google.adk import Agent
from google.genai import types

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "gemini-3.1-flash-lite"

with open(os.path.join(AGENTS_DIR, "instructions", "compliance.md"), "r") as f:
    _compliance_instruction = f.read()

def make_compliance_agent() -> Agent:
    return Agent(
        name="compliance_agent",
        description="The Guard: Enforces hackathon compliance, terminology, parity, and safety standards.",
        instruction=_compliance_instruction,
        model=MODEL,
        generate_content_config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_budget=2048,
            )
        ),
    )


compliance_agent = make_compliance_agent()
