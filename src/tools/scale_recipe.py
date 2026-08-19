"""
Tool: scale_recipe

Scales a recipe's ingredient quantities up or down based on a
target number of servings.

Note: this tool returns raw scaled quantities (e.g. 2.5 eggs)
without rounding. Whether to round a countable ingredient like
eggs or garlic cloves up/down is a judgment call left to the
agent, which has conversational context the tool doesn't.
"""


def scale_recipe(recipe: dict, target_servings: int) -> dict:
    """
    Scale a recipe's ingredients to a new serving size.

    Args:
        recipe (dict): A recipe dict as returned by
            src.database.recipes.get_recipe(). Must contain
            "servings" (int) and "ingredients" (list of dicts
            with "quantity", "unit", "name").
        target_servings (int): The desired number of servings.
            Must be a positive integer.

    Returns:
        dict: {
            "success": bool,
            "error": str | None,
            "original_servings": int,
            "target_servings": int,
            "scale_factor": float,
            "ingredients": list[dict]  # scaled ingredients
        }

    Raises:
        Nothing. All errors are returned in the "error" field so
        this is safe to call directly from agent tool-calling code.
    """

    # ---- Input validation ----

    if not isinstance(recipe, dict):
        return _error("recipe must be a dictionary.")

    if "servings" not in recipe or "ingredients" not in recipe:
        return _error(
            "recipe must include 'servings' and 'ingredients'."
        )

    original_servings = recipe["servings"]

    if not isinstance(original_servings, (int, float)) or original_servings <= 0:
        return _error("recipe's original servings must be a positive number.")

    if not isinstance(target_servings, (int, float)):
        return _error("target_servings must be a number.")

    if target_servings <= 0:
        return _error("target_servings must be greater than 0.")

    ingredients = recipe["ingredients"]

    if not isinstance(ingredients, list) or len(ingredients) == 0:
        return _error("recipe must have at least one ingredient.")

    # ---- Scaling logic ----

    scale_factor = target_servings / original_servings

    scaled_ingredients = []

    for ingredient in ingredients:
        if not isinstance(ingredient, dict) or "quantity" not in ingredient:
            return _error(
                f"Malformed ingredient entry: {ingredient!r}"
            )

        try:
            original_quantity = float(ingredient["quantity"])
        except (TypeError, ValueError):
            return _error(
                f"Ingredient '{ingredient.get('name', '?')}' has a "
                f"non-numeric quantity."
            )

        scaled_quantity = round(original_quantity * scale_factor, 2)

        scaled_ingredients.append(
            {
                "name": ingredient.get("name", ""),
                "unit": ingredient.get("unit", ""),
                "quantity": scaled_quantity,
            }
        )

    return {
        "success": True,
        "error": None,
        "original_servings": original_servings,
        "target_servings": target_servings,
        "scale_factor": round(scale_factor, 4),
        "ingredients": scaled_ingredients,
    }


def _error(message: str) -> dict:
    """Build a standard error response."""
    return {
        "success": False,
        "error": message,
        "original_servings": None,
        "target_servings": None,
        "scale_factor": None,
        "ingredients": None,
    }