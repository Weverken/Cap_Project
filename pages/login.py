import streamlit as st

from src.auth import login, signup


hero_col, form_col = st.columns([3, 2], gap="large")

with hero_col:

    st.markdown("# 🍳 CookMate")

    st.markdown(
        "### Cook with an assistant that knows what's in your pan."
    )

    st.write(
        "Most recipe apps just store text. CookMate's assistant can "
        "actually act on your recipes — scale them, swap out "
        "ingredients you don't have, and keep track of exactly which "
        "step you're on while you cook."
    )

    st.divider()

    st.markdown("**Talk to it while you cook**")
    st.write(
        "\"Scale my curry to 6 people.\" \"I don't have buttermilk, "
        "what can I use instead?\" \"I'm on this step and the sauce "
        "looks too thick.\" The assistant knows what recipe you have "
        "open and which step you're on, so you don't have to explain "
        "context every time."
    )

    st.markdown("**Build your own recipe book**")
    st.write(
        "Save recipes, search them by name or by what's already in "
        "your fridge, and ask what you can make with the ingredients "
        "you have on hand."
    )

    st.markdown("**Import from a photo or a link**")
    st.write(
        "Snap a photo of a handwritten recipe card — even messy "
        "handwriting — or paste a link to a recipe online. Review "
        "what gets extracted, fix anything that's off, and save it."
    )

    st.divider()

    st.caption(
        "Sign up to get started — your recipes are private to your "
        "account."
    )

with form_col:

    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    with tab_login:

        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In", type="primary")

            if submitted:
                if not username or not password:
                    st.error("Please enter both a username and password.")
                else:
                    result = login(username, password)

                    if result["success"]:
                        st.session_state["user_id"] = result["user_id"]
                        st.session_state["username"] = username.strip()
                        st.rerun()
                    else:
                        st.error(result["error"])

    with tab_signup:

        with st.form("signup_form"):
            new_username = st.text_input(
                "Username",
                key="signup_username",
                help="3-32 characters: letters, numbers, or underscores only.",
            )
            new_password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
                help="At least 8 characters.",
            )
            confirm_password = st.text_input(
                "Confirm Password", type="password", key="signup_confirm"
            )
            submitted = st.form_submit_button("Create Account", type="primary")

            if submitted:
                if not new_username or not new_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords don't match.")
                else:
                    result = signup(new_username, new_password)

                    if result["success"]:
                        st.session_state["user_id"] = result["user_id"]
                        st.session_state["username"] = new_username.strip()
                        st.success("Account created!")
                        st.rerun()
                    else:
                        st.error(result["error"])