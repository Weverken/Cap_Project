import json

from src.database.connection import get_connection, execute


def initialize_cooking_sessions_table():
    """
    Create the cooking_sessions table if it does not already exist.

    Design note: only one session is "active" per user at a time.
    Rather than enforcing that with a unique constraint (which
    would complicate switching recipes mid-cook), it's enforced at
    the application layer in start_cooking_session(), which ends
    any existing active session before starting a new one.
    """

    conn = get_connection()

    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS cooking_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            recipe_id INTEGER NOT NULL,
            servings INTEGER NOT NULL,
            current_step INTEGER NOT NULL DEFAULT 0,
            substitutions TEXT NOT NULL DEFAULT '[]',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )

    conn.commit()
    conn.close()


def start_cooking_session(user_id: int, recipe_id: int, servings: int) -> dict:
    """
    Start a new cooking session for a recipe, ending any other
    active session for this user first (only one recipe can be
    "currently cooking" at a time).

    Returns the newly created session as a dict.
    """

    conn = get_connection()

    # End any existing active session for this user.
    execute(
        conn,
        "UPDATE cooking_sessions SET is_active = FALSE WHERE user_id = %s AND is_active = TRUE",
        (user_id,),
    )

    cursor = execute(
        conn,
        """
        INSERT INTO cooking_sessions
            (user_id, recipe_id, servings, current_step, substitutions, is_active)
        VALUES (%s, %s, %s, 0, '[]', TRUE)
        RETURNING id
        """,
        (user_id, recipe_id, servings),
    )

    session_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return get_session_by_id(session_id)


def get_active_session(user_id: int) -> dict | None:
    """
    Get the user's currently active cooking session, if any.
    Returns None if nothing is being actively cooked right now.
    """

    conn = get_connection()

    cursor = execute(
        conn,
        """
        SELECT id, user_id, recipe_id, servings, current_step,
               substitutions, is_active, started_at, updated_at
        FROM cooking_sessions
        WHERE user_id = %s AND is_active = TRUE
        ORDER BY started_at DESC
        LIMIT 1
        """,
        (user_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return _row_to_dict(row)


def get_session_by_id(session_id: int) -> dict | None:
    """Get a cooking session by its id, regardless of active status."""

    conn = get_connection()

    cursor = execute(
        conn,
        """
        SELECT id, user_id, recipe_id, servings, current_step,
               substitutions, is_active, started_at, updated_at
        FROM cooking_sessions
        WHERE id = %s
        """,
        (session_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return _row_to_dict(row)


def update_session_step(session_id: int, current_step: int) -> None:
    """Move the session to a specific step index (0-based)."""

    conn = get_connection()

    execute(
        conn,
        """
        UPDATE cooking_sessions
        SET current_step = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (current_step, session_id),
    )

    conn.commit()
    conn.close()


def add_session_substitution(session_id: int, note: str) -> None:
    """
    Append a substitution/change note to a session's log (e.g.
    "used applesauce instead of egg"), so the agent can reference
    it later in the same cooking session.
    """

    session = get_session_by_id(session_id)

    if session is None:
        return

    substitutions = session["substitutions"]
    substitutions.append(note)

    conn = get_connection()

    execute(
        conn,
        """
        UPDATE cooking_sessions
        SET substitutions = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (json.dumps(substitutions), session_id),
    )

    conn.commit()
    conn.close()


def end_cooking_session(session_id: int) -> None:
    """Mark a cooking session as no longer active."""

    conn = get_connection()

    execute(
        conn,
        "UPDATE cooking_sessions SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (session_id,),
    )

    conn.commit()
    conn.close()


def _row_to_dict(row) -> dict:
    """Convert a raw Postgres row into a dict, deserializing JSON fields."""

    return {
        "id": row[0],
        "user_id": row[1],
        "recipe_id": row[2],
        "servings": row[3],
        "current_step": row[4],
        "substitutions": json.loads(row[5]),
        "is_active": bool(row[6]),
        "started_at": row[7],
        "updated_at": row[8],
    }