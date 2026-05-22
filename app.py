import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from io import BytesIO
from datetime import date

from auth import (
    render_login_page,
    delete_user,
    change_user_password,
    load_credentials,
    register_user
)

from database import (
    add_record,
    get_records,
    update_record,
    delete_record
)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="MOLO SACCO Dashboard",
    page_icon="🚌",
    layout="wide"
)

# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    render_login_page()
    st.stop()

role = st.session_state.get("role")
uname = st.session_state.get("username")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_kes(val):

    try:
        return f"KES {float(val):,.0f}"
    except:
        return "KES 0"


def records_to_df(table):

    rows = get_records(table)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if "_id" in df.columns:
        df["_id"] = df["_id"].astype(str)

    return df


def to_excel_bytes(sheets):

    buf = BytesIO()

    with pd.ExcelWriter(
        buf,
        engine="openpyxl"
    ) as writer:

        for name, df in sheets.items():
            df.to_excel(
                writer,
                sheet_name=name[:31],
                index=False
            )

    return buf.getvalue()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("🚌 MOLO SACCO Dashboard")

st.caption("Nakuru ↔ Naivasha Route")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:

    st.write(f"Logged in as: `{uname}`")

    if role == "admin":
        st.success("Admin Access")
    else:
        st.info("User Access")

    if st.button("Logout"):

        for k in [
            "authenticated",
            "username",
            "role"
        ]:
            st.session_state.pop(k, None)

        st.rerun()

# ─────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────
all_records = records_to_df("daily_earnings")

gross_total = 0
exp_total = 0
net_total = 0

if not all_records.empty:

    gross_total = pd.to_numeric(
        all_records["gross_earnings"],
        errors="coerce"
    ).sum()

    exp_total = pd.to_numeric(
        all_records["total_expenditures"],
        errors="coerce"
    ).sum()

    net_total = gross_total - exp_total

c1, c2, c3 = st.columns(3)

c1.metric("Gross Earnings", fmt_kes(gross_total))
c2.metric("Expenses", fmt_kes(exp_total))
c3.metric("Net Income", fmt_kes(net_total))

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tabs = ["📅 Enter Record", "📋 Reports"]

if role == "admin":
    tabs.append("⚙️ Admin")

tab_objects = st.tabs(tabs)

# ═════════════════════════════════════════════
# TAB 1
# ═════════════════════════════════════════════
with tab_objects[0]:

    st.subheader("Enter Daily Record")

    if "exp_rows" not in st.session_state:
        st.session_state.exp_rows = [
            {
                "description": "",
                "amount": 0.0
            }
        ]

    col1, col2 = st.columns(2)

    with col1:
        entry_date = st.date_input(
            "Date",
            value=date.today()
        )

    with col2:
        gross = st.number_input(
            "Gross Earnings",
            min_value=0.0,
            step=100.0
        )

    st.markdown("### Expenditures")

    for i, row in enumerate(st.session_state.exp_rows):

        a, b, c = st.columns([3, 2, 1])

        with a:
            st.session_state.exp_rows[i]["description"] = st.text_input(
                f"Description #{i+1}",
                value=row["description"],
                key=f"desc_{i}"
            )

        with b:
            st.session_state.exp_rows[i]["amount"] = st.number_input(
                f"Amount #{i+1}",
                value=float(row["amount"]),
                min_value=0.0,
                step=50.0,
                key=f"amt_{i}"
            )

        with c:
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button(
                "Delete",
                key=f"delete_{i}"
            ):
                st.session_state.exp_rows.pop(i)
                st.rerun()

    if st.button("➕ Add Expenditure"):

        st.session_state.exp_rows.append({
            "description": "",
            "amount": 0.0
        })

        st.rerun()

    total_exp = sum(
        r["amount"] for r in st.session_state.exp_rows
    )

    net_income = gross - total_exp

    st.metric("Net Daily Income", fmt_kes(net_income))

    if st.button(
        "💾 Save Record",
        type="primary"
    ):

        exp_list = [
            r for r in st.session_state.exp_rows
            if r["description"].strip()
        ]

        add_record("daily_earnings", {
            "date": str(entry_date),
            "gross_earnings": gross,
            "expenditures": exp_list,
            "total_expenditures": total_exp,
            "net_daily_income": net_income,
            "entered_by": uname
        })

        st.success("Record saved.")

        st.session_state.exp_rows = [
            {
                "description": "",
                "amount": 0.0
            }
        ]

        st.rerun()

