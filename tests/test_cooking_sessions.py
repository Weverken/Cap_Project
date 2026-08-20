import importlib

import pytest

import src.database.connection as connection


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """
    Point get_connection() at a throwaway SQLite file for the
    duration of the test, then reload the cooking_sessions module
    so it picks up a fresh table.
    """
    db_path = tmp_path / "test_recipes.db"
    monkeypatch.setattr(connection, "DB_PATH", db_path)

    import src.database.cooking_sessions as cooking_sessions
    importlib.reload(cooking_sessions)

    cooking_sessions.initialize_cooking_sessions_table()

    yield cooking_sessions


def test_start_cooking_session_creates_session(temp_db):
    session = temp_db.start_cooking_session(user_id=1, recipe_id=5, servings=4)

    assert session["user_id"] == 1
    assert session["recipe_id"] == 5
    assert session["servings"] == 4
    assert session["current_step"] == 0
    assert session["substitutions"] == []
    assert session["is_active"] is True


def test_get_active_session_returns_none_when_nothing_cooking(temp_db):
    result = temp_db.get_active_session(user_id=1)

    assert result is None


def test_get_active_session_returns_current_session(temp_db):
    started = temp_db.start_cooking_session(user_id=1, recipe_id=5, servings=4)

    active = temp_db.get_active_session(user_id=1)

    assert active["id"] == started["id"]


def test_starting_new_session_ends_previous_one(temp_db):
    first = temp_db.start_cooking_session(user_id=1, recipe_id=5, servings=4)
    second = temp_db.start_cooking_session(user_id=1, recipe_id=9, servings=2)

    active = temp_db.get_active_session(user_id=1)

    assert active["id"] == second["id"]
    assert active["recipe_id"] == 9

    first_after = temp_db.get_session_by_id(first["id"])
    assert first_after["is_active"] is False


def test_sessions_scoped_per_user(temp_db):
    temp_db.start_cooking_session(user_id=1, recipe_id=5, servings=4)
    temp_db.start_cooking_session(user_id=2, recipe_id=9, servings=2)

    user_1_active = temp_db.get_active_session(user_id=1)
    user_2_active = temp_db.get_active_session(user_id=2)

    assert user_1_active["recipe_id"] == 5
    assert user_2_active["recipe_id"] == 9


def test_update_session_step(temp_db):
    session = temp_db.start_cooking_session(user_id=1, recipe_id=5, servings=4)

    temp_db.update_session_step(session["id"], current_step=3)

    updated = temp_db.get_session_by_id(session["id"])
    assert updated["current_step"] == 3


def test_add_session_substitution_appends(temp_db):
    session = temp_db.start_cooking_session(user_id=1, recipe_id=5, servings=4)

    temp_db.add_session_substitution(session["id"], "used applesauce instead of egg")
    temp_db.add_session_substitution(session["id"], "used oat milk instead of buttermilk")

    updated = temp_db.get_session_by_id(session["id"])
    assert updated["substitutions"] == [
        "used applesauce instead of egg",
        "used oat milk instead of buttermilk",
    ]


def test_end_cooking_session(temp_db):
    session = temp_db.start_cooking_session(user_id=1, recipe_id=5, servings=4)

    temp_db.end_cooking_session(session["id"])

    assert temp_db.get_active_session(user_id=1) is None
    ended = temp_db.get_session_by_id(session["id"])
    assert ended["is_active"] is False


def test_get_session_by_id_returns_none_for_missing_id(temp_db):
    result = temp_db.get_session_by_id(9999)

    assert result is None