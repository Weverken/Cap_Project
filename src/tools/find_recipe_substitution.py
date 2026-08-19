"""
Tool: find_recipe_substitution

Looks up a deterministic substitution for a small set of
ratio-sensitive ingredients — ones where getting the substitution
ratio wrong changes how the recipe actually turns out (leavening
agents, eggs/buttermilk in baking, etc.).

This is intentionally NOT a comprehensive substitution database.
For ingredients not covered here, the tool returns found=False so
the calling agent can fall back to its own general knowledge and
present the answer as a suggestion rather than a tested ratio.
"""


# Each entry: canonical ingredient -> list of substitution options.
# Each option includes the substitute, the ratio relative to the
# original ingredient, and a short note on any caveat.
SUBSTITUTION_TABLE = {
    "baking powder": [
        {
            "substitute": "baking soda + cream of tartar",
            "ratio": "1 tsp baking powder = 1/4 tsp baking soda + 1/2 tsp cream of tartar",
            "note": "Use immediately; the reaction starts as soon as it's mixed with liquid.",
        },
    ],
    "baking soda": [
        {
            "substitute": "baking powder",
            "ratio": "1 tsp baking soda = 3 tsp baking powder",
            "note": "Baking powder is weaker; you need about 3x as much. May slightly affect flavor/texture.",
        },
    ],
    "buttermilk": [
        {
            "substitute": "milk + lemon juice or vinegar",
            "ratio": "1 cup buttermilk = 1 cup milk + 1 tbsp lemon juice or vinegar, rested 5-10 min",
            "note": "Let it sit until slightly curdled before using.",
        },
        {
            "substitute": "plain yogurt",
            "ratio": "1 cup buttermilk = 1 cup yogurt thinned with a splash of milk",
            "note": "Good for pancakes/baking; slightly tangier.",
        },
    ],
    "egg": [
        {
            "substitute": "unsweetened applesauce",
            "ratio": "1 egg = 1/4 cup applesauce",
            "note": "Best in baking (cakes, muffins); adds slight sweetness/moisture, won't work for meringue-type uses.",
        },
        {
            "substitute": "flaxseed meal + water",
            "ratio": "1 egg = 1 tbsp ground flaxseed + 3 tbsp water, rested 5 min",
            "note": "Works as a binder in baking; adds a mild nutty flavor.",
        },
    ],
    "butter": [
        {
            "substitute": "vegetable oil",
            "ratio": "1 cup butter = 3/4 cup oil",
            "note": "Best for moist bakes (muffins, quick breads); changes texture in cookies.",
        },
        {
            "substitute": "margarine",
            "ratio": "1 cup butter = 1 cup margarine",
            "note": "1:1 swap; flavor will be milder.",
        },
    ],
    "cornstarch": [
        {
            "substitute": "all-purpose flour",
            "ratio": "1 tbsp cornstarch = 2 tbsp flour",
            "note": "Use for thickening sauces/gravies; flour makes the result slightly more opaque.",
        },
    ],
    "sour cream": [
        {
            "substitute": "plain yogurt",
            "ratio": "1 cup sour cream = 1 cup plain yogurt",
            "note": "1:1 swap; yogurt is slightly tangier and less rich.",
        },
    ],
    "heavy cream": [
        {
            "substitute": "milk + butter",
            "ratio": "1 cup heavy cream = 3/4 cup milk + 1/4 cup melted butter",
            "note": "Won't whip into stiff peaks, but works fine for cooking/baking.",
        },
    ],
    "brown sugar": [
        {
            "substitute": "white sugar + molasses",
            "ratio": "1 cup brown sugar = 1 cup white sugar + 1 tbsp molasses",
            "note": "Mix well before using.",
        },
    ],
    "self-rising flour": [
        {
            "substitute": "all-purpose flour + baking powder + salt",
            "ratio": "1 cup self-rising flour = 1 cup flour + 1.5 tsp baking powder + 1/4 tsp salt",
            "note": "Standard homemade equivalent.",
        },
    ],
    "yeast": [
        {
            "substitute": "baking powder",
            "ratio": "Not a direct ratio substitute",
            "note": "Baking powder can't replicate yeast's rise in bread; only works for quick breads, not yeasted dough.",
        },
    ],
    "honey": [
        {
            "substitute": "white sugar + water",
            "ratio": "1 cup honey = 1 1/4 cup sugar + 1/4 cup water",
            "note": "Reduce other liquids in the recipe slightly since honey adds moisture too.",
        },
    ],
    "molasses": [
        {
            "substitute": "brown sugar",
            "ratio": "1 cup molasses = 1 cup packed brown sugar",
            "note": "Reduces overall liquid in the recipe; texture/flavor will be milder.",
        },
    ],
    "cream of tartar": [
        {
            "substitute": "lemon juice or white vinegar",
            "ratio": "1/2 tsp cream of tartar = 1 1/2 tsp lemon juice or vinegar",
            "note": "Works for stabilizing egg whites/preventing sugar crystallization.",
        },
    ],
    "shortening": [
        {
            "substitute": "butter",
            "ratio": "1 cup shortening = 1 cup butter",
            "note": "1:1 swap; baked goods will spread slightly more and taste richer.",
        },
    ],
}


def find_recipe_substitution(ingredient: str) -> dict:
    """
    Look up a deterministic substitution for an ingredient.

    Args:
        ingredient (str): The ingredient to find a substitute for
            (e.g. "buttermilk", "baking powder"). Case-insensitive,
            leading/trailing whitespace is ignored.

    Returns:
        dict: {
            "success": bool,          # False only on bad input
            "error": str | None,
            "ingredient": str,
            "found": bool,            # True if a match was found
            "substitutions": list[dict] | None,
            # Each substitution dict: substitute, ratio, note
        }

    Note:
        This tool only covers ingredients where the substitution
        ratio meaningfully affects the outcome (leavening agents,
        eggs/dairy in baking, etc.). If found=False, the calling
        agent should answer from its own general knowledge and
        present it as a suggestion rather than a tested ratio.
    """

    if not isinstance(ingredient, str) or not ingredient.strip():
        return {
            "success": False,
            "error": "ingredient must be a non-empty string.",
            "ingredient": ingredient,
            "found": False,
            "substitutions": None,
        }

    key = ingredient.strip().lower()

    if key in SUBSTITUTION_TABLE:
        return {
            "success": True,
            "error": None,
            "ingredient": key,
            "found": True,
            "substitutions": SUBSTITUTION_TABLE[key],
        }

    return {
        "success": True,
        "error": None,
        "ingredient": key,
        "found": False,
        "substitutions": None,
    }