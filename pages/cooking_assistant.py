import streamlit as st


st.title("👨‍🍳 Cooking Assistant")

st.write(
    "Your AI cooking companion. Ask questions, get cooking advice, "
    "and interact with your saved recipes."
)

st.divider()

# Current recipe placeholder
st.subheader("Currently Cooking")

st.info(
    "No recipe selected. Choose a recipe from your recipe book "
    "to start cooking."
)

st.divider()

# Chat interface placeholder
st.subheader("Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything about cooking..."):
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = (
            "The AI cooking assistant will be connected here."
        )
        st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )