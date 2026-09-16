"""
Thin, validated wrapper around src.database.recipes.search_recipes.

The DB function does the real search but just raises on bad input -
this adds input validation and turns errors into a normal dict
response, since the agent can't handle a raised exception.
"""

from src.database.recipes import search_recipes as _db_search_recipes


def search_recipes(
    user_id: int,
    search_term: str | None = None,
    max_cook_time: int | None = None,
) -> dict:
    """Search a user's recipes by name/description text, optionally
    capped by max_cook_time (minutes). Either filter can be left out."""

    # ---- Input validation ----

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        return _error("user_id must be an integer.")

    if search_term is not None and not isinstance(search_term, str):
        return _error("search_term must be a string or None.")

    if max_cook_time is not None:
        if not isinstance(max_cook_time, int) or isinstance(max_cook_time, bool):
            return _error("max_cook_time must be an integer or None.")

        if max_cook_time < 0:
            return _error("max_cook_time cannot be negative.")

    cleaned_search_term = search_term.strip() if search_term else None

    if cleaned_search_term == "":
        cleaned_search_term = None

    # ---- Query ----

    try:
        recipes = _db_search_recipes(
            user_id=user_id,
            search_term=cleaned_search_term,
            max_cook_time=max_cook_time,
        )
    except Exception as e:
        return _error(f"Database error while searching recipes: {e}")

    return {
        "success": True,
        "error": None,
        "count": len(recipes),
        "recipes": recipes,
    }


def _error(message: str) -> dict:
    """Build a standard error response."""
    return {
        "success": False,
        "error": message,
        "count": None,
        "recipes": None,
    }