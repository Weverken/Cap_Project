"""
Tool: search_recipes

Agent-facing wrapper around src.database.recipes.search_recipes.

The database layer already implements the actual search logic
(name/description matching, max cook time filter). This tool's
job is to give the agent a clean, validated, error-safe interface
to that logic — since the DB function itself will raise on bad
input rather than returning a structured error.
"""

from src.database.recipes import search_recipes as _db_search_recipes


def search_recipes(
    user_id: int,
    search_term: str | None = None,
    max_cook_time: int | None = None,
) -> dict:
    """
    Search a user's saved recipes by name/description, optionally
    filtered by maximum cooking time.

    Args:
        user_id (int): The ID of the user whose recipes to search.
        search_term (str | None): Text to match against recipe
            name or description (case-insensitive substring
            match). If None or empty, no text filter is applied.
        max_cook_time (int | None): Only include recipes with
            cook_time less than or equal to this value (minutes).
            If None, no time filter is applied.

    Returns:
        dict: {
            "success": bool,
            "error": str | None,
            "count": int | None,
            "recipes": list[dict] | None,
        }
    """

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