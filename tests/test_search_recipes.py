from unittest.mock import patch

from src.tools.search_recipes import search_recipes


SAMPLE_DB_RESULTS = [
    {
        "id": 1,
        "user_id": 1,
        "name": "Chicken Curry",
        "description": "A mild curry",
        "servings": 4,
        "prep_time": 10,
        "cook_time": 30,
        "ingredients": [],
        "instructions": [],
        "tags": [],
        "created_at": "2026-01-01",
    }
]


@patch("src.tools.search_recipes._db_search_recipes")
def test_returns_results_from_db_layer(mock_db_search):
    mock_db_search.return_value = SAMPLE_DB_RESULTS

    result = search_recipes(user_id=1, search_term="curry")

    assert result["success"] is True
    assert result["count"] == 1
    assert result["recipes"][0]["name"] == "Chicken Curry"


@patch("src.tools.search_recipes._db_search_recipes")
def test_passes_cleaned_args_to_db_layer(mock_db_search):
    mock_db_search.return_value = []

    search_recipes(user_id=5, search_term="  curry  ", max_cook_time=20)

    mock_db_search.assert_called_once_with(
        user_id=5, search_term="curry", max_cook_time=20
    )


@patch("src.tools.search_recipes._db_search_recipes")
def test_empty_search_term_becomes_none(mock_db_search):
    mock_db_search.return_value = []

    search_recipes(user_id=1, search_term="   ")

    mock_db_search.assert_called_once_with(
        user_id=1, search_term=None, max_cook_time=None
    )


@patch("src.tools.search_recipes._db_search_recipes")
def test_no_results_returns_empty_list_not_error(mock_db_search):
    mock_db_search.return_value = []

    result = search_recipes(user_id=1, search_term="nonexistent")

    assert result["success"] is True
    assert result["count"] == 0
    assert result["recipes"] == []


@patch("src.tools.search_recipes._db_search_recipes")
def test_db_exception_returns_structured_error(mock_db_search):
    mock_db_search.side_effect = Exception("db is locked")

    result = search_recipes(user_id=1, search_term="curry")

    assert result["success"] is False
    assert "db is locked" in result["error"]


def test_rejects_non_integer_user_id():
    result = search_recipes(user_id="1", search_term="curry")

    assert result["success"] is False


def test_rejects_bool_as_user_id():
    result = search_recipes(user_id=True, search_term="curry")

    assert result["success"] is False


def test_rejects_negative_max_cook_time():
    result = search_recipes(user_id=1, max_cook_time=-5)

    assert result["success"] is False


def test_rejects_non_integer_max_cook_time():
    result = search_recipes(user_id=1, max_cook_time="20")

    assert result["success"] is False


def test_rejects_non_string_search_term():
    result = search_recipes(user_id=1, search_term=123)

    assert result["success"] is False