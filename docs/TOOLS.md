# Tools

This document covers every tool registered with the cooking assistant's Gemini agent, defined in `src/agent/tools.py`. These are the functions the model can call on its own during a conversation, when it decides a request needs one of them.

A quick note on how this is organized before the individual tools: most of these wrap a plain, deterministic function from `src/tools/`. The reason there's a wrapper at all is that the model can only pass simple values like strings and numbers into a tool call. It has no way to hand over a full recipe dict pulled from the database, and it shouldn't be trusted with raw database access either. So the wrapper in `src/agent/tools.py` takes the simple arguments the model provides, does whatever database lookup is needed, and only then calls the underlying pure function. `get_current_cooking_session_tool`, `advance_cooking_step_tool`, `log_cooking_substitution_tool`, and `save_recipe_change_tool` don't have a separate pure-function counterpart since they're tied directly to database state (the active cooking session, or a saved recipe).

All tools return a dictionary rather than raising exceptions. Most include a `success` key so the agent can check whether the call worked without needing a try/except around every call.

---

## scale_recipe_tool

Scales a saved recipe's ingredients to a different number of servings.

**Wraps:** `src.tools.scale_recipe.scale_recipe`

**Parameters:**
- `recipe_name` (string): the name of the recipe to scale, as it appears in the user's recipe book. Matching is case-insensitive, and falls back to a substring match if there's no exact hit.
- `target_servings` (integer): the number of servings to scale to.

**Returns:**
```
{
  "success": bool,
  "error": str or null,
  "original_servings": int,
  "target_servings": int,
  "scale_factor": float,
  "ingredients": [{"name": str, "unit": str, "quantity": float}, ...]
}
```

One thing worth knowing: this doesn't round quantities for countable ingredients. If scaling produces something like 2.5 eggs, it stays 2.5. Rounding that sensibly depends on context the tool doesn't have (is half an egg workable here, should it round up or down), so that judgment call is left to the agent, guided by the system prompt.

---

## convert_measurement_tool

Converts a quantity from one unit to another, as long as both units are in the same category (volume to volume, or weight to weight).

**Wraps:** `src.tools.convert_measurement.convert_measurement`

**Parameters:**
- `quantity` (number): the amount to convert.
- `from_unit` (string): starting unit, e.g. `"cup"`, `"g"`, `"tbsp"`.
- `to_unit` (string): target unit.

**Returns:**
```
{
  "success": bool,
  "error": str or null,
  "original_quantity": float,
  "from_unit": str,
  "converted_quantity": float or null,
  "to_unit": str
}
```

This intentionally does not convert across categories, like cups to grams. That conversion depends on the specific ingredient's density (flour and sugar don't weigh the same per cup), which isn't something this tool can know. If the model gets asked for a cross-category conversion, the call fails cleanly and the system prompt tells the agent to answer from general knowledge instead, with a note that it's an estimate.

---

## find_recipe_substitution_tool

Looks up a tested substitution for an ingredient, but only for a specific list of ingredients where getting the ratio wrong actually matters (mostly leavening agents and a handful of baking staples).

**Wraps:** `src.tools.find_recipe_substitution.find_recipe_substitution`

**Parameters:**
- `ingredient` (string): the ingredient to substitute, e.g. `"buttermilk"`.

**Returns:**
```
{
  "success": bool,
  "error": str or null,
  "ingredient": str,
  "found": bool,
  "substitutions": [{"substitute": str, "ratio": str, "note": str}, ...] or null
}
```

This is deliberately a short list, around 15 entries, rather than an attempt at a comprehensive substitution database. If the ingredient isn't in the table, `found` comes back `false` with no error. That's the signal for the agent to fall back on its own general cooking knowledge instead, and say so, rather than pretending the table has an answer it doesn't.

---

## find_recipes_by_ingredients_tool

Ranks the user's saved recipes by how many of the listed ingredients they already cover.

**Wraps:** `src.tools.find_by_ingredients.find_by_ingredients`

**Parameters:**
- `available_ingredients` (list of strings): what the user currently has on hand, e.g. `["chicken", "rice", "broccoli"]`.

