from unittest.mock import patch

from src.agent.tools import (
    get_current_cooking_session_tool,
    advance_cooking_step_tool,
    log_cooking_substitution_tool,
)


SAMPLE_RECIPE = {
    "id": 5,
    "name": "Chicken Curry",
    "servings": 4,
    "instructions": ["Chop onions.", "Cook chicken.", "Add sauce.", "Simmer."],
}

SAMPLE_SESSION = {
    "id": 1,
    "user_id": 1,
    "recipe_id": 5,
    "servings": 4,
    "current_step": 1,
    "substitutions": ["used oat milk instead of dairy"],
    "is_active": True,
}


@patch("src.agent.tools.get_recipe")
@patch("src.agent.tools.get_active_session")
def test_get_current_session_tool_with_active_session(mock_get_session, mock_get_recipe):
    mock_get_session.return_value = SAMPLE_SESSION
    mock_get_recipe.return_value = SAMPLE_RECIPE

    result = get_current_cooking_session_tool()

    assert result["has_active_session"] is True
    assert result["recipe_name"] == "Chicken Curry"
    assert result["current_step_number"] == 2
    assert result["total_steps"] == 4
    assert result["current_step_instruction"] == "Cook chicken."
    assert result["substitutions_logged_this_session"] == ["used oat milk instead of dairy"]


@patch("src.agent.tools.get_active_session")
def test_get_current_session_tool_no_active_session(mock_get_session):
    mock_get_session.return_value = None

    result = get_current_cooking_session_tool()

    assert result["has_active_session"] is False


@patch("src.agent.tools.get_recipe")
@patch("src.agent.tools.get_active_session")
def test_get_current_session_tool_deleted_recipe(mock_get_session, mock_get_recipe):
    mock_get_session.return_value = SAMPLE_SESSION
    mock_get_recipe.return_value = None

    result = get_current_cooking_session_tool()

    assert result["success"] is False
    assert result["has_active_session"] is False


@patch("src.agent.tools.update_session_step")
@patch("src.agent.tools.get_recipe")
@patch("src.agent.tools.get_active_session")
def test_advance_step_next(mock_get_session, mock_get_recipe, mock_update_step):
    mock_get_session.return_value = SAMPLE_SESSION
    mock_get_recipe.return_value = SAMPLE_RECIPE

    result = advance_cooking_step_tool("next")

    assert result["success"] is True
    assert result["current_step_number"] == 3
    mock_update_step.assert_called_once_with(1, 2)


@patch("src.agent.tools.update_session_step")
@patch("src.agent.tools.get_recipe")
@patch("src.agent.tools.get_active_session")
def test_advance_step_previous(mock_get_session, mock_get_recipe, mock_update_step):
    mock_get_session.return_value = SAMPLE_SESSION
    mock_get_recipe.return_value = SAMPLE_RECIPE

    result = advance_cooking_step_tool("previous")

    assert result["current_step_number"] == 1
    mock_update_step.assert_called_once_with(1, 0)


@patch("src.agent.tools.update_session_step")
@patch("src.agent.tools.get_recipe")
@patch("src.agent.tools.get_active_session")
def test_advance_step_clamps_at_last_step(mock_get_session, mock_get_recipe, mock_update_step):
    last_step_session = {**SAMPLE_SESSION, "current_step": 3}
    mock_get_session.return_value = last_step_session
    mock_get_recipe.return_value = SAMPLE_RECIPE

    result = advance_cooking_step_tool("next")

    assert result["current_step_number"] == 4  # unchanged, already last
    mock_update_step.assert_called_once_with(1, 3)


def test_advance_step_rejects_invalid_direction():
    result = advance_cooking_step_tool("sideways")

    assert result["success"] is False


@patch("src.agent.tools.get_active_session")
def test_advance_step_no_active_session(mock_get_session):
    mock_get_session.return_value = None

    result = advance_cooking_step_tool("next")

    assert result["success"] is False


@patch("src.agent.tools.add_session_substitution")
@patch("src.agent.tools.get_active_session")
def test_log_substitution_success(mock_get_session, mock_add_sub):
    mock_get_session.return_value = SAMPLE_SESSION

    result = log_cooking_substitution_tool("used almond milk instead of regular milk")

    assert result["success"] is True
    mock_add_sub.assert_called_once_with(1, "used almond milk instead of regular milk")


@patch("src.agent.tools.get_active_session")
def test_log_substitution_no_active_session(mock_get_session):
    mock_get_session.return_value = None

    result = log_cooking_substitution_tool("used almond milk")

    assert result["success"] is False


@patch("src.agent.tools.get_active_session")
def test_log_substitution_rejects_empty_note(mock_get_session):
    mock_get_session.return_value = SAMPLE_SESSION

    result = log_cooking_substitution_tool("   ")

    assert result["success"] is False