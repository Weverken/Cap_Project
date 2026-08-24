import streamlit as st

from src.auth import login, signup


st.title("🍳 Welcome to CookMate")

st.write("Sign in to access your recipes, or create a new account.")

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