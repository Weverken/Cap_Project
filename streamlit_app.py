import streamlit as st

from src.database.recipes import initialize_database
from src.database.cooking_sessions import initialize_cooking_sessions_table
from src.database.users import initialize_users_table
from src.agent.context import set_current_user_id


# Database setup
# (CREATE TABLE IF NOT EXISTS — safe to call on every startup,
# and necessary since a fresh database has no tables yet.)

initialize_database()
initialize_cooking_sessions_table()
initialize_users_table()


# Page configuration

st.set_page_config(
    page_title="CookMate",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Auth gate
# Only the login/signup page is reachable until a user has
# authenticated. This runs on every script rerun (Streamlit reuses
# the same thread across reruns within a session), so the
# thread-local "current user" context is always kept fresh here
# rather than assumed to persist from an earlier rerun.

login_page = st.Page(
    "pages/login.py",
    title="Log In",
    icon="🔑",
)

if "user_id" not in st.session_state:

    pg = st.navigation([login_page])
    pg.run()

else:

    set_current_user_id(st.session_state["user_id"])

    with st.sidebar:
        st.caption(f"Signed in as **{st.session_state.get('username', 'user')}**")
        if st.button("Log Out"):
            for key in ("user_id", "username", "agent", "messages"):
                st.session_state.pop(key, None)
            st.rerun()

    cooking_assistant = st.Page(
        "pages/cooking_assistant.py",
        title="Cooking Assistant",
        icon="👨‍🍳",
    )

    my_recipes = st.Page(
        "pages/my_recipes.py",
        title="My Recipes",
        icon="📚",
    )

    import_recipe = st.Page(
        "pages/import_recipe.py",
        title="Import Recipe",
        icon="📥",
    )

    pg = st.navigation(
        [
            cooking_assistant,
            my_recipes,
            import_recipe,
        ]
    )

    pg.run()