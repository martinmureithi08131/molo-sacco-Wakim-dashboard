import streamlit as st
import hashlib
import json
import os

CREDENTIALS_FILE = "credentials.json"

ADMIN_USERNAME = "Admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("Admin08131".encode()).hexdigest()


# -----------------------------
# PASSWORD HASHING
# -----------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# -----------------------------
# LOAD / SAVE CREDENTIALS
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
# AUTH CHECK
# -----------------------------
def verify_user(username: str, password: str):
    if username == ADMIN_USERNAME and hash_password(password) == ADMIN_PASSWORD_HASH:
        return "admin"

    creds = load_credentials()
    if username in creds and creds[username]["password"] == hash_password(password):
        return "user"

    return None


# -----------------------------
# USER MANAGEMENT (ADMIN ONLY)
# -----------------------------
def register_user(username: str, password: str):
    if username == ADMIN_USERNAME:
        return False, "Username reserved for system admin."

    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    creds = load_credentials()

    if username in creds:
        return False, "Username already exists."

    creds[username] = {
        "password": hash_password(password),
        "role": "user"
    }

    save_credentials(creds)
    return True, "User created successfully!"


def delete_user(username: str):
    creds = load_credentials()

    if username not in creds:
        return False, "User not found."

    del creds[username]
    save_credentials(creds)

    return True, f"User '{username}' deleted."


# -----------------------------
# LOGIN PAGE
# -----------------------------
def render_login_page():
    st.title("🚌 MOLO SACCO LOGIN")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.error("Please enter both fields.")
        else:
            role = verify_user(username, password)

            if role:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["role"] = role
                st.rerun()
            else:
                st.error("Invalid username or password.")


# -----------------------------
# ADMIN PANEL
# -----------------------------
def render_admin_panel():
    st.title("👑 Admin Dashboard")

    st.subheader("Create New User")

    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")

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

    if st.button("Delete User"):
        ok, msg = delete_user(del_user)
        if ok:
            st.success(msg)
        else:
            st.error(msg)


# -----------------------------
# USER DASHBOARD
# -----------------------------
def render_user_dashboard():
    st.title("📊 User Dashboard")
    st.success(f"Welcome {st.session_state['username']} 👋")
    st.write("You are logged in as a normal user.")


# -----------------------------
# MAIN APP
# -----------------------------
def main():

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        render_login_page()
        return

    # Sidebar
    st.sidebar.write(f"Logged in as: **{st.session_state['username']}**")
    st.sidebar.write(f"Role: **{st.session_state['role']}**")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    # Role-based routing
    if st.session_state["role"] == "admin":
        render_admin_panel()
    else:
        render_user_dashboard()


if __name__ == "__main__":
    main()
