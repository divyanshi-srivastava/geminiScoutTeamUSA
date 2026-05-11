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
from api.context import active_agent  # noqa: E402

# ── Logging ──

# ANSI color codes
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_COLORS = {
    # level colors
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[37m",   # white
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
    # agent colors (injected via AgentContextFilter)
    "supervisor_agent":  "\033[95m",  # bright magenta
    "scout_agent":       "\033[96m",  # bright cyan
    "narrator_agent":    "\033[93m",  # bright yellow
    "compliance_agent":  "\033[91m",  # bright red
    "eval_agent":        "\033[92m",  # bright green
    "logger_agent":      "\033[94m",  # bright blue
    "—":                 "\033[90m",  # dark grey (no agent)
}


class AgentContextFilter(logging.Filter):
    """Injects the currently active agent name into every log record."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.agent = active_agent.get()  # type: ignore[attr-defined]
        return True


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        agent = getattr(record, "agent", "—")
        level = record.levelname
        agent_color = _COLORS.get(agent, "\033[90m")
        level_color  = _COLORS.get(level, "")

        time_str  = self.formatTime(record, self.datefmt)
        level_str = f"{level_color}{level:<7}{_RESET}"
        agent_str = f"{agent_color}{agent:<20}{_RESET}"
        name_str  = f"{_DIM}{record.name}{_RESET}"
        msg_str   = record.getMessage()

        line = f"{_DIM}{time_str}{_RESET}  {level_str}  {agent_str}  {name_str}: {msg_str}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


_agent_filter = AgentContextFilter()
_color_fmt     = ColorFormatter(datefmt="%H:%M:%S")

_root_handler = logging.StreamHandler()
_root_handler.setFormatter(_color_fmt)
_root_handler.addFilter(_agent_filter)

logging.root.handlers = []
logging.root.addHandler(_root_handler)
logging.root.setLevel(logging.INFO)

# Scout streamer gets DEBUG so full thoughts print
logging.getLogger("scout-streamer").setLevel(logging.DEBUG)

# Suppress ADK noise: "Sending out request, model: …" fires for every LLM call
logging.getLogger("google_adk").setLevel(logging.WARNING)
logging.getLogger("google.adk").setLevel(logging.WARNING)

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
    _mode = (
        "TIME_TRAVEL_INTERVIEW" if request.target_game_year and not request.is_ready_to_scout
        else "SCOUTING" if request.is_ready_to_scout
        else "INTERVIEW"
    )
    logger.info(
        "\n%s\n"
        "  ▶▶ INCOMING REQUEST  /scout\n"
        "     mode          → %s\n"
        "     user/session  → %s / %s\n"
        "     biometrics    → h=%scm  w=%skg  born=%s  gender=%s\n"
        "     history       → %d turns\n"
        "     target_year   → %-10s  ready_to_scout → %s\n"
        "     era_context   → %-10s  era_history    → %s\n"
        "%s",
        "═" * 64,
        _mode,
        request.user_id, request.session_id,
        request.height_cm, request.weight_kg, request.birth_year, request.gender or "—",
        len(request.conversation_history),
        request.target_game_year or "none", request.is_ready_to_scout,
        "YES" if request.era_context_summary else "none",
        "YES" if request.era_history else "none",
        "═" * 64,
    )
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
