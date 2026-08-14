from pathlib import Path
import sqlite3


# Project root: Cap_Project/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Database location: Cap_Project/data/recipes.db
DB_PATH = PROJECT_ROOT / "data" / "recipes.db"


def get_connection():
    """
    Create and return a connection to the SQLite database.
    """
    return sqlite3.connect(DB_PATH)