import os

import psycopg2
from dotenv import load_dotenv


def get_connection():
    """Open a connection to Postgres. Needs DATABASE_URL set (see .env.example)."""

    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL not found in environment variables. "
            "Set it to your Postgres connection string (see .env.example)."
        )

    return psycopg2.connect(database_url)


def execute(conn, query, params=None):
    """Run a query, return the cursor. psycopg2 doesn't have SQLite's
    conn.execute() shortcut, so this just fakes it."""

    cursor = conn.cursor()
    cursor.execute(query, params or ())
    return cursor