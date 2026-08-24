"""
Per-request "current user" context for agent tools.

Agent tools are registered as plain Python functions (the Gemini
SDK calls them directly via automatic function calling), so they
have no natural way to know which user's request they're serving.

A single module-level variable would NOT be safe here: Streamlit
can run multiple people's sessions concurrently in the same
Python process (each session's script reruns in its own thread),
so a plain global could leak user A's id into user B's tool calls
if their requests overlap in time.

threading.local() gives each thread — and therefore each
concurrent Streamlit session — its own isolated value, which is
what we actually need.
"""

import threading

from src.config import DEFAULT_USER_ID

_context = threading.local()


def set_current_user_id(user_id: int) -> None:
    """
    Set the current user for this thread. Call this at the top of
    every page, on every rerun, before any DB or agent-tool code
    runs — Streamlit reuses threads across reruns, so this must be
    set fresh each time rather than assumed to persist correctly.
    """
    _context.user_id = user_id


def get_current_user_id() -> int:
    """
    Get the current user for this thread. Falls back to
    DEFAULT_USER_ID if never set (e.g. running a script or test
    outside the Streamlit app, or before auth is wired up on a
    given page).
    """
    return getattr(_context, "user_id", DEFAULT_USER_ID)