**Returns:**
```
{
  "success": bool,
  "error": str or null,
  "available_ingredients": [str, ...],
  "matches": [
    {
      "recipe_id": int,
      "recipe_name": str,
      "match_ratio": float,
      "matched_ingredients": [str, ...],
      "missing_ingredients": [str, ...]
    },
    ...
  ] or null
}
```

Matching uses case-insensitive substring comparison in both directions, so "chicken" in the ingredient list matches "chicken breast" in a recipe. Matches are sorted by match ratio first, then by fewest missing ingredients, so the closest match to "make with what you have" comes first.

---

## search_recipes_tool

Searches the user's saved recipes by name or description text, with an optional cap on cook time.

**Wraps:** `src.tools.search_recipes.search_recipes`

**Parameters:**
- `search_term` (string, optional): text to match against recipe name or description.
- `max_cook_time` (integer, optional): only return recipes with a cook time at or under this many minutes.

**Returns:**
```
{
  "success": bool,
  "error": str or null,
  "count": int or null,
  "recipes": [recipe dict, ...] or null
}
```

Both parameters are optional, so this also works as "show me everything" with no filters at all.

---

## get_current_cooking_session_tool

Looks up whatever the user is actively cooking right now, including which step they're on.

**Parameters:** none.

**Returns:**
```
{
  "success": bool,
  "has_active_session": bool,
  "recipe_name": str,
  "servings": int,
  "current_step_number": int,
  "total_steps": int,
  "current_step_instruction": str,
  "substitutions_logged_this_session": [str, ...]
}
```

The system prompt tells the agent to call this whenever a message only makes sense in the context of an active cooking session, things like "this step" or "the sauce looks too thick" with no recipe named. Without this tool, the agent would have no way to know what "this" refers to.

---

## advance_cooking_step_tool

Moves the active cooking session forward or back a step. This is the same action as clicking the Previous or Next buttons in Cooking Mode, just triggered through conversation instead ("go to the next step").

**Parameters:**
- `direction` (string): either `"next"` or `"previous"`.

**Returns:**
```
{
  "success": bool,
  "error": str or null,
  "current_step_number": int,
  "total_steps": int,
  "current_step_instruction": str or null
}
```

The step index is clamped, so calling "next" on the last step just stays on the last step rather than erroring or going out of bounds.

---

## log_cooking_substitution_tool

Records a substitution or change for the current cooking session only. This does not touch the saved recipe in any way, it's scoped to this one cooking session.

**Parameters:**
- `note` (string): a short description of what changed, e.g. `"used oat milk instead of dairy"`.

**Returns:**
```
{
  "success": bool,
  "error": str or null,
  "logged": str
}
```

If there's no active cooking session, this fails, since there's nowhere to attach the note.

---

## save_recipe_change_tool

Permanently edits the currently-cooking recipe in the database, replacing one ingredient with another. This is the tool behind "save that substitution" or "replace X with Y from now on."

**Parameters:**
- `original_ingredient_name` (string): the ingredient currently in the recipe to replace.
- `new_ingredient_name` (string): what to replace it with.
- `new_quantity` (number, optional): new quantity, if it should change. Leave out to keep the original amount.
- `new_unit` (string, optional): new unit, if it should change. Leave out to keep the original unit.

**Returns:**
```
{
  "success": bool,
  "error": str or null,
  "recipe_name": str,
  "replaced": str,
  "with": str
}
```

This is the one tool in the set that writes a permanent change to the database rather than just logging it for the session. The system prompt is explicit that the agent should only call this when the user clearly means "from now on" rather than "just for this one time," and to check with the user if that's ambiguous. That distinction is enforced through prompt instructions, not code, so it depends on the model actually following it. `log_cooking_substitution_tool` is the safer default for anything that isn't clearly meant to be permanent.

---

## A note on ingredient name matching

Several of these tools (`save_recipe_change_tool`, `find_recipes_by_ingredients_tool`) match ingredient names using case-insensitive substring comparison rather than exact matching. This is intentional, since a user is far more likely to say "chicken" than "boneless skinless chicken breast," and exact matching would fail constantly. The tradeoff is that substring matching can occasionally match the wrong thing if two ingredients share a substring in an unlucky way. In practice this hasn't come up as a real problem, but it's worth knowing about if a match seems off.