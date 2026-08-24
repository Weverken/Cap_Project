import os

import psycopg2
from dotenv import load_dotenv


def get_connection():
    """
    Create and return a connection to the Postgres database.

    Requires DATABASE_URL to be set (e.g. a Supabase/Neon
    connection string) — see .env.example.
    """

    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL not found in environment variables. "
            "Set it to your Postgres connection string (see .env.example)."
        )

    return psycopg2.connect(database_url)


def execute(conn, query, params=None):
    """
    Run a query on a connection and return the cursor.

    Small helper so calling code can keep the same
    `cursor = execute(conn, "...", (...))` shape it used with
    SQLite's conn.execute() shortcut, which psycopg2 doesn't have
    (psycopg2 requires an explicit cursor object).
    """

    cursor = conn.cursor()
    cursor.execute(query, params or ())
    return cursor