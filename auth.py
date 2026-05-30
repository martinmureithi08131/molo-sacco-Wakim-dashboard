import streamlit as st
import hashlib
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1LSB0XGF_0eS9w3DCom71aBymN5YwslMyyn6PDLKwgpo"
ADMIN_USERNAME = "Admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("Admin08131".encode()).hexdigest()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_spreadsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)

def get_creds_sheet():
    spreadsheet = get_spreadsheet()
    sheet_names = [ws.title for ws in spreadsheet.worksheets()]
    if "credentials" not in sheet_names:
        ws = spreadsheet.add_worksheet(title="credentials", rows=100, cols=3)
        ws.append_row(["username", "password"])
    else:
        ws = spreadsheet.worksheet("credentials")
        # Ensure headers exist
        if not ws.row_values(1):
            ws.append_row(["username", "password"])
    return ws

def load_credentials() -> dict:
    ws = get_creds_sheet()
    records = ws.get_all_records()
    return {r["username"]: {"password": r["password"]} for r in records if r.get("username")}

def save_credentials(creds: dict):
    ws = get_creds_sheet()
    ws.clear()
    ws.append_row(["username", "password"])
    for username, data in creds.items():
        ws.append_row([username, data["password"]])

def verify_user(username: str, password: str) -> str | None:
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
        st.markdown("<br>", unsafe_allow_html=True)
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
        st.caption("Contact the admin to get an account.")
