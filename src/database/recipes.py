import json

from src.database.connection import get_connection


def initialize_database():
    """
    Create the recipes table if it does not already exist.
    """

    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            servings INTEGER,
            prep_time INTEGER,
            cook_time INTEGER,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


def create_recipe(
    user_id,
    name,
    description,
    servings,
    prep_time,
    cook_time,
    ingredients,
    instructions,
    tags,
):
    """
    Create a new recipe in the database.

    ingredients, instructions and tags are Python lists
    and will be stored as JSON in SQLite.
    """

    conn = get_connection()

    ingredients_json = json.dumps(ingredients)
    instructions_json = json.dumps(instructions)
    tags_json = json.dumps(tags)

    cursor = conn.execute(
        """
        INSERT INTO recipes (
            user_id,
            name,
            description,
            servings,
            prep_time,
            cook_time,
            ingredients,
            instructions,
            tags
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            name,
            description,
            servings,
            prep_time,
            cook_time,
            ingredients_json,
            instructions_json,
            tags_json,
        ),
    )

    recipe_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return recipe_id


def get_recipe(recipe_id):
    """
    Retrieve a single recipe by its ID.
    """

    conn = get_connection()

    cursor = conn.execute(
        """
        SELECT *
        FROM recipes
        WHERE id = ?
        """,
        (recipe_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "description": row[3],
        "servings": row[4],
        "prep_time": row[5],
        "cook_time": row[6],
        "ingredients": json.loads(row[7]),
        "instructions": json.loads(row[8]),
        "tags": json.loads(row[9]),
        "created_at": row[10],
    }


def get_all_recipes(user_id):
    """
    Retrieve all recipes belonging to a user.
    """

    conn = get_connection()

    cursor = conn.execute(
        """
        SELECT *
        FROM recipes
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    )

    rows = cursor.fetchall()

    conn.close()

    recipes = []

    for row in rows:
        recipes.append(
            {
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "description": row[3],
                "servings": row[4],
                "prep_time": row[5],
                "cook_time": row[6],
                "ingredients": json.loads(row[7]),
                "instructions": json.loads(row[8]),
                "tags": json.loads(row[9]),
                "created_at": row[10],
            }
        )

    return recipes


def update_recipe(
    recipe_id,
    name,
    description,
    servings,
    prep_time,
    cook_time,
    ingredients,
    instructions,
    tags,
):
    """
    Update an existing recipe.
    """

    conn = get_connection()

    ingredients_json = json.dumps(ingredients)
    instructions_json = json.dumps(instructions)
    tags_json = json.dumps(tags)

    conn.execute(
        """
        UPDATE recipes
        SET
            name = ?,
            description = ?,
            servings = ?,
            prep_time = ?,
            cook_time = ?,
            ingredients = ?,
            instructions = ?,
            tags = ?
        WHERE id = ?
        """,
        (
            name,
            description,
            servings,
            prep_time,
            cook_time,
            ingredients_json,
            instructions_json,
            tags_json,
            recipe_id,
        ),
    )

    conn.commit()
    conn.close()


def delete_recipe(recipe_id):
    """
    Delete a recipe by its ID.
    """

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM recipes
        WHERE id = ?
        """,
        (recipe_id,),
    )

    conn.commit()
    conn.close()


def search_recipes(
    user_id,
    search_term=None,
    max_cook_time=None,
):
    """
    Search a user's recipes by name or description.

    Optionally filter recipes by maximum cooking time.
    """

    conn = get_connection()

    query = """
        SELECT *
        FROM recipes
        WHERE user_id = ?
    """

    params = [user_id]

    if search_term:
        query += """
            AND (
                name LIKE ?
                OR description LIKE ?
            )
        """

        search_pattern = f"%{search_term}%"

        params.extend([
            search_pattern,
            search_pattern,
        ])

    if max_cook_time is not None:
        query += """
            AND cook_time <= ?
        """

        params.append(max_cook_time)

    query += """
        ORDER BY created_at DESC
    """

    cursor = conn.execute(query, params)

    rows = cursor.fetchall()

    conn.close()

    recipes = []

    for row in rows:
        recipes.append(
            {
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "description": row[3],
                "servings": row[4],
                "prep_time": row[5],
                "cook_time": row[6],
                "ingredients": json.loads(row[7]),
                "instructions": json.loads(row[8]),
                "tags": json.loads(row[9]),
                "created_at": row[10],
            }
        )

    return recipes