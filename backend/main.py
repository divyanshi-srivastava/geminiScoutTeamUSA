"""
Gemini Scout — Enterprise Backend Entry Point
==============================================
Minimal FastAPI routing layer. All business logic lives in:
  - agents/     → 5-agent hub-and-spoke architecture
  - api/        → Pydantic models & SSE streamer
"""
import os
import logging

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# ── Vertex AI / ADK authentication ──
# On Cloud Run these are set automatically via the service account.
# Locally, set them in your shell or .env before starting.
os.environ.setdefault("GOOGLE_GENAI_USE_ENTERPRISE", "true")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "geminiscoutteamusa")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")

# Local-only: point to the service-account key file.
_creds_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "scout-credentials.json"
)
if os.path.isfile(_creds_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _creds_path
    print(f"DEBUG: Using credentials from {_creds_path}")

# ── Imports (MUST come after env vars are set) ──
from api.models import StoryRequest  # noqa: E402
from api.streamer import event_generator  # noqa: E402

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scout-backend")

# ── FastAPI app ──
app = FastAPI(title="Gemini Scout Enterprise Backend")

# CORS: allow the Angular frontend (local dev + deployed domain)
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:4200,https://geminiscoutteamusa.web.app,https://geminiscoutteamusa.firebaseapp.com",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ──


@app.get("/health")
async def health():
    """Health check endpoint (required by Cloud Run)."""
    return {"status": "ok"}


@app.post("/scout")
async def analyze_story(request: StoryRequest):
    """
    Stateful 5-Agent Pipeline with real-time SSE streaming.
    Mode is determined by request.is_ready_to_scout:
      - INTERVIEW: Narrator generates next question (with compliance review)
      - SCOUTING:  Full pipeline Scout → Narrator → Compliance (Logger as sidecar)
    Errors during streaming are handled inside event_generator and emitted as
    SSE error events — a try/except here cannot catch them.
    """
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
