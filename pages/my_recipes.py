import streamlit as st

from src.database.recipes import (
    get_all_recipes,
    get_recipe,
    create_recipe,
    update_recipe,
    delete_recipe,
)
from src.database.cooking_sessions import start_cooking_session


st.title("📚 My Recipes")

# Temporary user ID
# Later this will come from the logged-in user
user_id = 1


# ==================================================
# ADD RECIPE
# ==================================================

if "adding_recipe" in st.session_state:

    st.header("➕ Add Recipe")

    # ------------------------------------------
    # Recipe information
    # ------------------------------------------

    name = st.text_input(
        "Recipe Name",
        placeholder="e.g. Chicken Curry",
    )

    description = st.text_area(
        "Description",
        placeholder="A short description of the recipe...",
    )

    # ------------------------------------------
    # Time and servings
    # ------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        servings = st.number_input(
            "Servings",
            min_value=1,
            value=2,
            step=1,
        )

    with col2:
        prep_time = st.number_input(
            "Prep Time (minutes)",
            min_value=0,
            value=10,
            step=1,
        )

    with col3:
        cook_time = st.number_input(
            "Cook Time (minutes)",
            min_value=0,
            value=20,
            step=1,
        )

    st.divider()

    # ------------------------------------------
    # Ingredients
    # ------------------------------------------

    st.subheader("🥕 Ingredients")

    st.write("Add the ingredients for your recipe.")

    # Number of ingredient rows
    if "add_ingredient_count" not in st.session_state:
        st.session_state["add_ingredient_count"] = 1

    ingredients = []

    for i in range(
        st.session_state["add_ingredient_count"]
    ):

        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=1.0,
                key=f"add_quantity_{i}",
            )

        with col2:
            unit = st.text_input(
                "Unit",
                key=f"add_unit_{i}",
                placeholder="g, tbsp, etc.",
            )

        with col3:
            ingredient_name = st.text_input(
                "Ingredient",
                key=f"add_ingredient_{i}",
                placeholder="Ingredient name",
            )

        ingredients.append(
            {
                "quantity": quantity,
                "unit": unit,
                "name": ingredient_name,
            }
        )

    if st.button("➕ Add Ingredient"):

        st.session_state["add_ingredient_count"] += 1

        st.rerun()

    st.divider()

    # ------------------------------------------
    # Instructions
    # ------------------------------------------

    st.subheader("👨‍🍳 Instructions")

    if "add_instruction_count" not in st.session_state:
        st.session_state["add_instruction_count"] = 1

    instructions = []

    for i in range(
        st.session_state["add_instruction_count"]
    ):

        instruction = st.text_area(
            f"Step {i + 1}",
            key=f"add_instruction_{i}",
            placeholder=f"Describe step {i + 1}...",
        )

        instructions.append(instruction)

    if st.button("➕ Add Step"):

        st.session_state["add_instruction_count"] += 1

        st.rerun()

    st.divider()

    # ------------------------------------------
    # Tags
    # ------------------------------------------

    st.subheader("🏷️ Tags")

    tags_text = st.text_input(
        "Tags",
        placeholder="chicken, quick, dinner",
        help="Separate tags with commas.",
    )

    tags = [
        tag.strip()
        for tag in tags_text.split(",")
        if tag.strip()
    ]

    st.divider()

    # ------------------------------------------
    # Save / Cancel
    # ------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "💾 Save Recipe",
            type="primary",
            use_container_width=True,
        ):

            # Validate recipe name
            if not name.strip():

                st.error(
                    "Please enter a recipe name."
                )

            # Validate ingredients
            elif not any(
                ingredient["name"].strip()
                for ingredient in ingredients
            ):

                st.error(
                    "Please add at least one ingredient."
                )

            # Validate instructions
            elif not any(
                instruction.strip()
                for instruction in instructions
            ):

                st.error(
                    "Please add at least one instruction."
                )

            else:

                # Remove empty ingredients
                ingredients = [
                    ingredient
                    for ingredient in ingredients
                    if ingredient["name"].strip()
                ]

                # Remove empty instructions
                instructions = [
                    instruction.strip()
                    for instruction in instructions
                    if instruction.strip()
                ]

                # Create recipe in database
                recipe_id = create_recipe(
                    user_id=user_id,
                    name=name.strip(),
                    description=description.strip(),
                    servings=servings,
                    prep_time=prep_time,
                    cook_time=cook_time,
                    ingredients=ingredients,
                    instructions=instructions,
                    tags=tags,
                )

                # Clear add mode
                del st.session_state["adding_recipe"]

                # Reset counters
                st.session_state["add_ingredient_count"] = 1
                st.session_state["add_instruction_count"] = 1

                # Open newly created recipe
                st.session_state["selected_recipe_id"] = recipe_id

                st.rerun()

    with col2:

        if st.button(
            "Cancel",
            use_container_width=True,
        ):

            del st.session_state["adding_recipe"]

            # Reset counters
            st.session_state["add_ingredient_count"] = 1
            st.session_state["add_instruction_count"] = 1

            st.rerun()


