from contextvars import ContextVar

# Tracks the currently active agent across async boundaries.
# Set by the streamer whenever a new agent produces an event.
# Read by the log filter in main.py to label every log line with agent context.
active_agent: ContextVar[str] = ContextVar("active_agent", default="—")
