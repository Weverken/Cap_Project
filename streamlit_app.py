import streamlit as st

from src.database.recipes import initialize_database
from src.database.cooking_sessions import initialize_cooking_sessions_table


# Database setup
# (CREATE TABLE IF NOT EXISTS — safe to call on every startup,
# and necessary since a fresh clone has no data/recipes.db yet.)

initialize_database()
initialize_cooking_sessions_table()


# Page configuration

st.set_page_config(
    page_title="CookMate",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Pages

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


# Navigation

pg = st.navigation(
    [
        cooking_assistant,
        my_recipes,
        import_recipe,
    ]
)

pg.run()