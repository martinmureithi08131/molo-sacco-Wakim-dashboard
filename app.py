import streamlit as st
import hashlib
import json
import os

# =========================================
# CONFIG
# =========================================

CREDENTIALS_FILE = "credentials.json"

ADMIN_USERNAME = "Admin"
ADMIN_PASSWORD_HASH = hashlib.sha256(
    "Admin08131".encode()
).hexdigest()

# =========================================
# SESSION STATE
# =========================================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "username" not in st.session_state:
    st.session_state["username"] = None

if "role" not in st.session_state:
    st.session_state["role"] = None

# =========================================
# UTILITY FUNCTIONS
# =========================================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_credentials() -> dict:
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, "r") as f:
                return json.load(f)
    except:
        return {}

    return {}


def save_credentials(creds: dict):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)


def verify_user(username: str, password: str):

    # ADMIN LOGIN
    if (
        username == ADMIN_USERNAME
        and hash_password(password) == ADMIN_PASSWORD_HASH
    ):
        return "admin"

    # NORMAL USER LOGIN
    creds = load_credentials()

    if (
        username in creds
        and creds[username]["password"] == hash_password(password)
    ):
        return "user"

    return None


def register_user(username: str, password: str):

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

    return True, "User created successfully."


def delete_user(username: str):

    creds = load_credentials()

    if username not in creds:
        return False, "User not found."

    del creds[username]

    save_credentials(creds)

    return True, f"User '{username}' deleted."


def change_user_password(username: str, new_password: str):

    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."

    creds = load_credentials()

    if username not in creds:
        return False, "User not found."

    creds[username]["password"] = hash_password(new_password)

    save_credentials(creds)

    return True, "Password updated."


def logout():

    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None

    st.rerun()

# =========================================
# LOGIN PAGE
# =========================================

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
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }

    .login-wrap h2 {
        text-align:center;
        margin-bottom:4px;
        font-size:1.5rem;
    }

    .login-wrap p {
        text-align:center;
        opacity:.7;
        font-size:.85rem;
        margin-bottom:28px;
    }

    </style>

    <div class="login-wrap">
      <h2>🚌 MOLO SACCO</h2>
      <p>KBW 066S · Nakuru ↔ Naivasha · Cashflow Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1,2,1])[1]

    with col:

        username = st.text_input(
            "Username",
            placeholder="Enter username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        if st.button(
            "🔐 Login",
            use_container_width=True,
            type="primary"
        ):

            if not username or not password:
                st.error(
                    "Please enter both username and password."
                )

            else:

                role = verify_user(username, password)

                if role:

                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = role

                    st.rerun()

                else:
                    st.error(
                        "Invalid username or password."
                    )

# =========================================
# MAIN APP
# =========================================

def render_dashboard():

    st.sidebar.success(
        f"Logged in as: {st.session_state['username']}"
    )

    st.sidebar.button(
        "🚪 Logout",
        on_click=logout
    )

    st.title("📊 MOLO SACCO Dashboard")

    st.write(
        "Welcome to the cashflow management system."
    )

    # =====================================
    # ADMIN PANEL
    # =====================================

    if st.session_state["role"] == "admin":

        st.divider()

        st.subheader("👑 Admin Panel")

        # ==============================
        # CREATE USER
        # ==============================

        with st.expander("➕ Create New User"):

            new_user = st.text_input(
                "New Username"
            )

            new_pass = st.text_input(
                "New Password",
                type="password"
            )

            if st.button("Create User"):

                ok, msg = register_user(
                    new_user,
                    new_pass
                )

                if ok:
                    st.success(msg)

                else:
                    st.error(msg)

        # ==============================
        # RESET PASSWORD
        # ==============================

        with st.expander("🔑 Reset User Password"):

            creds = load_credentials()

            if creds:

                selected_user = st.selectbox(
                    "Select User",
                    list(creds.keys())
                )

                new_password = st.text_input(
                    "New Password",
                    type="password"
                )

                if st.button("Update Password"):

                    ok, msg = change_user_password(
                        selected_user,
                        new_password
                    )

                    if ok:
                        st.success(msg)

                    else:
                        st.error(msg)

            else:
                st.info("No users available.")

        # ==============================
        # DELETE USER
        # ==============================

        with st.expander("🗑 Delete User"):

            creds = load_credentials()

            if creds:

                delete_target = st.selectbox(
                    "Choose User",
                    list(creds.keys()),
                    key="delete_user"
                )

                if st.button(
                    "Delete User",
                    type="secondary"
                ):

                    ok, msg = delete_user(
                        delete_target
                    )

                    if ok:
                        st.success(msg)
                        st.rerun()

                    else:
                        st.error(msg)

            else:
                st.info("No users found.")

        # ==============================
        # VIEW USERS
        # ==============================

        with st.expander("👥 View Users"):

            creds = load_credentials()

            if creds:

                st.write("Registered Users:")

                for user in creds.keys():
                    st.write(f"• {user}")

            else:
                st.info("No users registered.")

# =========================================
# APP ROUTER
# =========================================

if st.session_state["authenticated"]:
    render_dashboard()

else:
    render_login_page()