# ==================================================
# EDIT RECIPE
# ==================================================

elif "editing_recipe_id" in st.session_state:

    recipe_id = st.session_state["editing_recipe_id"]

    recipe = get_recipe(recipe_id)

    if recipe is None:

        st.error("Recipe not found.")

        if st.button("← Back to My Recipes"):

            del st.session_state["editing_recipe_id"]

            st.rerun()

    else:

        st.header("✏️ Edit Recipe")

        # ------------------------------------------
        # Recipe information
        # ------------------------------------------

        name = st.text_input(
            "Recipe Name",
            value=recipe["name"],
        )

        description = st.text_area(
            "Description",
            value=recipe["description"] or "",
        )

        # ------------------------------------------
        # Time and servings
        # ------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            servings = st.number_input(
                "Servings",
                min_value=1,
                value=recipe["servings"],
                step=1,
            )

        with col2:
            prep_time = st.number_input(
                "Prep Time (minutes)",
                min_value=0,
                value=recipe["prep_time"],
                step=1,
            )

        with col3:
            cook_time = st.number_input(
                "Cook Time (minutes)",
                min_value=0,
                value=recipe["cook_time"],
                step=1,
            )

        st.divider()

        # ------------------------------------------
        # Ingredients
        # ------------------------------------------

        st.subheader("🥕 Ingredients")

        edited_ingredients = []

        for i, ingredient in enumerate(
            recipe["ingredients"]
        ):

            col1, col2, col3, col4 = st.columns(
                [1, 1, 3, 0.5]
            )

            with col1:
                quantity = st.number_input(
                    "Quantity",
                    min_value=0.0,
                    value=float(ingredient["quantity"]),
                    key=f"quantity_{i}",
                )

            with col2:
                unit = st.text_input(
                    "Unit",
                    value=ingredient["unit"],
                    key=f"unit_{i}",
                )

            with col3:
                ingredient_name = st.text_input(
                    "Ingredient",
                    value=ingredient["name"],
                    key=f"ingredient_{i}",
                )

            with col4:
                st.write("")
                st.write("")

                remove = st.checkbox(
                    "Remove",
                    key=f"remove_{i}",
                )

            if not remove:

                edited_ingredients.append(
                    {
                        "quantity": quantity,
                        "unit": unit,
                        "name": ingredient_name,
                    }
                )

        # ------------------------------------------
        # Add ingredient
        # ------------------------------------------

        if "new_ingredient_count" not in st.session_state:
            st.session_state["new_ingredient_count"] = 0

        if st.button("➕ Add Ingredient"):

            st.session_state["new_ingredient_count"] += 1

            st.rerun()

        for i in range(
            st.session_state["new_ingredient_count"]
        ):

            col1, col2, col3 = st.columns([1, 1, 3])

            with col1:
                quantity = st.number_input(
                    "Quantity",
                    min_value=0.0,
                    value=1.0,
                    key=f"new_quantity_{i}",
                )

            with col2:
                unit = st.text_input(
                    "Unit",
                    key=f"new_unit_{i}",
                    placeholder="g, tbsp, etc.",
                )

            with col3:
                ingredient_name = st.text_input(
                    "Ingredient",
                    key=f"new_ingredient_{i}",
                    placeholder="Ingredient name",
                )

            if ingredient_name:

                edited_ingredients.append(
                    {
                        "quantity": quantity,
                        "unit": unit,
                        "name": ingredient_name,
                    }
                )

        st.divider()

        # ------------------------------------------
        # Instructions
        # ------------------------------------------

        st.subheader("👨‍🍳 Instructions")

        edited_instructions = []

        for i, instruction in enumerate(
            recipe["instructions"]
        ):

            edited_instruction = st.text_area(
                f"Step {i + 1}",
                value=instruction,
                key=f"instruction_{i}",
            )

            if edited_instruction.strip():

                edited_instructions.append(
                    edited_instruction
                )

        st.divider()

        # ------------------------------------------
        # Tags
        # ------------------------------------------

        st.subheader("🏷️ Tags")

        tags_text = st.text_input(
            "Tags",
            value=", ".join(recipe["tags"]),
            help="Separate tags with commas.",
        )

        edited_tags = [
            tag.strip()
            for tag in tags_text.split(",")
            if tag.strip()
        ]

        st.divider()

        # ------------------------------------------
        # Save / Cancel
        # ------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "💾 Save Changes",
                type="primary",
                use_container_width=True,
            ):

                if not name.strip():

                    st.error(
                        "Recipe name cannot be empty."
                    )

                elif not edited_ingredients:

                    st.error(
                        "A recipe needs at least one ingredient."
                    )

                elif not edited_instructions:

                    st.error(
                        "A recipe needs at least one instruction."
                    )

                else:

                    update_recipe(
                        recipe_id=recipe_id,
                        name=name.strip(),
                        description=description.strip(),
                        servings=servings,
                        prep_time=prep_time,
                        cook_time=cook_time,
                        ingredients=edited_ingredients,
                        instructions=edited_instructions,
                        tags=edited_tags,
                    )

                    del st.session_state[
                        "editing_recipe_id"
                    ]

                    st.success(
                        "Recipe updated successfully!"
                    )

                    st.rerun()

        with col2:

            if st.button(
                "Cancel",
                use_container_width=True,
            ):

                del st.session_state[
                    "editing_recipe_id"
                ]

                st.rerun()


