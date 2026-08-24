"""
Integration tests for the Postgres database layer.

These run against a REAL Postgres database rather than mocks,
since SQL syntax bugs (wrong placeholder style, RETURNING clauses,
type mismatches) won't be caught by mocking psycopg2 calls — the
only way to actually verify the SQL is correct is to run it.

Requires TEST_DATABASE_URL to point at a database you don't mind
being wiped between test runs (each test truncates all tables).
NEVER point this at your production DATABASE_URL.

Setup options:
- A free second database/branch on Supabase or Neon, used only
  for testing.
- A local Postgres instance (e.g. via Docker:
  `docker run -e POSTGRES_PASSWORD=test -p 5432:5432 postgres`).

Run with:
    TEST_DATABASE_URL=postgresql://user:pass@host:port/dbname pytest tests/test_database_integration.py

If TEST_DATABASE_URL isn't set, these tests are skipped rather
than failing, so the rest of the suite still runs fine without a
database available.
"""

import os

import pytest

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="Set TEST_DATABASE_URL to run database integration tests (see file docstring).",
)


@pytest.fixture(autouse=True)
def use_test_database(monkeypatch):
    """
    Point the app at the test database for this test, ensure
    tables exist, and truncate them afterward so every test starts
    from a clean, known state.
    """
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)

    from src.database.recipes import initialize_database
    from src.database.cooking_sessions import initialize_cooking_sessions_table

    initialize_database()
    initialize_cooking_sessions_table()

    yield

    from src.database.connection import get_connection, execute

    conn = get_connection()
    execute(conn, "TRUNCATE recipes, cooking_sessions RESTART IDENTITY CASCADE")
    conn.commit()
    conn.close()


def _make_recipe(**overrides):
    from src.database.recipes import create_recipe

    defaults = dict(
        user_id=1,
        name="Chicken Curry",
        description="A mild curry",
        servings=4,
        prep_time=10,
        cook_time=30,
        ingredients=[{"quantity": 2, "unit": "lb", "name": "chicken"}],
        instructions=["Chop onions.", "Cook chicken.", "Add sauce."],
        tags=["dinner", "curry"],
    )
    defaults.update(overrides)
    return create_recipe(**defaults)


# ---- Recipes CRUD ----

def test_create_and_get_recipe():
    from src.database.recipes import get_recipe

    recipe_id = _make_recipe()
    recipe = get_recipe(recipe_id)

    assert recipe["name"] == "Chicken Curry"
    assert recipe["ingredients"][0]["name"] == "chicken"
    assert recipe["instructions"] == ["Chop onions.", "Cook chicken.", "Add sauce."]


def test_get_recipe_returns_none_for_missing_id():
    from src.database.recipes import get_recipe

    assert get_recipe(999999) is None


def test_get_all_recipes_scoped_to_user():
    from src.database.recipes import get_all_recipes

    _make_recipe(user_id=1, name="User 1 Recipe")
    _make_recipe(user_id=2, name="User 2 Recipe")

    user_1_recipes = get_all_recipes(1)

    assert len(user_1_recipes) == 1
    assert user_1_recipes[0]["name"] == "User 1 Recipe"


def test_update_recipe():
    from src.database.recipes import get_recipe, update_recipe

    recipe_id = _make_recipe()

    update_recipe(
        recipe_id=recipe_id,
        name="Chicken Curry V2",
        description="Updated",
        servings=6,
        prep_time=15,
        cook_time=35,
        ingredients=[{"quantity": 3, "unit": "lb", "name": "chicken"}],
        instructions=["New step."],
        tags=["updated"],
    )

    updated = get_recipe(recipe_id)

    assert updated["name"] == "Chicken Curry V2"
    assert updated["servings"] == 6
    assert updated["ingredients"][0]["quantity"] == 3


def test_delete_recipe():
    from src.database.recipes import get_recipe, delete_recipe

    recipe_id = _make_recipe()

    delete_recipe(recipe_id)

    assert get_recipe(recipe_id) is None


def test_search_by_term_is_case_insensitive():
    from src.database.recipes import search_recipes

    _make_recipe(name="Chicken Curry")

    results = search_recipes(user_id=1, search_term="CHICKEN")

    assert len(results) == 1


def test_search_by_max_cook_time():
    from src.database.recipes import search_recipes

    _make_recipe(name="Quick Meal", cook_time=10)
    _make_recipe(name="Slow Meal", cook_time=60)

    results = search_recipes(user_id=1, max_cook_time=20)

    assert len(results) == 1
    assert results[0]["name"] == "Quick Meal"


def test_search_with_no_filters_returns_all_user_recipes():
    from src.database.recipes import search_recipes

    _make_recipe(name="Recipe A")
    _make_recipe(name="Recipe B")

    results = search_recipes(user_id=1)

    assert len(results) == 2


# ---- Cooking sessions ----

def test_start_and_get_active_session():
    from src.database.cooking_sessions import start_cooking_session, get_active_session

    recipe_id = _make_recipe()

    session = start_cooking_session(user_id=1, recipe_id=recipe_id, servings=4)
    active = get_active_session(1)

    assert active["id"] == session["id"]
    assert active["current_step"] == 0
    assert active["substitutions"] == []


def test_starting_new_session_ends_previous_one():
    from src.database.cooking_sessions import start_cooking_session, get_active_session

    recipe_a = _make_recipe(name="Recipe A")
    recipe_b = _make_recipe(name="Recipe B")

    start_cooking_session(user_id=1, recipe_id=recipe_a, servings=4)
    session_b = start_cooking_session(user_id=1, recipe_id=recipe_b, servings=2)

    active = get_active_session(1)

    assert active["id"] == session_b["id"]
    assert active["recipe_id"] == recipe_b


def test_sessions_scoped_per_user():
    from src.database.cooking_sessions import start_cooking_session, get_active_session

    recipe_a = _make_recipe(name="Recipe A")
    recipe_b = _make_recipe(name="Recipe B")

    start_cooking_session(user_id=1, recipe_id=recipe_a, servings=4)
    start_cooking_session(user_id=2, recipe_id=recipe_b, servings=2)

    assert get_active_session(1)["recipe_id"] == recipe_a
    assert get_active_session(2)["recipe_id"] == recipe_b


def test_update_session_step():
    from src.database.cooking_sessions import (
        start_cooking_session, update_session_step, get_session_by_id,
    )

    recipe_id = _make_recipe()
    session = start_cooking_session(user_id=1, recipe_id=recipe_id, servings=4)

    update_session_step(session["id"], 2)

    assert get_session_by_id(session["id"])["current_step"] == 2


def test_add_session_substitution_appends():
    from src.database.cooking_sessions import (
        start_cooking_session, add_session_substitution, get_session_by_id,
    )

    recipe_id = _make_recipe()
    session = start_cooking_session(user_id=1, recipe_id=recipe_id, servings=4)

    add_session_substitution(session["id"], "used oat milk")
    add_session_substitution(session["id"], "used tamari instead of soy sauce")

    updated = get_session_by_id(session["id"])

    assert updated["substitutions"] == [
        "used oat milk",
        "used tamari instead of soy sauce",
    ]


def test_end_cooking_session():
    from src.database.cooking_sessions import (
        start_cooking_session, end_cooking_session, get_active_session, get_session_by_id,
    )

    recipe_id = _make_recipe()
    session = start_cooking_session(user_id=1, recipe_id=recipe_id, servings=4)

    end_cooking_session(session["id"])

    assert get_active_session(1) is None
    assert get_session_by_id(session["id"])["is_active"] is False