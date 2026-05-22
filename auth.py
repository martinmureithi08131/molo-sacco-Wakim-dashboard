import streamlit as st
import hashlib
import json
import os

CREDENTIALS_FILE = "credentials.json"

ADMIN_USERNAME = "Admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("Admin08131".encode()).hexdigest()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_credentials() -> dict:
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_credentials(creds: dict):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)

def verify_user(username: str, password: str) -> str | None:
    """Returns role: 'admin', 'user', or None if invalid."""
    if username == ADMIN_USERNAME and hash_password(password) == ADMIN_PASSWORD_HASH:
        return "admin"
    creds = load_credentials()
    if username in creds and creds[username]["password"] == hash_password(password):
        return "user"
    return None

def register_user(username: str, password: str) -> tuple[bool, str]:
    if username == ADMIN_USERNAME:
        return False, "Username reserved."
    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    creds = load_credentials()
    if username in creds:
        return False, "Username already exists."
    creds[username] = {"password": hash_password(password)}
    save_credentials(creds)
    return True, "Account created successfully!"

def delete_user(username: str) -> tuple[bool, str]:
    creds = load_credentials()
    if username not in creds:
        return False, "User not found."
    del creds[username]
    save_credentials(creds)
    return True, f"User '{username}' deleted."

def change_user_password(username: str, new_password: str) -> tuple[bool, str]:
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    creds = load_credentials()
    if username not in creds:
        return False, "User not found."
    creds[username]["password"] = hash_password(new_password)
    save_credentials(creds)
    return True, "Password updated."

def render_login_page():
    st.markdown("""
    <style>
    .login-wrap {
        max-width: 420px; margin: 60px auto 0; padding: 40px 36px;
        background: linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
        border-radius: 16px; color: white; box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    .login-wrap h2 { text-align:center; margin-bottom:4px; font-size:1.5rem; }
    .login-wrap p  { text-align:center; opacity:.7; font-size:.85rem; margin-bottom:28px; }
    </style>
    <div class="login-wrap">
      <h2>🚌 MOLO SACCO</h2>
      <p>KBW 066S · Nakuru ↔ Naivasha · Cashflow Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        mode = st.radio("", ["Login", "Create Account"], horizontal=True, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)

        if mode == "Login":
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            if st.button("🔐 Login", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    role = verify_user(username, password)
                    if role:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["role"] = role
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
        else:
            new_user = st.text_input("Choose a username", placeholder="min. 3 characters")
            new_pass = st.text_input("Choose a password", type="password", placeholder="min. 6 characters")
            new_pass2 = st.text_input("Confirm password", type="password", placeholder="Repeat password")
            if st.button("✅ Create Account", use_container_width=True, type="primary"):
                if new_pass != new_pass2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(new_user, new_pass)
                    if ok:
                        st.success(msg + " You can now log in.")
                    else:
                        st.error(msg)
