from src.tools.find_by_ingredients import find_recipes_by_ingredients


SAMPLE_RECIPES = [
    {
        "id": 1,
        "name": "Chicken Fried Rice",
        "ingredients": [
            {"name": "chicken breast"},
            {"name": "rice"},
            {"name": "soy sauce"},
            {"name": "egg"},
        ],
    },
    {
        "id": 2,
        "name": "Broccoli Stir Fry",
        "ingredients": [
            {"name": "broccoli"},
            {"name": "garlic"},
            {"name": "soy sauce"},
        ],
    },
    {
        "id": 3,
        "name": "Beef Tacos",
        "ingredients": [
            {"name": "ground beef"},
            {"name": "taco shells"},
            {"name": "cheese"},
        ],
    },
]


def test_ranks_by_match_ratio():
    result = find_recipes_by_ingredients(
        SAMPLE_RECIPES,
        ["chicken", "rice", "broccoli", "soy sauce"],
    )

    assert result["success"] is True
    names = [m["recipe_name"] for m in result["matches"]]

    # Chicken Fried Rice: 3/4 matched, Broccoli Stir Fry: 2/3 matched
    assert names[0] == "Chicken Fried Rice"
    assert names[1] == "Broccoli Stir Fry"


def test_reports_missing_ingredients():
    result = find_recipes_by_ingredients(
        SAMPLE_RECIPES,
        ["chicken", "rice"],
    )

    fried_rice = next(
        m for m in result["matches"] if m["recipe_name"] == "Chicken Fried Rice"
    )

    assert "soy sauce" in fried_rice["missing_ingredients"]
    assert "egg" in fried_rice["missing_ingredients"]
    assert len(fried_rice["matched_ingredients"]) == 2


def test_zero_match_recipe_included_with_ratio_zero():
    result = find_recipes_by_ingredients(
        SAMPLE_RECIPES,
        ["chicken", "rice"],
    )

    tacos = next(m for m in result["matches"] if m["recipe_name"] == "Beef Tacos")

    assert tacos["match_ratio"] == 0.0


def test_min_match_ratio_filters_out_low_matches():
    result = find_recipes_by_ingredients(
        SAMPLE_RECIPES,
        ["chicken", "rice"],
        min_match_ratio=0.5,
    )

    names = [m["recipe_name"] for m in result["matches"]]

    assert "Beef Tacos" not in names
    assert "Chicken Fried Rice" in names


def test_case_insensitive_matching():
    result = find_recipes_by_ingredients(
        SAMPLE_RECIPES,
        ["CHICKEN", "Rice"],
    )

    fried_rice = next(
        m for m in result["matches"] if m["recipe_name"] == "Chicken Fried Rice"
    )

    assert "chicken breast" in fried_rice["matched_ingredients"]


def test_substring_matches_both_directions():
    # "chicken" should match "chicken breast" (available is substring of recipe ingredient)
    result = find_recipes_by_ingredients(
        [{"id": 9, "name": "Test", "ingredients": [{"name": "chicken"}]}],
        ["chicken breast"],
    )

    assert result["matches"][0]["match_ratio"] == 1.0


def test_rejects_empty_available_ingredients():
    result = find_recipes_by_ingredients(SAMPLE_RECIPES, [])

    assert result["success"] is False


def test_rejects_non_list_recipes():
    result = find_recipes_by_ingredients("not a list", ["chicken"])

    assert result["success"] is False


def test_rejects_invalid_min_match_ratio():
    result = find_recipes_by_ingredients(
        SAMPLE_RECIPES, ["chicken"], min_match_ratio=1.5
    )

    assert result["success"] is False


def test_handles_empty_recipes_list():
    result = find_recipes_by_ingredients([], ["chicken"])

    assert result["success"] is True
    assert result["matches"] == []


def test_skips_malformed_recipe_entries():
    malformed = [{"id": 1, "name": "Broken"}]  # missing "ingredients"

    result = find_recipes_by_ingredients(malformed, ["chicken"])

    assert result["success"] is True
    assert result["matches"] == []