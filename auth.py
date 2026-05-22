import streamlit as st
import json
import bcrypt
import os

CREDENTIALS_FILE = "credentials.json"


# ─────────────────────────────────────────────
# LOAD CREDENTIALS
# ─────────────────────────────────────────────
def load_credentials():

    if not os.path.exists(CREDENTIALS_FILE):

        default_admin = {
            "admin": {
                "password": bcrypt.hashpw(
                    "admin123".encode(),
                    bcrypt.gensalt()
                ).decode(),
                "role": "admin"
            }
        }

        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(default_admin, f, indent=4)

    with open(CREDENTIALS_FILE, "r") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# SAVE CREDENTIALS
# ─────────────────────────────────────────────
def save_credentials(data):

    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def render_login_page():

    st.title("🔐 Login")

    username = st.text_input("Username")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        creds = load_credentials()

        if username not in creds:
            st.error("Invalid username.")
            return

        stored_pw = creds[username]["password"]

        if bcrypt.checkpw(
            password.encode(),
            stored_pw.encode()
        ):

            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["role"] = creds[username]["role"]

            st.rerun()

        else:
            st.error("Invalid password.")


# ─────────────────────────────────────────────
# REGISTER USER
# ADMIN ONLY
# ─────────────────────────────────────────────
def register_user(username, password):

    if st.session_state.get("role") != "admin":
        return False, "Only admins can create users."

    creds = load_credentials()

    if username in creds:
        return False, "Username already exists."

    if len(username) < 3:
        return False, "Username too short."

    if len(password) < 4:
        return False, "Password too short."

    hashed_pw = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    creds[username] = {
        "password": hashed_pw,
        "role": "user"
    }

    save_credentials(creds)

    return True, "User created successfully."


# ─────────────────────────────────────────────
# DELETE USER
# ─────────────────────────────────────────────
def delete_user(username):

    creds = load_credentials()

    if username == "admin":
        return False, "Cannot delete admin."

    if username not in creds:
        return False, "User not found."

    del creds[username]

    save_credentials(creds)

    return True, "User deleted successfully."


# ─────────────────────────────────────────────
# RESET PASSWORD
# ─────────────────────────────────────────────
def change_user_password(username, new_password):

    creds = load_credentials()

    if username not in creds:
        return False, "User not found."

    hashed_pw = bcrypt.hashpw(
        new_password.encode(),
        bcrypt.gensalt()
    ).decode()

    creds[username]["password"] = hashed_pw

    save_credentials(creds)

    return True, "Password updated successfully."
