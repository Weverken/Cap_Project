import streamlit as st

from src.config import DEFAULT_USER_ID
from src.database.recipes import get_recipe
from src.database.cooking_sessions import (
    get_active_session,
    update_session_step,
    end_cooking_session,
)
from src.agent.service import CookingAgent


st.title("👨‍🍳 Cooking Assistant")

st.write(
    "Your AI cooking companion. Ask questions, get cooking advice, "
    "and interact with your saved recipes."
)

st.divider()

# ==================================================
# CURRENTLY COOKING (Cooking Mode)
# ==================================================

st.subheader("Currently Cooking")

active_session = get_active_session(DEFAULT_USER_ID)

if active_session is None:
    st.info(
        "No recipe selected. Go to **My Recipes**, open a recipe, "
        "and click **Start Cooking** to begin a cooking session."
    )
else:
    recipe = get_recipe(active_session["recipe_id"])

    if recipe is None:
        # Recipe was deleted mid-session — clean up rather than crash.
        end_cooking_session(active_session["id"])
        st.warning("The recipe for this session no longer exists. Session ended.")
        st.rerun()

    else:
        instructions = recipe["instructions"]
        total_steps = len(instructions)
        step_index = active_session["current_step"]

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### {recipe['name']}")
                st.caption(f"Servings: {active_session['servings']}")

            with col2:
                if st.button("End Session", use_container_width=True):
                    end_cooking_session(active_session["id"])
                    st.rerun()

            st.divider()

            st.markdown(f"**Step {step_index + 1} / {total_steps}**")
            st.write(instructions[step_index])

            nav_col1, nav_col2 = st.columns(2)

            with nav_col1:
                if st.button(
                    "⬅️ Previous",
                    use_container_width=True,
                    disabled=(step_index <= 0),
                ):
                    update_session_step(active_session["id"], step_index - 1)
                    st.rerun()

            with nav_col2:
                if st.button(
                    "Next ➡️",
                    use_container_width=True,
                    disabled=(step_index >= total_steps - 1),
                ):
                    update_session_step(active_session["id"], step_index + 1)
                    st.rerun()

            if active_session["substitutions"]:
                with st.expander("📝 Substitutions/changes this session"):
                    for note in active_session["substitutions"]:
                        st.write(f"- {note}")

st.divider()

# ==================================================
# CHAT
# ==================================================

st.subheader("Chat")

if "agent" not in st.session_state:
    try:
        st.session_state.agent = CookingAgent()
        st.session_state.agent_error = None
    except ValueError as e:
        st.session_state.agent = None
        st.session_state.agent_error = str(e)

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.agent_error:
    st.error(
        f"Couldn't start the assistant: {st.session_state.agent_error}"
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.session_state.agent is not None:
    with st.expander("🔍 Debug: raw conversation history sent to Gemini"):
        history = st.session_state.agent.chat.get_history()
        st.write(f"{len(history)} entries in history")
        for i, entry in enumerate(history):
            role = getattr(entry, "role", "?")
            parts_preview = []
            for p in getattr(entry, "parts", []):
                text = getattr(p, "text", None)
                if text is not None:
                    parts_preview.append(text[:80])
                else:
                    parts_preview.append(str(p)[:80])
            st.text(f"[{i}] {role}: {parts_preview}")

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
        if st.session_state.agent is None:
            response = (
                "The assistant isn't available right now — check "
                "that GOOGLE_API_KEY is set."
            )
        else:
            with st.spinner("Thinking..."):
                response = st.session_state.agent.send_message(prompt)

        st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    # Step navigation via chat (advance_cooking_step_tool) can change
    # the session's current_step — rerun so the Cooking Mode card
    # above reflects it immediately instead of on the next interaction.
    st.rerun()