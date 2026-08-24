"""
Authentication: password hashing and signup/login logic.

Uses bcrypt for password hashing — includes a per-password salt
automatically and is deliberately slow (resistant to brute-force
attacks), which is why it's used instead of a fast hash like
SHA-256 for passwords specifically.
"""

import re

import bcrypt

from src.database.users import create_user, get_user_by_username


MIN_PASSWORD_LENGTH = 8
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


def hash_password(password: str) -> str:
    """Hash a plaintext password for storage."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored hash."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        # Malformed hash — treat as non-matching rather than crashing.
        return False


def signup(username: str, password: str) -> dict:
    """
    Create a new account.

    Returns:
        dict: {"success": bool, "error": str | None, "user_id": int | None}
    """

    username = username.strip()

    if not USERNAME_PATTERN.match(username):
        return {
            "success": False,
            "error": "Username must be 3-32 characters: letters, numbers, "
            "or underscores only.",
            "user_id": None,
        }

    if len(password) < MIN_PASSWORD_LENGTH:
        return {
            "success": False,
            "error": f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
            "user_id": None,
        }

    if get_user_by_username(username) is not None:
        return {
            "success": False,
            "error": "That username is already taken.",
            "user_id": None,
        }

    password_hash = hash_password(password)
    user_id = create_user(username, password_hash)

    return {"success": True, "error": None, "user_id": user_id}


def login(username: str, password: str) -> dict:
    """
    Verify credentials for an existing account.

    Returns:
        dict: {"success": bool, "error": str | None, "user_id": int | None}
    """

    user = get_user_by_username(username.strip())

    if user is None:
        # Deliberately vague — don't reveal whether the username
        # exists, to avoid helping enumerate valid usernames.
        return {"success": False, "error": "Invalid username or password.", "user_id": None}

    if not verify_password(password, user["password_hash"]):
        return {"success": False, "error": "Invalid username or password.", "user_id": None}

    return {"success": True, "error": None, "user_id": user["id"]}