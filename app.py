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
    delete_record,
    update_record
)

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="MOLO SACCO",
    page_icon="🚌",
    layout="wide"
)

# =====================================
# AUTH
# =====================================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    render_login_page()
    st.stop()

role = st.session_state["role"]
uname = st.session_state["username"]

# =====================================
# HELPERS
# =====================================

def fmt_kes(x):

    return f"KES {float(x):,.0f}"


def records_to_df():

    rows = get_records("daily_earnings")

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)

# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.success(
        f"Logged in as: {uname}"
    )

    if st.button("🚪 Logout"):

        st.session_state.clear()

        st.rerun()

# =====================================
# TITLE
# =====================================

st.title("🚌 MOLO SACCO Dashboard")

tabs = ["📅 Add Record", "📋 Records"]

if role == "admin":
    tabs.append("⚙️ Admin")

tabs = st.tabs(tabs)

# =====================================
# TAB 1
# =====================================

with tabs[0]:

    st.subheader("📅 Add Daily Record")

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

    net = gross - total_exp

    st.info(
        f"Net Income: {fmt_kes(net)}"
    )

    if st.button(
        "💾 Save Record",
        type="primary"
    ):

        add_record(
            "daily_earnings",
            {
                "date": str(entry_date),
                "gross_earnings": gross,
                "total_expenditures": total_exp,
                "net_daily_income": net,
                "entered_by": uname
            }
        )

        st.success(
            "Record saved successfully."
        )

# =====================================
# TAB 2
# =====================================

with tabs[1]:

    st.subheader("📋 Records")

    df = records_to_df()

    if df.empty:

        st.info("No records found.")

    else:

        st.dataframe(
            df.drop(columns=["_id"]),
            use_container_width=True
        )

# =====================================
# TAB 3 ADMIN
# =====================================

if role == "admin":

    with tabs[2]:

        st.subheader("⚙️ Admin Panel")

        # =============================
        # USERS
        # =============================

        st.markdown("## 👥 User Management")

        creds = load_credentials()

        users = list(creds.keys())

        if users:

            st.dataframe(
                pd.DataFrame({
                    "Users": users
                }),
                use_container_width=True
            )

        # CREATE USER

        with st.expander("➕ Create User"):

            new_user = st.text_input(
                "Username"
            )

            new_pass = st.text_input(
                "Password",
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

        # DELETE USER

        with st.expander("🗑 Delete User"):

            if users:

                del_user = st.selectbox(
                    "Select User",
                    users
                )

                if st.button("Delete User"):

                    ok, msg = delete_user(
                        del_user
                    )

                    if ok:
                        st.success(msg)
                        st.rerun()

                    else:
                        st.error(msg)

        # RESET PASSWORD

        with st.expander("🔑 Reset Password"):

            if users:

                reset_user = st.selectbox(
                    "Select User",
                    users,
                    key="reset"
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

        st.markdown("---")

        # =============================
        # TRANSACTION MANAGEMENT
        # =============================

        st.markdown("## 📝 Manage Transactions")

        tx_df = records_to_df()

        if tx_df.empty:

            st.info("No transactions found.")

        else:

            tx_df["display"] = (
                tx_df["date"].astype(str)
                + " | Gross: "
                + tx_df["gross_earnings"].astype(str)
            )

            selected = st.selectbox(
                "Select Transaction",
                tx_df["display"]
            )

            row = tx_df[
                tx_df["display"] == selected
            ].iloc[0]

            record_id = row["_id"]

            edit_date = st.date_input(
                "Edit Date",
                value=pd.to_datetime(
                    row["date"]
                ).date()
            )

            edit_gross = st.number_input(
                "Edit Gross Earnings",
                value=float(
                    row["gross_earnings"]
                )
            )

            edit_exp = st.number_input(
                "Edit Expenditures",
                value=float(
                    row["total_expenditures"]
                )
            )

            edit_net = (
                edit_gross - edit_exp
            )

            st.info(
                f"Net: {fmt_kes(edit_net)}"
            )

            col1, col2 = st.columns(2)

            # UPDATE

            with col1:

                if st.button(
                    "💾 Update Transaction"
                ):

                    ok = update_record(
                        "daily_earnings",
                        record_id,
                        {
                            "date": str(edit_date),
                            "gross_earnings": edit_gross,
                            "total_expenditures": edit_exp,
                            "net_daily_income": edit_net,
                            "entered_by": row["entered_by"]
                        }
                    )

                    if ok:

                        st.success(
                            "Transaction updated."
                        )

                        st.rerun()

                    else:
                        st.error(
                            "Update failed."
                        )

            # DELETE

            with col2:

                if st.button(
                    "🗑 Delete Transaction"
                ):

                    ok = delete_record(
                        "daily_earnings",
                        record_id
                    )

                    if ok:

                        st.success(
                            "Transaction deleted."
                        )

                        st.rerun()

                    else:
                        st.error(
                            "Delete failed."
                        )
