"""
Tool: find_recipes_by_ingredients

Given a list of ingredients someone has on hand, finds which of
their saved recipes are the closest match — ranked by how many
required ingredients they already have, with the rest listed as
missing.

This is the tool behind prompts like:
"I have chicken, rice, and broccoli. What can I make?"
"""


def find_by_ingredients(
    recipes: list,
    available_ingredients: list,
    min_match_ratio: float = 0.0,
) -> dict:
    """
    Rank a user's saved recipes by how well they match a list of
    ingredients the user currently has.

    Args:
        recipes (list[dict]): Recipes as returned by
            src.database.recipes.get_all_recipes(). Each recipe
            must have "id", "name", and "ingredients" (list of
            dicts with a "name" key).
        available_ingredients (list[str]): Ingredients the user
            currently has on hand (e.g. ["chicken", "rice",
            "broccoli"]). Matching is case-insensitive and uses
            substring matching in both directions, so "chicken
            breast" in a recipe matches "chicken" in the list.
        min_match_ratio (float): Only include recipes where at
            least this fraction of ingredients are matched
            (0.0-1.0). Defaults to 0.0 (include everything, let
            the caller/agent decide what's a "close enough" match).

    Returns:
        dict: {
            "success": bool,
            "error": str | None,
            "available_ingredients": list[str],
            "matches": list[dict] | None,
            # Each match: {
            #   "recipe_id", "recipe_name",
            #   "match_ratio" (0.0-1.0),
            #   "matched_ingredients": list[str],
            #   "missing_ingredients": list[str],
            # }
            # Sorted by match_ratio descending, then by fewest
            # missing ingredients.
        }
    """

    # ---- Input validation ----

    if not isinstance(recipes, list):
        return _error("recipes must be a list.")

    if not isinstance(available_ingredients, list) or len(available_ingredients) == 0:
        return _error("available_ingredients must be a non-empty list.")

    if not all(isinstance(item, str) for item in available_ingredients):
        return _error("available_ingredients must all be strings.")

    if not isinstance(min_match_ratio, (int, float)) or not (0.0 <= min_match_ratio <= 1.0):
        return _error("min_match_ratio must be a number between 0.0 and 1.0.")

    normalized_available = [
        ingredient.strip().lower()
        for ingredient in available_ingredients
        if ingredient.strip()
    ]

    if not normalized_available:
        return _error("available_ingredients contained no usable values.")

    # ---- Matching ----

    matches = []

    for recipe in recipes:
        if not isinstance(recipe, dict) or "ingredients" not in recipe:
            continue

        recipe_ingredients = recipe.get("ingredients", [])

        if not isinstance(recipe_ingredients, list) or len(recipe_ingredients) == 0:
            continue

        matched = []
        missing = []

        for ingredient in recipe_ingredients:
            if not isinstance(ingredient, dict):
                continue

            ingredient_name = ingredient.get("name", "").strip()

            if not ingredient_name:
                continue

            if _is_available(ingredient_name, normalized_available):
                matched.append(ingredient_name)
            else:
                missing.append(ingredient_name)

        total = len(matched) + len(missing)

        if total == 0:
            continue

        match_ratio = round(len(matched) / total, 3)

        if match_ratio < min_match_ratio:
            continue

        matches.append(
            {
                "recipe_id": recipe.get("id"),
                "recipe_name": recipe.get("name", "Untitled recipe"),
                "match_ratio": match_ratio,
                "matched_ingredients": matched,
                "missing_ingredients": missing,
            }
        )

    matches.sort(
        key=lambda m: (-m["match_ratio"], len(m["missing_ingredients"]))
    )

    return {
        "success": True,
        "error": None,
        "available_ingredients": normalized_available,
        "matches": matches,
    }


def _is_available(ingredient_name: str, normalized_available: list) -> bool:
    """
    Check if a recipe ingredient is covered by the available
    ingredients list, using case-insensitive substring matching
    in both directions (e.g. "chicken breast" <-> "chicken").
    """
    name = ingredient_name.lower()

    for available in normalized_available:
        if available in name or name in available:
            return True

    return False


def _error(message: str) -> dict:
    """Build a standard error response."""
    return {
        "success": False,
        "error": message,
        "available_ingredients": None,
        "matches": None,
    }