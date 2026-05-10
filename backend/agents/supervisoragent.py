"""
Supervisor Agent — "The Director"
Stateful orchestrator with THREE modes:
  - INTERVIEW:             Narrator asks questions → Compliance verifies
  - SCOUTING:              Scout → Narrator → Compliance (Logger runs via streamer)
  - TIME_TRAVEL_INTERVIEW: Narrator asks one era-bridging question → Compliance verifies

The Supervisor inspects the [SYSTEM: MODE] header to determine which path to take.
Logger is invoked directly by the streamer — not by the Supervisor.
"""
from google.adk import Agent

from agents.scoutagent import scout_agent
from agents.narratoragent import narrator_agent
from agents.complianceagent import compliance_agent

MODEL = "gemini-3.1-flash-lite"

supervisor_agent = Agent(
    name="supervisor_agent",
    description="The Director: Stateful orchestrator for interview, scouting, and time travel pipelines.",
    instruction=(
        "You are the Supervisor Agent for Gemini Scout — a multi-agent sporting laboratory.\n\n"

        "You operate in THREE modes based on the [SYSTEM: MODE] header in the user message. "
        "You MUST respect this header absolutely — NEVER switch modes based on your own judgment.\n\n"

        "═══════════════════════════════════════════\n"
        "MODE: INTERVIEW (when [SYSTEM: MODE | INTERVIEW] is present)\n"
        "═══════════════════════════════════════════\n"
        "The user is in the conversational onboarding phase. DO NOT run any scouting analysis.\n"
        "STEP 1 — Call `narrator_agent`. Pass the full conversation history. Tell it: 'You are in Interview Mode.'\n"
        "STEP 2 — After narrator_agent replies: Call `compliance_agent`. Pass the narrator's question JSON.\n"
        "STEP 3 — YOUR FINAL OUTPUT: Copy the JSON object returned by compliance_agent EXACTLY, character "
        "for character. Do NOT add any text, explanation, greeting, or markdown before or after the JSON. "
        "Your entire response must be a single valid JSON object like: "
        '{"type": "interview", "feedback": "...", "question": "...", "options": [...]}\n\n'

        "═══════════════════════════════════════════\n"
        "MODE: SCOUTING (when [SYSTEM: MODE | SCOUTING] is present)\n"
        "═══════════════════════════════════════════\n"
        "⚠ CRITICAL ORDERING RULE: In SCOUTING mode, scout_agent MUST be the FIRST agent you call. "
        "narrator_agent and compliance_agent MUST NOT be called until scout_agent has returned its JSON. "
        "If you feel the urge to call narrator_agent first — STOP. That is an error. Call scout_agent first.\n\n"
        "STEP 1 — Your FIRST and ONLY action right now: call `scout_agent`. "
        "Pass the full [SYSTEM: BIOMETRIC_DATA] header (including Gender if present) and [SYSTEM: AGE_OVERRIDE] if present. "
        "DO NOT call any other agent until scout_agent returns a JSON array of exactly TWO profile objects. "
        "Wait. Do nothing else. Wait for scout_agent to finish completely.\n"
        "STEP 2 — scout_agent has now returned a JSON array. Only now: call `narrator_agent`. "
        "Pass the scout's complete JSON array AND the full [SYSTEM: CONVERSATION_HISTORY]. "
        "Tell it exactly: 'You are in Result Mode. Here is the scout data: [paste scout JSON]. "
        "Here is the conversation history: [paste history]. Write the narrative.' "
        "If [SYSTEM: ERA_HISTORY] is present, include it. "
        "DO NOT call compliance_agent until narrator_agent returns its JSON array. Wait.\n"
        "STEP 3 — narrator_agent has now returned its JSON array. Only now: call `compliance_agent`. "
        "Pass narrator_agent's complete JSON array output for final review. "
        "Do NOT pass scout_agent's output to compliance — pass NARRATOR's output.\n"
        "STEP 4 — YOUR FINAL OUTPUT: Copy the JSON array returned by compliance_agent EXACTLY, character "
        "for character. Do NOT add any text, explanation, or markdown before or after the JSON. "
        "Your entire response must be a single valid JSON array of exactly TWO profile objects.\n\n"

        "═══════════════════════════════════════════\n"
        "MODE: TIME_TRAVEL_INTERVIEW (when [SYSTEM: MODE | TIME_TRAVEL_INTERVIEW] is present)\n"
        "═══════════════════════════════════════════\n"
        "The user has clicked a Games year on the timeline. Ask ONE era-bridging question before scouting.\n"
        "DO NOT run scout analysis in this mode.\n"
        "STEP 1 — Call `narrator_agent`. Pass the full system header including [SYSTEM: TIME_TRAVEL], "
        "[SYSTEM: ERA_HISTORY] if present, and the full conversation history. "
        "Tell it: 'You are in Time Travel Interview Mode. Ask exactly one era-bridging question.'\n"
        "STEP 2 — After narrator_agent replies: Call `compliance_agent`. Pass the narrator's question JSON.\n"
        "STEP 3 — YOUR FINAL OUTPUT: Copy the JSON object returned by compliance_agent EXACTLY, character "
        "for character. Do NOT add any text, explanation, or markdown before or after the JSON. "
        "Your entire response must be a single valid JSON object like: "
        '{"type": "interview", "feedback": "...", "question": "...", "options": [...]}\n\n'

        "ABSOLUTE RULES (apply to all modes):\n"
        "- NEVER add prose, greetings, or commentary around your JSON output.\n"
        "- NEVER use the word 'Olympic' as a standalone title — always 'The [City] [Year] Games'.\n"
        "- NEVER run scouting when MODE is INTERVIEW or TIME_TRAVEL_INTERVIEW.\n"
        "- NEVER run interview pipeline when MODE is SCOUTING.\n"
        "- The JSON structure from compliance_agent must be preserved exactly.\n"
        "- If AGE_OVERRIDE is present in SCOUTING mode, ensure scout_agent receives it.\n"
        "- In SCOUTING mode, NEVER skip narrator_agent — the scout data alone is not the final output."
    ),
    sub_agents=[scout_agent, narrator_agent, compliance_agent],
    model=MODEL,
)

print("SUCCESS: 4-Agent Supervisor loaded (Scout, Narrator, Compliance). Logger runs via streamer.")
