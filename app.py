import streamlit as st
import pandas as pd
from datetime import date

from auth import (
    render_login_page,
    load_credentials,
    register_user,
    delete_user,
    change_user_password
)

from database import (
    add_record,
    get_records,
    update_record,
    delete_record
)

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="MOLO SACCO Dashboard",
    page_icon="🚌",
    layout="wide"
)

# =========================================================
# AUTHENTICATION
# =========================================================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    render_login_page()
    st.stop()

role = st.session_state.get("role", "user")
uname = st.session_state.get("username", "Unknown")

# =========================================================
# HELPERS
# =========================================================

def fmt_kes(x):

    try:
        return f"KES {float(x):,.0f}"

    except:
        return "KES 0"


def records_to_df(collection):

    rows = get_records(collection)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    return df


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🚌 MOLO SACCO")

    st.success(f"Logged in as: {uname}")

    if role == "admin":
        st.info("Role: Admin")

    else:
        st.info("Role: User")

    st.markdown("---")

    if st.button("🚪 Logout"):

        st.session_state.clear()

        st.rerun()

# =========================================================
# MAIN HEADER
# =========================================================

st.title("🚌 MOLO SACCO DAILY DASHBOARD")

st.caption(
    "Nakuru ↔ Naivasha Route"
)

# =========================================================
# KPI SECTION
# =========================================================

all_records = records_to_df("daily_earnings")

total_gross = 0
total_exp = 0
total_net = 0

if not all_records.empty:

    if "gross_earnings" not in all_records.columns:
        all_records["gross_earnings"] = 0

    if "total_expenditures" not in all_records.columns:
        all_records["total_expenditures"] = 0

    total_gross = pd.to_numeric(
        all_records["gross_earnings"],
        errors="coerce"
    ).fillna(0).sum()

    total_exp = pd.to_numeric(
        all_records["total_expenditures"],
        errors="coerce"
    ).fillna(0).sum()

    total_net = total_gross - total_exp

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Total Gross Earnings",
        fmt_kes(total_gross)
    )

with c2:
    st.metric(
        "Total Expenditures",
        fmt_kes(total_exp)
    )

with c3:
    st.metric(
        "Total Net Income",
        fmt_kes(total_net)
    )

# =========================================================
# TABS
# =========================================================

tabs = ["📅 Add Transaction", "📋 View Records"]

if role == "admin":
    tabs.append("⚙️ Admin Panel")

tabs = st.tabs(tabs)

# =========================================================
# TAB 1 - ADD TRANSACTION
# =========================================================

with tabs[0]:

    st.subheader("📅 Add Daily Transaction")

    entry_date = st.date_input(
        "Date",
        value=date.today()
    )

    gross = st.number_input(
        "Gross Earnings",
        min_value=0.0,
        step=100.0
    )

    total_exp = st.number_input(
        "Total Expenditures",
        min_value=0.0,
        step=100.0
    )

    net_income = gross - total_exp

    st.info(
        f"Net Income: {fmt_kes(net_income)}"
    )

    if st.button(
        "💾 Save Transaction",
        type="primary"
    ):

        result = add_record(
            "daily_earnings",
            {
                "date": str(entry_date),
                "gross_earnings": gross,
                "total_expenditures": total_exp,
                "net_daily_income": net_income,
                "entered_by": uname
            }
        )

        if result["success"]:

            st.success(
                result["message"]
            )

            st.rerun()

        else:

            st.error(
                result["message"]
            )

# =========================================================
# TAB 2 - VIEW RECORDS
# =========================================================

with tabs[1]:

    st.subheader("📋 Transaction Records")

    df = records_to_df("daily_earnings")

    if df.empty:

        st.info(
            "No records available."
        )

    else:

        required_cols = [
            "_id",
            "date",
            "gross_earnings",
            "total_expenditures",
            "net_daily_income",
            "entered_by"
        ]

        for col in required_cols:

            if col not in df.columns:

                if col == "entered_by":
                    df[col] = "Unknown"

                else:
                    df[col] = 0

        display_df = df[
            [
                "date",
                "gross_earnings",
                "total_expenditures",
                "net_daily_income",
                "entered_by"
            ]
        ].copy()

        display_df.columns = [
            "Date",
            "Gross Earnings",
            "Total Expenditures",
            "Net Income",
            "Entered By"
        ]

        st.dataframe(
            display_df,
            use_container_width=True
        )

