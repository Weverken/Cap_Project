from src.tools.find_recipe_substitution import find_recipe_substitution


def test_finds_known_ingredient():
    result = find_recipe_substitution("buttermilk")

    assert result["success"] is True
    assert result["found"] is True
    assert len(result["substitutions"]) >= 1
    assert "substitute" in result["substitutions"][0]
    assert "ratio" in result["substitutions"][0]


def test_case_insensitive_and_trims_whitespace():
    result = find_recipe_substitution("  Baking Powder  ")

    assert result["found"] is True
    assert result["ingredient"] == "baking powder"


def test_returns_multiple_options_when_available():
    result = find_recipe_substitution("egg")

    assert result["found"] is True
    assert len(result["substitutions"]) == 2


def test_unknown_ingredient_returns_found_false_not_error():
    result = find_recipe_substitution("saffron")

    assert result["success"] is True
    assert result["found"] is False
    assert result["substitutions"] is None
    assert result["error"] is None


def test_rejects_empty_string():
    result = find_recipe_substitution("")

    assert result["success"] is False
    assert result["error"] is not None


def test_rejects_non_string_input():
    result = find_recipe_substitution(123)

    assert result["success"] is False


def test_rejects_whitespace_only_string():
    result = find_recipe_substitution("   ")

    assert result["success"] is False