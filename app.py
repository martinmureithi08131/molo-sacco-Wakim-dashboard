# 🚌 MOLO SACCO – Daily Earnings Dashboard
# KBW 066S | Nakuru ↔ Naivasha | 2026/2027 Financial Year

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from datetime import date
from auth import (
    render_login_page,
    delete_user,
    change_user_password,
    load_credentials,
    register_user,
)
from database import add_record, get_records, get_db

st.set_page_config(
    page_title="MOLO SACCO – Daily Earnings",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth Gate ────────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    render_login_page()
    st.stop()

role = st.session_state.get("role", "user")
uname = st.session_state.get("username", "")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main {padding-top: 1rem;}
    .metric-card {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
        color: white;
        padding: 1rem;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    .sub-card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }
    .small-muted {color: #6b7280; font-size: 0.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Helpers ──────────────────────────────────────────────────────────────────
def fmt_kes(val):
    try:
        return f"KES {float(val):,.0f}"
    except Exception:
        return "KES 0"


def to_excel_bytes(sheets):
    buf = BytesIO()
    valid = {k: v for k, v in sheets.items() if isinstance(v, pd.DataFrame) and not v.empty}
    if not valid:
        valid = {"No Data": pd.DataFrame({"Info": ["No data entered yet."]})}
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in valid.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return buf.getvalue()


def records_to_df(table, keep_id=False):
    rows = get_records(table)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if not keep_id and "_id" in df.columns:
        df = df.drop(columns=["_id"])
    return df


def update_record(table: str, doc_id: str, updates: dict):
    db = get_db()
    db.collection(table).document(doc_id).update(updates)


def safe_float(v, default=0.0):
    try:
        if v is None or v == "":
            return float(default)
        return float(v)
    except Exception:
        return float(default)


def ensure_columns(df: pd.DataFrame, cols: list):
    for c in cols:
        if c not in df.columns:
            df[c] = 0 if c not in ["date", "driver", "conductor", "notes"] else ""
    return df


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    badge = "👑 Admin" if role == "admin" else "👤 User"
    st.markdown(f"**{badge}** · `{uname}`")

    if st.button("🚪 Logout", use_container_width=True):
        for k in ["authenticated", "username", "role"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown("---")
    st.markdown("**🚌 KBW 066S | MOLO SACCO**")
    st.markdown("Route: Nakuru ↔ Naivasha")
    st.markdown("Owner: Josphat Njuguna Kimani")

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    ## MOLO SACCO – Daily Earnings Dashboard
    **KBW 066S** · Nakuru ↔ Naivasha · 2026/2027 Financial Year
    """
)

tabs = ["Daily Entry", "Reports"]
if role == "admin":
    tabs += ["Edit Transactions", "User Management"]

selected_tab = st.tabs(tabs)

# ── Tab 1: Daily Entry ───────────────────────────────────────────────────────
with selected_tab[0]:
    st.subheader("Daily Transaction Entry")

    with st.form("daily_entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            driver = st.text_input("Driver Name")
            fuel = st.number_input("Fuel (KES)", min_value=0.0, step=50.0)
            parking = st.number_input("Parking (KES)", min_value=0.0, step=20.0)
            stage = st.number_input("Stage/County Fee (KES)", min_value=0.0, step=20.0)
            police = st.number_input("Police/Bribes (KES)", min_value=0.0, step=20.0)

        with c2:
            conductor = st.text_input("Conductor Name")
            cash_collected = st.number_input("Cash Collected (KES)", min_value=0.0, step=100.0)
            repair = st.number_input("Repairs/Maintenance (KES)", min_value=0.0, step=50.0)
            loading = st.number_input("Loading/Turnboy (KES)", min_value=0.0, step=20.0)
            other = st.number_input("Other Expenses (KES)", min_value=0.0, step=20.0)
            notes = st.text_area("Notes")

        submitted = st.form_submit_button("💾 Save Transaction", use_container_width=True)

        if submitted:
            
