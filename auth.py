import streamlit as st
import hashlib
import json
import os

CREDENTIALS_FILE = "credentials.json"

ADMIN_USERNAME = "Admin"

ADMIN_PASSWORD_HASH = hashlib.sha256(
    "Admin08131".encode()
).hexdigest()


def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


def load_credentials():

    try:
        if os.path.exists(CREDENTIALS_FILE):

            with open(CREDENTIALS_FILE, "r") as f:
                return json.load(f)

    except:
        return {}

    return {}


def save_credentials(creds):

    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)


def verify_user(username, password):

    if (
        username == ADMIN_USERNAME
        and hash_password(password)
        == ADMIN_PASSWORD_HASH
    ):
        return "admin"

    creds = load_credentials()

    if (
        username in creds
        and creds[username]["password"]
        == hash_password(password)
    ):
        return "user"

    return None


def register_user(username, password):

    if username == ADMIN_USERNAME:
        return False, "Username reserved."

    if len(username.strip()) < 3:
        return False, "Username too short."

    if len(password) < 6:
        return False, "Password too short."

    creds = load_credentials()

    if username in creds:
        return False, "Username already exists."

    creds[username] = {
        "password": hash_password(password)
    }

    save_credentials(creds)

    return True, "User created successfully."


def delete_user(username):

    creds = load_credentials()

    if username not in creds:
        return False, "User not found."

    del creds[username]

    save_credentials(creds)

    return True, "User deleted."


def change_user_password(username, new_password):

    creds = load_credentials()

    if username not in creds:
        return False, "User not found."

    creds[username]["password"] = hash_password(
        new_password
    )

    save_credentials(creds)

    return True, "Password updated."


def render_login_page():

    st.markdown("""
    <style>

    .login-wrap{
        max-width:420px;
        margin:70px auto;
        padding:40px;
        border-radius:16px;
        background:linear-gradient(
            135deg,
            #1a1a2e,
            #16213e,
            #0f3460
        );
        color:white;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-wrap">

    <h2 style="text-align:center;">
    🚌 MOLO SACCO
    </h2>

    <p style="text-align:center;">
    Cashflow Dashboard
    </p>

    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1,2,1])[1]

    with col:

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "🔐 Login",
            use_container_width=True
        ):

            role = verify_user(
                username,
                password
            )

            if role:

                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["role"] = role

                st.rerun()

            else:
                st.error(
                    "Invalid username or password."
                )
