"""
Scout Pipeline — SequentialAgent instances replacing the supervisor.

Mode selection happens in Python (streamer.py). Each pipeline enforces
its agent ordering deterministically with no LLM routing decisions.

  SCOUTING:             scout → narrator → compliance
  INTERVIEW:            narrator → compliance
  TIME_TRAVEL_INTERVIEW: narrator → compliance  (with era headers in system message)
"""
from google.adk.agents import SequentialAgent

from agents.scout_agent import scout_agent
from agents.narrator_agent import make_narrator_agent
from agents.compliance_agent import make_compliance_agent

# Each pipeline gets its own agent instances — ADK enforces one parent per agent.
# All instances share the same name so event_author matching in the streamer is consistent.

scouting_pipeline = SequentialAgent(
    name="scouting_pipeline",
    description="Full scouting run: scout → narrator → compliance.",
    sub_agents=[scout_agent, make_narrator_agent(), make_compliance_agent()],
)

interview_pipeline = SequentialAgent(
    name="interview_pipeline",
    description="Interview turn: narrator asks next question → compliance reviews.",
    sub_agents=[make_narrator_agent(), make_compliance_agent()],
)

time_travel_pipeline = SequentialAgent(
    name="time_travel_pipeline",
    description="Time travel interview: narrator asks one era-bridging question → compliance reviews.",
    sub_agents=[make_narrator_agent(), make_compliance_agent()],
)

print("SUCCESS: 3 pipelines loaded (scouting, interview, time_travel). Supervisor removed.")
