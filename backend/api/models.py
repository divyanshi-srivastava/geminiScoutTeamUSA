"""
Pydantic schemas for the Gemini Scout API.
Supports both stateful Interview mode and one-shot Scouting mode.
"""
from pydantic import BaseModel
from typing import Optional, List


class ConversationTurn(BaseModel):
    """A single Q&A turn in the narrator-led interview."""
    role: str  # "narrator" or "user"
    content: str


class StoryRequest(BaseModel):
    """
    Incoming request from the Angular frontend.
    Supports two modes:
      - INTERVIEW (is_ready_to_scout=False): Narrator generates the next question.
      - SCOUTING  (is_ready_to_scout=True):  Full 5-agent pipeline executes.
    """
    story: str = ""
    user_id: str = "default_user"
    session_id: str = "default_session"
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    birth_year: Optional[int] = None

    # ── Stateful Conversation Fields ──
    conversation_history: List[ConversationTurn] = []
    is_ready_to_scout: bool = False

    # ── Time-Travel Field ──
    target_game_year: Optional[int] = None


class AgentEventTrace(BaseModel):
    """A single audit trace event emitted during orchestration."""
    agent: str
    event: str
    timestamp: str
    detail: Optional[str] = None


class ScoutResponse(BaseModel):
    """Final scouting response (used for non-streaming fallback)."""
    response: str
    trace: List[AgentEventTrace] = []
