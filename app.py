import streamlit as st
import hashlib
import json
import os

# -----------------------------
# FILE STORAGE
# -----------------------------
CREDENTIALS_FILE = "credentials.json"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin1234".encode()).hexdigest()


# -----------------------------
# PASSWORD HASHING
# -----------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# -----------------------------
# LOAD / SAVE USERS
# -----------------------------
def load_credentials() -> dict:
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_credentials(creds: dict):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)


# -----------------------------
# AUTHENTICATION
# -----------------------------
def verify_user(username: str, password: str):
    if username == ADMIN_USERNAME and hash_password(password) == ADMIN_PASSWORD_HASH:
        return "admin"

    creds = load_credentials()

    if username in creds and creds[username]["password"] == hash_password(password):
        return "user"

    return None


# -----------------------------
# CREATE USER (ADMIN ONLY)
# -----------------------------
def register_user(username: str, password: str):
    if username == ADMIN_USERNAME:
        return False, "Reserved username."

    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    creds = load_credentials()

    if username in creds:
        return False, "User already exists."

    creds[username] = {
        "password": hash_password(password),
        "role": "user"
    }

    save_credentials(creds)
    return True, "User created successfully."


# -----------------------------
# DELETE USER (ADMIN ONLY)
# -----------------------------
def delete_user(username: str):
    creds = load_credentials()

    if username not in creds:
        return False, "User not found."

    del creds[username]
    save_credentials(creds)

    return True, "User deleted successfully."


# -----------------------------
# LOGIN PAGE
# -----------------------------
def render_login():
    st.title("🚌 MOLO SACCO LOGIN")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        role = verify_user(username, password)

        if role:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["role"] = role
            st.rerun()
        else:
            st.error("Invalid credentials")


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
def render_admin():
    st.title("👑 Admin Dashboard")

    st.subheader("Create User")

    new_user = st.text_input("New username")
    new_pass = st.text_input("New password", type="password")

    if st.button("Create User"):
        ok, msg = register_user(new_user, new_pass)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    st.divider()

    st.subheader("All Users")
    creds = load_credentials()
    st.write(list(creds.keys()))

    st.divider()

    st.subheader("Delete User")
    del_user = st.text_input("Username to delete")

    if st.button("Delete"):
        ok, msg = delete_user(del_user)
        if ok:
            st.success(msg)
        else:
            st.error(msg)


# -----------------------------
# USER DASHBOARD
# -----------------------------
def render_user():
    st.title("📊 User Dashboard")
    st.success(f"Welcome {st.session_state['username']} 👋")


# -----------------------------
# MAIN APP
# -----------------------------
def main():

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        render_login()
        return

    # Sidebar
    st.sidebar.write(f"User: {st.session_state['username']}")
    st.sidebar.write(f"Role: {st.session_state['role']}")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    # ROLE ROUTING
    if st.session_state["role"] == "admin":
        render_admin()
    else:
        render_user()


if __name__ == "__main__":
    main()