# =========================================================
# TAB 3 - ADMIN PANEL
# =========================================================

if role == "admin":

    with tabs[2]:

        st.subheader("⚙️ Admin Panel")

        # =================================================
        # USER MANAGEMENT
        # =================================================

        st.markdown("## 👥 User Management")

        creds = load_credentials()

        users = list(creds.keys())

        if users:

            user_df = pd.DataFrame({
                "Username": users
            })

            st.dataframe(
                user_df,
                use_container_width=True
            )

        else:

            st.info("No users found.")

        # =============================================
        # CREATE USER
        # =============================================

        st.markdown("---")
        st.markdown("### ➕ Create User")

        new_user = st.text_input(
            "Username"
        )

        new_pass = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Create User"
        ):

            ok, msg = register_user(
                new_user,
                new_pass
            )

            if ok:

                st.success(msg)

                st.rerun()

            else:

                st.error(msg)

        # =============================================
        # DELETE USER
        # =============================================

        st.markdown("---")
        st.markdown("### 🗑️ Delete User")

        if users:

            del_user = st.selectbox(
                "Select User",
                users
            )

            if st.button(
                "Delete User"
            ):

                ok, msg = delete_user(
                    del_user
                )

                if ok:

                    st.success(msg)

                    st.rerun()

                else:

                    st.error(msg)

        # =============================================
        # RESET PASSWORD
        # =============================================

        st.markdown("---")
        st.markdown("### 🔑 Reset Password")

        if users:

            reset_user = st.selectbox(
                "Select User To Reset",
                users,
                key="reset_user"
            )

            new_pw = st.text_input(
                "New Password",
                type="password"
            )

            if st.button(
                "Reset Password"
            ):

                ok, msg = change_user_password(
                    reset_user,
                    new_pw
                )

                if ok:

                    st.success(msg)

                else:

                    st.error(msg)

        # =================================================
        # MANAGE TRANSACTIONS
        # =================================================

        st.markdown("---")
        st.markdown("## 🗑️ Manage Transactions")

        tx_df = records_to_df(
            "daily_earnings"
        )

        if tx_df.empty:

            st.info(
                "No transactions available."
            )

        else:

            required_cols = [
                "_id",
                "date",
                "gross_earnings",
                "total_expenditures",
                "net_daily_income",
                "entered_by"
            ]

            for col in required_cols:

                if col not in tx_df.columns:

                    if col == "entered_by":
                        tx_df[col] = "Unknown"

                    else:
                        tx_df[col] = 0

            tx_df["_label"] = (

                tx_df["date"].astype(str)
                + " | "
                + tx_df["entered_by"].astype(str)
                + " | Gross: KES "
                + tx_df["gross_earnings"].astype(str)
            )

            selected = st.selectbox(
                "Select Transaction",
                tx_df["_label"]
            )

            row = tx_df[
                tx_df["_label"] == selected
            ].iloc[0]

            record_id = row["_id"]

            st.markdown(
                "### ✏️ Edit Transaction"
            )

            new_date = st.text_input(
                "Date",
                value=str(row["date"])
            )

            new_gross = st.number_input(
                "Gross Earnings",
                value=float(
                    row["gross_earnings"]
                )
            )

            new_exp = st.number_input(
                "Total Expenditures",
                value=float(
                    row["total_expenditures"]
                )
            )

            new_net = (
                new_gross - new_exp
            )

            st.info(
                f"Net Income: {fmt_kes(new_net)}"
            )

            col1, col2 = st.columns(2)

            # =========================================
            # UPDATE TRANSACTION
            # =========================================

            with col1:

                if st.button(
                    "💾 Update Transaction"
                ):

                    updated_record = {
                        "date": new_date,
                        "gross_earnings": new_gross,
                        "total_expenditures": new_exp,
                        "net_daily_income": new_net,
                        "entered_by": row["entered_by"]
                    }

                    ok = update_record(
                        "daily_earnings",
                        record_id,
                        updated_record
                    )

                    if ok:

                        st.success(
                            "Transaction updated successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Failed to update transaction."
                        )

            # =========================================
            # DELETE TRANSACTION
            # =========================================

            with col2:

                if st.button(
                    "🗑️ Delete Transaction"
                ):

                    ok = delete_record(
                        "daily_earnings",
                        record_id
                    )

                    if ok:

                        st.success(
                            "Transaction deleted successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Failed to delete transaction."
                        )

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "MOLO SACCO Dashboard • Built with Streamlit"
)
