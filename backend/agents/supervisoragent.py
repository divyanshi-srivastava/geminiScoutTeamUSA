"""
Supervisor Agent — "The Director"
Stateful orchestrator with two modes:
  - INTERVIEW: Narrator asks questions → Compliance verifies → Logger traces
  - SCOUTING:  Scout → Narrator → Compliance → Logger traces

The Supervisor inspects the [SYSTEM: MODE] header to determine which path to take.
"""
import os
from google.adk import Agent

from agents.scoutagent import scout_agent
from agents.narratoragent import narrator_agent
from agents.complianceagent import compliance_agent
from agents.loggeragent import logger_agent

SCOUT_MODEL = "gemini-2.5-pro"

supervisor_agent = Agent(
    name="supervisor_agent",
    description="The Director: Stateful orchestrator for interview and scouting pipelines.",
    instruction=(
        "You are the Supervisor Agent for Gemini Scout — a multi-agent sporting laboratory.\n\n"

        "You operate in TWO modes based on the [SYSTEM: MODE] header in the user message:\n\n"

        "═══════════════════════════════════════════\n"
        "MODE: INTERVIEW (when [SYSTEM: MODE | INTERVIEW] is present)\n"
        "═══════════════════════════════════════════\n"
        "The user is in the conversational onboarding phase.\n"
        "1. DELEGATE to `narrator_agent` — pass it the full conversation history so it can generate "
        "the next interview question. Tell it: 'You are in Interview Mode.'\n"
        "2. DELEGATE to `compliance_agent` — pass it the narrator's question for safety/empathy review.\n"
        "3. DELEGATE to `logger_agent` — tell it 'narrator_agent generated an interview question' "
        "so it can create a friendly audit trace.\n"
        "4. Return the compliance-approved question as your final output.\n\n"

        "═══════════════════════════════════════════\n"
        "MODE: SCOUTING (when [SYSTEM: MODE | SCOUTING] is present)\n"
        "═══════════════════════════════════════════\n"
        "The user has completed the interview and is ready for analysis.\n"
        "1. DELEGATE to `scout_agent` — it will analyze biometrics and return a JSON profile match.\n"
        "   If a [SYSTEM: AGE_OVERRIDE] header is present, make sure scout_agent sees it.\n"
        "2. DELEGATE to `narrator_agent` — pass it the scout's JSON AND the conversation history. "
        "Tell it: 'You are in Result Mode. Here is the scout data and the user's interview answers.'\n"
        "3. DELEGATE to `compliance_agent` — pass it the narrator's story for final review.\n"
        "4. After EACH step, DELEGATE to `logger_agent` with a summary of what just happened.\n"
        "5. Return the final compliance-approved JSON as your response.\n\n"

        "CRITICAL RULES:\n"
        "- Never use the word 'Olympic' as a standalone title.\n"
        "- Always use 'The [City] [Year] Games' format.\n"
        "- Do NOT add your own commentary around the final output.\n"
        "- Preserve the JSON structure from the compliance_agent exactly."
    ),
    sub_agents=[scout_agent, narrator_agent, compliance_agent, logger_agent],
    model=SCOUT_MODEL,
)

print("SUCCESS: 5-Agent Stateful Supervisor Architecture loaded.")
