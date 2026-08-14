import streamlit as st


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

        st.info(
            "AI recipe extraction will be added here."
        )


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