# ═════════════════════════════════════════════
# TAB 2
# ═════════════════════════════════════════════
with tab_objects[1]:

    st.subheader("Reports")

    df = records_to_df("daily_earnings")

    if df.empty:
        st.info("No records found.")

    else:

        df["date"] = pd.to_datetime(df["date"])

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df["date"],
            y=df["gross_earnings"],
            name="Gross"
        ))

        fig.add_trace(go.Bar(
            x=df["date"],
            y=df["total_expenditures"],
            name="Expenses"
        ))

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["net_daily_income"],
            mode="lines+markers",
            name="Net"
        ))

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            df,
            use_container_width=True
        )

# ═════════════════════════════════════════════
# TAB 3 ADMIN
# ═════════════════════════════════════════════
if role == "admin":

    with tab_objects[2]:

        st.subheader("Admin Panel")

        # USERS
        st.markdown("## 👥 Users")

        creds = load_credentials()

        users = list(creds.keys())

        st.dataframe(
            pd.DataFrame({
                "Username": users
            }),
            use_container_width=True,
            hide_index=True
        )

        # CREATE USER
        st.markdown("## ➕ Create User")

        new_user = st.text_input(
            "Username"
        )

        new_pw = st.text_input(
            "Password",
            type="password"
        )

        confirm_pw = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button("Create User"):

            if new_pw != confirm_pw:
                st.error("Passwords do not match.")

            else:

                ok, msg = register_user(
                    new_user,
                    new_pw
                )

                if ok:
                    st.success(msg)
                    st.rerun()

                else:
                    st.error(msg)

        # DELETE USER
        st.markdown("## 🗑️ Delete User")

        selected_user = st.selectbox(
            "Select User",
            users
        )

        if st.button("Delete User"):

            ok, msg = delete_user(selected_user)

            if ok:
                st.success(msg)
                st.rerun()

            else:
                st.error(msg)

        # RESET PASSWORD
        st.markdown("## 🔑 Reset Password")

        reset_user = st.selectbox(
            "User",
            users,
            key="reset_user"
        )

        reset_pw = st.text_input(
            "New Password",
            type="password"
        )

        if st.button("Reset Password"):

            ok, msg = change_user_password(
                reset_user,
                reset_pw
            )

            if ok:
                st.success(msg)

            else:
                st.error(msg)

        # EDIT TRANSACTIONS
        st.markdown("---")
        st.markdown("## ✏️ Edit Transactions")

        records_df = records_to_df(
            "daily_earnings"
        )

        if not records_df.empty:

            records_df["display"] = (
                records_df["date"].astype(str)
                + " | "
                + records_df["gross_earnings"].astype(str)
            )

            selected_record = st.selectbox(
                "Select Record",
                records_df["display"]
            )

            row = records_df[
                records_df["display"] == selected_record
            ].iloc[0]

            edit_gross = st.number_input(
                "Gross Earnings",
                value=float(row["gross_earnings"]),
                step=100.0
            )

            edit_exp = st.number_input(
                "Total Expenditures",
                value=float(row["total_expenditures"]),
                step=100.0
            )

            new_net = edit_gross - edit_exp

            st.info(
                f"Net Income: {fmt_kes(new_net)}"
            )

            if st.button("Update Transaction"):

                ok = update_record(
                    "daily_earnings",
                    row["_id"],
                    {
                        "gross_earnings": edit_gross,
                        "total_expenditures": edit_exp,
                        "net_daily_income": new_net
                    }
                )

                if ok:
                    st.success("Transaction updated.")
                    st.rerun()

                else:
                    st.error("Update failed.")

        # DELETE TRANSACTION
        st.markdown("---")
        st.markdown("## ❌ Delete Transaction")

        if not records_df.empty:

            delete_record_option = st.selectbox(
                "Select Transaction",
                records_df["display"],
                key="delete_transaction"
            )

            delete_row = records_df[
                records_df["display"] == delete_record_option
            ].iloc[0]

            if st.button(
                "Delete Transaction",
                type="primary"
            ):

                ok = delete_record(
                    "daily_earnings",
                    delete_row["_id"]
                )

                if ok:
                    st.success("Transaction deleted.")
                    st.rerun()

                else:
                    st.error("Delete failed.")
