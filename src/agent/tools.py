"""
Agent-facing tool wrappers.

These are the functions actually registered with the Gemini
client as tools. They exist because the Day 3 tools in
src/tools/ operate on data (full recipe dicts, lists of recipes)
that the LLM has no way to supply directly — it can only provide
simple values like a recipe name or a list of ingredient strings.

Each wrapper here:
1. Takes simple, LLM-supplyable arguments.
2. Fetches whatever data it needs from the database.
3. Delegates the actual logic to the corresponding Day 3 tool.

The docstrings on these functions are used by the Gemini SDK to
auto-generate the tool schema the model sees, so they double as
the tool's user-facing description — keep them accurate.
"""

from src.config import DEFAULT_USER_ID
from src.database.recipes import get_all_recipes, get_recipe, update_recipe
from src.database.cooking_sessions import (
    get_active_session,
    update_session_step,
    add_session_substitution,
)
from src.tools.scale_recipe import scale_recipe as _scale_recipe
from src.tools.convert_measurement import convert_measurement as _convert_measurement
from src.tools.find_recipe_substitution import (
    find_recipe_substitution as _find_recipe_substitution,
)
from src.tools.find_by_ingredients import find_by_ingredients as _find_by_ingredients
from src.tools.search_recipes import search_recipes as _search_recipes


def _find_recipe_by_name(name: str) -> dict | None:
    """Case-insensitive lookup of a saved recipe by name."""
    recipes = get_all_recipes(DEFAULT_USER_ID)
    name_lower = name.strip().lower()

    for recipe in recipes:
        if recipe["name"].strip().lower() == name_lower:
            return recipe

    # Fall back to substring match if there's no exact match.
    for recipe in recipes:
        if name_lower in recipe["name"].strip().lower():
            return recipe

    return None


def scale_recipe_tool(recipe_name: str, target_servings: int) -> dict:
    """
    Scale a saved recipe's ingredients to a new number of servings.

    Args:
        recipe_name: The name of the recipe to scale, as saved in
            the user's recipe book (e.g. "Chicken Curry").
        target_servings: The desired number of servings.
    """
    recipe = _find_recipe_by_name(recipe_name)

    if recipe is None:
        return {
            "success": False,
            "error": f"No saved recipe found matching '{recipe_name}'.",
        }

    return _scale_recipe(recipe, target_servings)


