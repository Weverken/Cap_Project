import streamlit as st

from src.config import DEFAULT_USER_ID
from src.database.recipes import create_recipe
from src.importer.extractor import extract_recipe_from_image


st.title("📥 Import Recipe")

st.write(
    "Add a recipe to your personal recipe book using an image, "
    "document, or URL."
)

st.divider()


# Import method

import_method = st.radio(
    "How would you like to add your recipe?",
    [
        "📷 Upload Image",
        "📄 Upload Document",
        "🔗 Recipe URL",
    ],
    horizontal=True,
)


# Image

if import_method == "📷 Upload Image":

    st.subheader("Upload a recipe image")

    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg"],
    )

    if uploaded_file:
        st.image(
            uploaded_file,
            caption="Uploaded recipe",
            use_container_width=True,
        )

        if st.button("🔍 Extract Recipe", type="primary"):

            image_bytes = uploaded_file.getvalue()
            mime_type = uploaded_file.type or "image/jpeg"

            with st.spinner("Reading the recipe..."):
                result = extract_recipe_from_image(image_bytes, mime_type)

            if not result["success"]:
                st.error(f"Couldn't extract a recipe: {result['error']}")
            else:
                # Clear row state from any previous extraction so
                # this new one isn't merged with leftover edits.
                for key in ("import_ingredient_rows", "import_instruction_rows"):
                    st.session_state.pop(key, None)

                st.session_state["extracted_recipe"] = result["recipe"]

        # ------------------------------------------
        # Review & edit extracted recipe
        # ------------------------------------------

        extracted = st.session_state.get("extracted_recipe")

        if extracted:

            st.divider()
            st.header("📝 Review Extracted Recipe")

            confidence = extracted["extraction_confidence"]
            confidence_icon = {
                "high": "🟢", "medium": "🟡", "low": "🔴",
            }.get(confidence, "⚪")

            st.write(f"{confidence_icon} Extraction confidence: **{confidence}**")

            if extracted["extraction_notes"]:
                st.caption(f"AI note: {extracted['extraction_notes']}")

            st.caption(
                "Review the extracted fields below and fix anything "
                "that's wrong before saving to your recipe book."
            )

            # ------------------------------------------
            # Recipe information
            # ------------------------------------------

            name = st.text_input(
                "Recipe Name",
                value=extracted["name"],
                key="import_name",
            )

            description = st.text_area(
                "Description",
                value=extracted["description"],
                key="import_description",
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                servings = st.number_input(
                    "Servings",
                    min_value=0,
                    value=extracted["servings"],
                    step=1,
                    key="import_servings",
                    help="0 means the recipe didn't state a serving size — set a real value before saving.",
                )

            with col2:
                prep_time = st.number_input(
                    "Prep Time (minutes)",
                    min_value=0,
                    value=extracted["prep_time"],
                    step=1,
                    key="import_prep_time",
                )

            with col3:
                cook_time = st.number_input(
                    "Cook Time (minutes)",
                    min_value=0,
                    value=extracted["cook_time"],
                    step=1,
                    key="import_cook_time",
                )

            st.divider()

            # ------------------------------------------
            # Ingredients (editable, add/remove rows)
            # ------------------------------------------

            st.subheader("🥕 Ingredients")

            # Only seed row state from extraction once, so the
            # user's own add/remove actions aren't overwritten on
            # every rerun.
            if "import_ingredient_rows" not in st.session_state:
                st.session_state["import_ingredient_rows"] = (
                    [dict(ing) for ing in extracted["ingredients"]]
                    or [{"quantity": 1.0, "unit": "", "name": ""}]
                )

            ingredients = []
            rows_to_remove = []

            for i, row in enumerate(st.session_state["import_ingredient_rows"]):

                col1, col2, col3, col4 = st.columns([1, 1, 3, 0.5])

                with col1:
                    quantity = st.number_input(
                        "Quantity",
                        min_value=0.0,
                        value=float(row["quantity"]),
                        key=f"import_quantity_{i}",
                    )

                with col2:
                    unit = st.text_input(
                        "Unit",
                        value=row["unit"],
                        key=f"import_unit_{i}",
                        placeholder="g, tbsp, etc.",
                    )

                with col3:
                    ingredient_name = st.text_input(
                        "Ingredient",
                        value=row["name"],
                        key=f"import_ingredient_{i}",
                        placeholder="Ingredient name",
                    )

                with col4:
                    st.write("")  # vertical spacer to align with inputs
                    if st.button("🗑️", key=f"import_remove_ingredient_{i}"):
                        rows_to_remove.append(i)

                ingredients.append(
                    {"quantity": quantity, "unit": unit, "name": ingredient_name}
                )

                if quantity == 0:
                    st.caption(
                        "⚠️ No quantity was found on the original for "
                        f"**{ingredient_name or 'this ingredient'}** — "
                        "0 means unspecified, not none. Fill in an amount "
                        "if you'd like one."
                    )

            if rows_to_remove:
                st.session_state["import_ingredient_rows"] = [
                    row for i, row in enumerate(st.session_state["import_ingredient_rows"])
                    if i not in rows_to_remove
                ]
                st.rerun()

            if st.button("➕ Add Ingredient", key="import_add_ingredient"):
                st.session_state["import_ingredient_rows"].append(
                    {"quantity": 1.0, "unit": "", "name": ""}
                )
                st.rerun()

            st.divider()

            # ------------------------------------------
            # Instructions (editable, add/remove rows)
            # ------------------------------------------

            st.subheader("👨‍🍳 Instructions")

            if "import_instruction_rows" not in st.session_state:
                st.session_state["import_instruction_rows"] = (
                    list(extracted["instructions"]) or [""]
                )

            instructions = []
            steps_to_remove = []

            for i, step_text in enumerate(st.session_state["import_instruction_rows"]):

                col1, col2 = st.columns([5, 0.5])

                with col1:
                    instruction = st.text_area(
                        f"Step {i + 1}",
                        value=step_text,
                        key=f"import_instruction_{i}",
                        placeholder=f"Describe step {i + 1}...",
                    )

                with col2:
                    st.write("")
                    if st.button("🗑️", key=f"import_remove_step_{i}"):
                        steps_to_remove.append(i)

                instructions.append(instruction)

            if steps_to_remove:
                st.session_state["import_instruction_rows"] = [
                    step for i, step in enumerate(st.session_state["import_instruction_rows"])
                    if i not in steps_to_remove
                ]
                st.rerun()

            if st.button("➕ Add Step", key="import_add_step"):
                st.session_state["import_instruction_rows"].append("")
                st.rerun()

            st.divider()

            # ------------------------------------------
            # Tags
            # ------------------------------------------

            st.subheader("🏷️ Tags")

            tags_text = st.text_input(
                "Tags",
                value=", ".join(extracted["tags"]),
                key="import_tags",
                help="Separate tags with commas.",
            )

            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

            st.divider()

            # ------------------------------------------
            # Save / Discard
            # ------------------------------------------

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "💾 Save to My Recipes",
                    type="primary",
                    use_container_width=True,
                ):
                    if not name.strip():
                        st.error("Please enter a recipe name.")
                    elif not any(ing["name"].strip() for ing in ingredients):
                        st.error("Please add at least one ingredient.")
                    elif not any(step.strip() for step in instructions):
                        st.error("Please add at least one instruction.")
                    else:
                        clean_ingredients = [
                            ing for ing in ingredients if ing["name"].strip()
                        ]
                        clean_instructions = [
                            step.strip() for step in instructions if step.strip()
                        ]

                        recipe_id = create_recipe(
                            user_id=DEFAULT_USER_ID,
                            name=name.strip(),
                            description=description.strip(),
                            servings=servings,
                            prep_time=prep_time,
                            cook_time=cook_time,
                            ingredients=clean_ingredients,
                            instructions=clean_instructions,
                            tags=tags,
                        )

                        # Clear import-specific state
                        for key in (
                            "extracted_recipe",
                            "import_ingredient_rows",
                            "import_instruction_rows",
                        ):
                            st.session_state.pop(key, None)

                        st.session_state["selected_recipe_id"] = recipe_id
                        st.success("Recipe saved!")
                        st.switch_page("pages/my_recipes.py")

            with col2:
                if st.button("Discard", use_container_width=True):
                    for key in (
                        "extracted_recipe",
                        "import_ingredient_rows",
                        "import_instruction_rows",
                    ):
                        st.session_state.pop(key, None)
                    st.rerun()


# Document

elif import_method == "📄 Upload Document":

    st.subheader("Upload a recipe document")

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "png", "jpg", "jpeg"],
    )

    if uploaded_file:
        st.success(
            f"Uploaded: {uploaded_file.name}"
        )

        st.info(
            "AI document processing will be added here."
        )


# URL

elif import_method == "🔗 Recipe URL":

    st.subheader("Import from a website")

    url = st.text_input(
        "Recipe URL",
        placeholder="https://example.com/recipe",
    )

    if st.button("Import Recipe"):
        if url:
            st.info(
                "Recipe extraction from URLs will be added here."
            )
        else:
            st.warning(
                "Please enter a recipe URL."
            )