# ==================================================
# RECIPE DETAIL
# ==================================================

elif "selected_recipe_id" in st.session_state:

    recipe_id = st.session_state["selected_recipe_id"]

    recipe = get_recipe(recipe_id)

    if recipe is None:

        st.error("Recipe not found.")

        if st.button("← Back to My Recipes"):

            del st.session_state["selected_recipe_id"]

            st.rerun()

    else:

        # ------------------------------------------
        # Back
        # ------------------------------------------

        if st.button("← Back to My Recipes"):

            del st.session_state["selected_recipe_id"]

            st.rerun()

        st.divider()

        # ------------------------------------------
        # Recipe header
        # ------------------------------------------

        st.header(recipe["name"])

        if recipe["description"]:

            st.write(recipe["description"])

        # ------------------------------------------
        # Recipe information
        # ------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Servings",
                recipe["servings"],
            )

        with col2:
            st.metric(
                "Prep Time",
                f"{recipe['prep_time']} min",
            )

        with col3:
            st.metric(
                "Cook Time",
                f"{recipe['cook_time']} min",
            )

        st.divider()

        # ------------------------------------------
        # Ingredients
        # ------------------------------------------

        st.subheader("🥕 Ingredients")

        for ingredient in recipe["ingredients"]:

            st.write(
                f"- **{ingredient['quantity']} "
                f"{ingredient['unit']}** "
                f"{ingredient['name']}"
            )

        st.divider()

        # ------------------------------------------
        # Instructions
        # ------------------------------------------

        st.subheader("👨‍🍳 Instructions")

        for i, instruction in enumerate(
            recipe["instructions"],
            start=1,
        ):

            st.write(
                f"**{i}.** {instruction}"
            )

        st.divider()

        # ------------------------------------------
        # Tags
        # ------------------------------------------

        if recipe["tags"]:

            st.subheader("🏷️ Tags")

            st.write(
                " ".join(
                    f"`{tag}`"
                    for tag in recipe["tags"]
                )
            )

        st.divider()

        # ------------------------------------------
        # Actions
        # ------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            if st.button(
                "👨‍🍳 Start Cooking",
                type="primary",
                use_container_width=True,
            ):

                start_cooking_session(
                    user_id=user_id,
                    recipe_id=recipe["id"],
                    servings=recipe["servings"],
                )

                st.switch_page("pages/cooking_assistant.py")

        with col2:

            if st.button(
                "✏️ Edit Recipe",
                use_container_width=True,
            ):

                st.session_state[
                    "editing_recipe_id"
                ] = recipe["id"]

                st.rerun()

        with col3:

            if st.button(
                "🗑️ Delete Recipe",
                use_container_width=True,
            ):

                st.session_state[
                    "confirm_delete"
                ] = True

        # ------------------------------------------
        # Delete confirmation
        # ------------------------------------------

        if st.session_state.get(
            "confirm_delete",
            False,
        ):

            st.warning(
                f"Are you sure you want to delete "
                f"**{recipe['name']}**?"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Yes, delete",
                    type="primary",
                    use_container_width=True,
                ):

                    delete_recipe(recipe["id"])

                    del st.session_state[
                        "selected_recipe_id"
                    ]

                    del st.session_state[
                        "confirm_delete"
                    ]

                    st.success("Recipe deleted.")

                    st.rerun()

            with col2:

                if st.button(
                    "Cancel",
                    use_container_width=True,
                ):

                    del st.session_state[
                        "confirm_delete"
                    ]

                    st.rerun()


