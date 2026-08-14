import streamlit as st


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
