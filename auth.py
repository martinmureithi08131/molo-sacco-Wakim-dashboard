import streamlit as st
import hashlib
import json
import os

CREDENTIALS_FILE = "credentials.json"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256(
    "admin1234".encode()
).hexdigest()


# ─────────────────────────────────────────────
# HASH PASSWORD
# ─────────────────────────────────────────────
def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# ─────────────────────────────────────────────
# LOAD CREDS
# ─────────────────────────────────────────────
def load_credentials() -> dict:

    if os.path.exists(CREDENTIALS_FILE):

        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)

    return {}


# ─────────────────────────────────────────────
# SAVE CREDS
# ─────────────────────────────────────────────
def save_credentials(creds: dict):

    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)


# ─────────────────────────────────────────────
# VERIFY USER
# ─────────────────────────────────────────────
def verify_user(username: str, password: str):

    if (
        username == ADMIN_USERNAME
        and hash_password(password) == ADMIN_PASSWORD_HASH
    ):
        return "admin"

    creds = load_credentials()

    if (
        username in creds
        and creds[username]["password"] == hash_password(password)
    ):
        return "user"

    return None


# ─────────────────────────────────────────────
# REGISTER USER
# ADMIN ONLY
# ─────────────────────────────────────────────
def register_user(username: str, password: str):

    if st.session_state.get("role") != "admin":
        return False, "Only admin can create accounts."

    if username == ADMIN_USERNAME:
        return False, "Username reserved."

    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    creds = load_credentials()

    if username in creds:
        return False, "Username already exists."

    creds[username] = {
        "password": hash_password(password)
    }

    save_credentials(creds)

    return True, "User account created."


# ─────────────────────────────────────────────
# DELETE USER
# ─────────────────────────────────────────────
def delete_user(username: str):

    creds = load_credentials()

    if username not in creds:
        return False, "User not found."

    del creds[username]

    save_credentials(creds)

    return True, f"User '{username}' deleted."


# ─────────────────────────────────────────────
# RESET PASSWORD
# ─────────────────────────────────────────────
def change_user_password(
    username: str,
    new_password: str
):

    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."

    creds = load_credentials()

    if username not in creds:
        return False, "User not found."

    creds[username]["password"] = hash_password(new_password)

    save_credentials(creds)

    return True, "Password updated."


# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def render_login_page():

    st.markdown("""
    <style>
    .login-wrap {
        max-width: 420px;
        margin: 60px auto 0;
        padding: 40px 36px;
        background: linear-gradient(
            135deg,
            #1a1a2e,
            #16213e,
            #0f3460
        );
        border-radius: 16px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-wrap">
      <h2 style="text-align:center;">
      🚌 MOLO SACCO
      </h2>

      <p style="text-align:center;">
      KBW 066S · Nakuru ↔ Naivasha
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
            use_container_width=True,
            type="primary"
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
