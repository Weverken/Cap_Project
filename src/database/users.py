from src.database.connection import get_connection, execute


def initialize_users_table():
    """
    Create the users table if it does not already exist.
    """

    conn = get_connection()

    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )

    conn.commit()
    conn.close()


def create_user(username: str, password_hash: str) -> int:
    """
    Create a new user and return their id.

    password_hash must already be hashed (see src.auth) — this
    layer never sees or stores a plaintext password.
    """

    conn = get_connection()

    cursor = execute(
        conn,
        """
        INSERT INTO users (username, password_hash)
        VALUES (%s, %s)
        RETURNING id
        """,
        (username, password_hash),
    )

    user_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return user_id


def get_user_by_username(username: str) -> dict | None:
    """Look up a user by username (case-sensitive, exact match)."""

    conn = get_connection()

    cursor = execute(
        conn,
        """
        SELECT id, username, password_hash, created_at
        FROM users
        WHERE username = %s
        """,
        (username,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "created_at": row[3],
    }


def get_user_by_id(user_id: int) -> dict | None:
    """Look up a user by id."""

    conn = get_connection()

    cursor = execute(
        conn,
        """
        SELECT id, username, password_hash, created_at
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "created_at": row[3],
    }