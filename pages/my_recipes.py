import streamlit as st


st.title("📚 My Recipes")

st.write(
    "Your personal recipe collection."
)

st.divider()

# Temporary example recipes
recipes = [
    {
        "name": "Chicken Curry",
        "time": "45 min",
        "servings": 4,
    },
    {
        "name": "Chicken Teriyaki Bowl",
        "time": "30 min",
        "servings": 2,
    },
    {
        "name": "Lemon Garlic Salmon",
        "time": "25 min",
        "servings": 2,
    },
]


# Search
search = st.text_input(
    "🔍 Search recipes",
    placeholder="Search by recipe name...",
)

filtered_recipes = [
    recipe
    for recipe in recipes
    if search.lower() in recipe["name"].lower()
]


# Recipe cards
if not filtered_recipes:
    st.warning("No recipes found.")

else:
    cols = st.columns(3)

    for i, recipe in enumerate(filtered_recipes):
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(recipe["name"])

                st.write(f"⏱️ {recipe['time']}")
                st.write(f"🍽️ {recipe['servings']} servings")

                if st.button(
                    "View Recipe",
                    key=f"view_{recipe['name']}",
                    use_container_width=True,
                ):
                    st.session_state["selected_recipe"] = recipe
                    st.info(
                        f"Recipe selected: {recipe['name']}"
                    )