def convert_measurement_tool(quantity: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert a quantity from one measurement unit to another.
    Only works within the same category (volume-to-volume, e.g.
    cups to tbsp, or weight-to-weight, e.g. grams to ounces).

    Args:
        quantity: The numeric amount to convert.
        from_unit: The unit to convert from (e.g. "cup", "g").
        to_unit: The unit to convert to (e.g. "tbsp", "oz").
    """
    return _convert_measurement(quantity, from_unit, to_unit)


def find_recipe_substitution_tool(ingredient: str) -> dict:
    """
    Look up a tested substitution ratio for a ratio-sensitive
    ingredient (e.g. baking powder, buttermilk, eggs in baking).
    Returns found=False if the ingredient isn't in the app's
    substitution database — in that case, answer from general
    knowledge instead and say so.

    Args:
        ingredient: The ingredient to find a substitute for.
    """
    return _find_recipe_substitution(ingredient)


def find_recipes_by_ingredients_tool(available_ingredients: list[str]) -> dict:
    """
    Find the user's saved recipes that best match a list of
    ingredients they currently have on hand, ranked by how many
    required ingredients are covered.

    Args:
        available_ingredients: Ingredients the user currently has
            (e.g. ["chicken", "rice", "broccoli"]).
    """
    recipes = get_all_recipes(DEFAULT_USER_ID)
    return _find_by_ingredients(recipes, available_ingredients)


def search_recipes_tool(
    search_term: str | None = None,
    max_cook_time: int | None = None,
) -> dict:
    """
    Search the user's saved recipes by name/description text,
    optionally filtered by maximum cook time.

    Args:
        search_term: Text to match against recipe name or
            description. Omit to skip text filtering.
        max_cook_time: Only include recipes with cook time (in
            minutes) at or below this value. Omit to skip.
    """
    return _search_recipes(
        user_id=DEFAULT_USER_ID,
        search_term=search_term,
        max_cook_time=max_cook_time,
    )


def get_current_cooking_session_tool() -> dict:
    """
    Get details of the recipe the user is currently cooking right
    now, if any — including which step they're on and any
    substitutions/changes already logged for this session.

    Call this whenever the user refers to "this recipe", "this
    step", "what I'm cooking", or asks something that only makes
    sense in the context of an active cooking session (e.g. "the
    sauce looks too thick"), so you know exactly what they mean
    without asking them to repeat themselves.
    """
    session = get_active_session(DEFAULT_USER_ID)

    if session is None:
        return {
            "success": True,
            "has_active_session": False,
            "message": "No recipe is currently being cooked.",
        }

    recipe = get_recipe(session["recipe_id"])

    if recipe is None:
        return {
            "success": False,
            "has_active_session": False,
            "message": "Active session refers to a recipe that no longer exists.",
        }

    instructions = recipe["instructions"]
    step_index = session["current_step"]
    total_steps = len(instructions)
    current_instruction = (
        instructions[step_index] if 0 <= step_index < total_steps else None
    )

    return {
        "success": True,
        "has_active_session": True,
        "recipe_name": recipe["name"],
        "servings": session["servings"],
        "current_step_number": step_index + 1,
        "total_steps": total_steps,
        "current_step_instruction": current_instruction,
        "substitutions_logged_this_session": session["substitutions"],
    }


def advance_cooking_step_tool(direction: str) -> dict:
    """
    Move the active cooking session to the next or previous step.

    Args:
        direction: Either "next" or "previous".
    """
    if direction not in ("next", "previous"):
        return {"success": False, "error": "direction must be 'next' or 'previous'."}

    session = get_active_session(DEFAULT_USER_ID)

    if session is None:
        return {"success": False, "error": "No recipe is currently being cooked."}

    recipe = get_recipe(session["recipe_id"])
    total_steps = len(recipe["instructions"]) if recipe else 0

    new_step = session["current_step"] + (1 if direction == "next" else -1)
    new_step = max(0, min(new_step, max(total_steps - 1, 0)))

    update_session_step(session["id"], new_step)

    return {
        "success": True,
        "current_step_number": new_step + 1,
        "total_steps": total_steps,
        "current_step_instruction": (
            recipe["instructions"][new_step] if recipe else None
        ),
    }


def log_cooking_substitution_tool(note: str) -> dict:
    """
    Record a substitution or change the user made during the
    current cooking session (e.g. "used applesauce instead of
    egg"), so it can be referenced later in the same session —
    for example if they ask "what did I substitute again?".

    Args:
        note: A short description of the substitution/change.
    """
    session = get_active_session(DEFAULT_USER_ID)

    if session is None:
        return {"success": False, "error": "No recipe is currently being cooked."}

    if not note or not note.strip():
        return {"success": False, "error": "note must not be empty."}

    add_session_substitution(session["id"], note.strip())

    return {"success": True, "logged": note.strip()}


def save_recipe_change_tool(
    original_ingredient_name: str,
    new_ingredient_name: str,
    new_quantity: float | None = None,
    new_unit: str | None = None,
) -> dict:
    """
    Permanently update the currently-cooking recipe in the user's
    recipe book — replacing one ingredient with another. Use this
    when the user explicitly asks to save/keep a substitution or
    change for future use (e.g. "save that substitution", "replace
    the soy sauce with tamari from now on"), as opposed to a
    one-off change for just this cooking session (use
    log_cooking_substitution_tool for that instead).

    Args:
        original_ingredient_name: The ingredient currently in the
            saved recipe to replace (e.g. "soy sauce").
        new_ingredient_name: What to replace it with (e.g. "tamari").
        new_quantity: New quantity, if it should change. Omit to
            keep the original ingredient's quantity.
        new_unit: New unit, if it should change. Omit to keep the
            original ingredient's unit.
    """
    session = get_active_session(DEFAULT_USER_ID)

    if session is None:
        return {
            "success": False,
            "error": "No recipe is currently being cooked, so there's "
            "nothing to permanently update. Start a cooking session first.",
        }

    recipe = get_recipe(session["recipe_id"])

    if recipe is None:
        return {"success": False, "error": "The recipe for this session no longer exists."}

    ingredients = recipe["ingredients"]
    target_name = original_ingredient_name.strip().lower()

    match_index = None
    for i, ing in enumerate(ingredients):
        if ing["name"].strip().lower() == target_name:
            match_index = i
            break

    if match_index is None:
        for i, ing in enumerate(ingredients):
            if target_name in ing["name"].strip().lower():
                match_index = i
                break

    if match_index is None:
        return {
            "success": False,
            "error": f"Couldn't find '{original_ingredient_name}' in this recipe's ingredients.",
        }

    old_ingredient = ingredients[match_index]
    updated_ingredient = {
        "quantity": new_quantity if new_quantity is not None else old_ingredient["quantity"],
        "unit": new_unit if new_unit is not None else old_ingredient["unit"],
        "name": new_ingredient_name,
    }
    ingredients[match_index] = updated_ingredient

    update_recipe(
        recipe_id=recipe["id"],
        name=recipe["name"],
        description=recipe["description"],
        servings=recipe["servings"],
        prep_time=recipe["prep_time"],
        cook_time=recipe["cook_time"],
        ingredients=ingredients,
        instructions=recipe["instructions"],
        tags=recipe["tags"],
    )

    return {
        "success": True,
        "recipe_name": recipe["name"],
        "replaced": old_ingredient["name"],
        "with": new_ingredient_name,
    }


# The list registered as `tools` on the Gemini chat session.
AGENT_TOOLS = [
    scale_recipe_tool,
    convert_measurement_tool,
    find_recipe_substitution_tool,
    find_recipes_by_ingredients_tool,
    search_recipes_tool,
    get_current_cooking_session_tool,
    advance_cooking_step_tool,
    log_cooking_substitution_tool,
    save_recipe_change_tool,
]