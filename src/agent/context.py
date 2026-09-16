"""
Keeps track of which user the current request belongs to.

Agent tools are just plain functions, Gemini calls them directly, so
they have no built-in idea of who's asking. Can't use a normal global
either, since Streamlit can run several people's sessions in the same
process at once, and a global would mix them up. threading.local() gives
each session its own value instead.
"""

import threading

from src.config import DEFAULT_USER_ID

_context = threading.local()


def set_current_user_id(user_id: int) -> None:
    """Call this at the top of every page (every rerun) before touching
    the DB or agent tools - Streamlit reuses threads, so it won't
    persist on its own."""
    _context.user_id = user_id


def get_current_user_id() -> int:
    """Falls back to DEFAULT_USER_ID if nothing was set yet."""
    return getattr(_context, "user_id", DEFAULT_USER_ID)
