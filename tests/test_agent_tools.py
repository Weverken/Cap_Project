from unittest.mock import patch

from src.agent.tools import (
    scale_recipe_tool,
    find_recipes_by_ingredients_tool,
    convert_measurement_tool,
    find_recipe_substitution_tool,
)


SAMPLE_RECIPES = [
    {
        "id": 1,
        "name": "Chicken Curry",
        "servings": 4,
        "ingredients": [
            {"name": "chicken", "quantity": 2, "unit": "lb"},
            {"name": "curry powder", "quantity": 2, "unit": "tbsp"},
        ],
    },
    {
        "id": 2,
        "name": "Veggie Stir Fry",
        "servings": 2,
        "ingredients": [
            {"name": "broccoli", "quantity": 1, "unit": "cup"},
        ],
    },
]


@patch("src.agent.tools.get_all_recipes")
def test_scale_recipe_tool_exact_name_match(mock_get_all):
    mock_get_all.return_value = SAMPLE_RECIPES

    result = scale_recipe_tool("Chicken Curry", 8)

    assert result["success"] is True
    assert result["scale_factor"] == 2.0


@patch("src.agent.tools.get_all_recipes")
def test_scale_recipe_tool_case_insensitive(mock_get_all):
    mock_get_all.return_value = SAMPLE_RECIPES

    result = scale_recipe_tool("chicken curry", 8)

    assert result["success"] is True


@patch("src.agent.tools.get_all_recipes")
def test_scale_recipe_tool_substring_fallback(mock_get_all):
    mock_get_all.return_value = SAMPLE_RECIPES

    result = scale_recipe_tool("curry", 8)

    assert result["success"] is True
    assert result["scale_factor"] == 2.0


@patch("src.agent.tools.get_all_recipes")
def test_scale_recipe_tool_not_found(mock_get_all):
    mock_get_all.return_value = SAMPLE_RECIPES

    result = scale_recipe_tool("Beef Wellington", 4)

    assert result["success"] is False
    assert "No saved recipe found" in result["error"]


@patch("src.agent.tools.get_all_recipes")
def test_find_recipes_by_ingredients_tool(mock_get_all):
    mock_get_all.return_value = SAMPLE_RECIPES

    result = find_recipes_by_ingredients_tool(["chicken", "curry powder"])

    assert result["success"] is True
    assert result["matches"][0]["recipe_name"] == "Chicken Curry"


def test_convert_measurement_tool_passthrough():
    result = convert_measurement_tool(1, "cup", "tbsp")

    assert result["success"] is True
    assert result["converted_quantity"] == 16.0


def test_find_substitution_tool_passthrough():
    result = find_recipe_substitution_tool("buttermilk")

    assert result["found"] is True