import streamlit as st

from src.database.recipes import initialize_database
from src.database.cooking_sessions import initialize_cooking_sessions_table
from src.database.users import initialize_users_table
from src.agent.context import set_current_user_id


# Sets up tables if they don't exist yet - safe to run on every startup.
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


# Extra button styling - theme.toml only does flat colors, this adds
# the hover/press feel so it doesn't look like a generic dashboard.

st.markdown(
    """
    <style>
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-secondary"] {
        border-radius: 10px;
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }

    /* Primary: filled sienna, warm shadow, lifts on hover */
    [data-testid="stBaseButton-primary"] {
        border: none;
        box-shadow: 0 2px 6px rgba(92, 58, 33, 0.35);
    }
    [data-testid="stBaseButton-primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(92, 58, 33, 0.45);
    }
    [data-testid="stBaseButton-primary"]:active {
        transform: translateY(0px);
        box-shadow: 0 1px 3px rgba(92, 58, 33, 0.35);
    }

    /* Secondary: outlined, warm on hover, same press feel */
    [data-testid="stBaseButton-secondary"] {
        border: 1.5px solid #A0522D;
        box-shadow: 0 1px 3px rgba(92, 58, 33, 0.15);
    }
    [data-testid="stBaseButton-secondary"]:hover {
        border-color: #8B4513;
        background-color: rgba(160, 82, 45, 0.08);
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(92, 58, 33, 0.25);
    }
    [data-testid="stBaseButton-secondary"]:active {
        transform: translateY(0px);
        box-shadow: 0 1px 2px rgba(92, 58, 33, 0.2);
    }
    /* Sidebar navigation links */
    [data-testid="stPageLink-NavLink"] {
        border-radius: 8px;
        padding-left: 12px !important;
        box-shadow: inset 0 0 0 0 #E9C9A0;
        transition: box-shadow 0.15s ease, background-color 0.15s ease,
                    padding-left 0.15s ease;
    }
    [data-testid="stPageLink-NavLink"]:hover {
        background-color: rgba(233, 201, 160, 0.12);
        box-shadow: inset 3px 0 0 0 #E9C9A0;
        padding-left: 16px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Auth gate - only login/signup is reachable until you're signed in.
# Runs on every rerun since Streamlit reuses the same thread, so we
# can't just assume the user context from a previous rerun still holds.

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

    discover_recipes = st.Page(
        "pages/discover_recipes.py",
        title="Discover Recipes",
        icon="🔎",
    )

    pg = st.navigation(
        [
            cooking_assistant,
            my_recipes,
            import_recipe,
            discover_recipes,
        ]
    )

    pg.run()