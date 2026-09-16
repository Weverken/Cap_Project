"""
Scales a recipe's ingredients up or down for a different serving size.

Doesn't round anything - if scaling gives you 2.5 eggs, that's what you
get back. Whether to round that up/down is a judgment call better left
to the agent (it has context this function doesn't).
"""


def scale_recipe(recipe: dict, target_servings: int) -> dict:
    """Scale recipe['ingredients'] to target_servings.

    recipe needs "servings" and "ingredients" (list of dicts with
    quantity/unit/name). Returns a dict with success/error plus the
    scaled ingredients and the scale factor used. Never raises -
    anything wrong with the input comes back in "error"."""

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
    return {
        "success": False,
        "error": message,
        "original_servings": None,
        "target_servings": None,
        "scale_factor": None,
        "ingredients": None,
    }