# ==================================================
# RECIPE BOOK
# ==================================================

else:

    # ------------------------------------------
    # Header + Add Recipe button
    # ------------------------------------------

    col1, col2 = st.columns([4, 1])

    with col1:

        st.write(
            "Your personal recipe collection."
        )

    with col2:

        if st.button(
            "➕ Add Recipe",
            use_container_width=True,
        ):

            st.session_state["adding_recipe"] = True

            st.rerun()

    st.divider()

    # ------------------------------------------
    # Search
    # ------------------------------------------

    search = st.text_input(
        "🔍 Search recipes",
        placeholder="Search by recipe name...",
    )

    recipes = get_all_recipes(user_id)

    filtered_recipes = [
        recipe
        for recipe in recipes
        if search.lower() in recipe["name"].lower()
    ]

    # ------------------------------------------
    # Display recipes
    # ------------------------------------------

    if not filtered_recipes:

        st.info("No recipes found.")

    else:

        cols = st.columns(3)

        for i, recipe in enumerate(
            filtered_recipes
        ):

            with cols[i % 3]:

                with st.container(border=True):

                    st.subheader(recipe["name"])

                    if recipe["description"]:

                        st.write(
                            recipe["description"]
                        )

                    total_time = (
                        recipe["prep_time"]
                        + recipe["cook_time"]
                    )

                    st.write(
                        f"⏱️ {total_time} min"
                    )

                    st.write(
                        f"🍽️ "
                        f"{recipe['servings']} servings"
                    )

                    if st.button(
                        "View Recipe",
                        key=f"view_{recipe['id']}",
                        use_container_width=True,
                    ):

                        st.session_state[
                            "selected_recipe_id"
                        ] = recipe["id"]

                        st.rerun()