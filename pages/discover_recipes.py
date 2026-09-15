import streamlit as st

from src.database.recipes import get_all_recipes
from src.discovery.recipe_finder import suggest_recipes_online


st.title("🔎 Discover Recipes")

st.write(
    "Describe what you're in the mood for, and I'll search the web "
    "for real recipes that match — skipping anything you've already "
    "saved."
)

query = st.text_input(
    "What are you looking for?",
    placeholder="e.g. easy recipes with pasta and chicken",
)

if st.button("🔎 Find Recipes", type="primary"):

    if not query.strip():
        st.warning("Tell me what kind of recipe you're looking for first.")
    else:
        saved_recipes = get_all_recipes(st.session_state["user_id"])
        saved_names = [r["name"] for r in saved_recipes]

        with st.spinner("Searching the web..."):
            result = suggest_recipes_online(query, excluded_names=saved_names)

        if not result["success"]:
            st.error(result["error"])
        else:
            st.divider()

            st.markdown(result["response_text"])

            if result["sources"]:
                st.divider()
                st.caption("Sources")

                for source in result["sources"]:
                    label = source["title"] or source["domain"] or source["url"]
                    st.markdown(f"- [{label}]({source['url']})")