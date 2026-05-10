import os
import sys
import asyncio

# Ensure the backend root is on the path so `agents` can be imported
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("GOOGLE_GENAI_USE_ENTERPRISE", "true")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "geminiscoutteamusa")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

_creds_path = os.path.join(BACKEND_DIR, "scout-credentials.json")
if os.path.isfile(_creds_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _creds_path

from google.adk import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402
from agents.supervisoragent import supervisor_agent  # noqa: E402


async def test_scout():
    story = (
        "I work in construction. I spend 8 hours a day carrying heavy bags of "
        "cement, wrestling with massive steel beams, and throwing equipment up "
        "to higher levels. My core and arms are incredibly dense from this daily grind."
    )
    print(f"Testing with story: {story}\n")

    runner = Runner(
        app_name="scout_app",
        agent=supervisor_agent,
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=story)],
    )

    print("Running agent...")
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=message,
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(part.text)


if __name__ == "__main__":
    asyncio.run(test_scout())
