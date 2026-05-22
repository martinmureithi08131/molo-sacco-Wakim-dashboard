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

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MOLO SACCO – Daily Earnings",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# AUTH GATE
# ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    render_login_page()
    st.stop()

role = st.session_state.get("role", "user")
uname = st.session_state.get("username", "")

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>

.main-header{
    background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
    padding:20px 30px;
    border-radius:12px;
    margin-bottom:20px;
    color:white;
}

.main-header h1{
    margin:0;
    font-size:1.8rem;
}

.main-header p{
    margin:4px 0 0;
    opacity:.75;
    font-size:.9rem;
}

.metric-card{
    padding:20px;
    border-radius:12px;
    color:white;
    text-align:center;
    margin-bottom:8px;
}

.metric-card.blue{
    background:linear-gradient(135deg,#2193b0,#6dd5ed);
}

.metric-card.green{
    background:linear-gradient(135deg,#11998e,#38ef7d);
}

.metric-card.red{
    background:linear-gradient(135deg,#eb3349,#f45c43);
}

.metric-card h3{
    font-size:.8rem;
    margin:0 0 6px;
    opacity:.9;
    text-transform:uppercase;
    letter-spacing:.5px;
}

.metric-card h2{
    font-size:1.5rem;
    margin:0;
    font-weight:700;
}

.section-header{
    border-left:4px solid #667eea;
    padding-left:12px;
    margin:24px 0 12px;
    font-size:1.1rem;
    font-weight:600;
}

.net-box{
    background:linear-gradient(135deg,#11998e,#38ef7d);
    border-radius:12px;
    padding:20px;
    text-align:center;
    color:white;
    margin:16px 0;
}

.net-box.loss{
    background:linear-gradient(135deg,#eb3349,#f45c43);
}

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def fmt_kes(val):

    try:
        return f"KES {float(val):,.0f}"
    except:
        return "KES 0"


def to_excel_bytes(sheets):

    buf = BytesIO()

    valid = {
        k: v for k, v in sheets.items()
        if isinstance(v, pd.DataFrame) and not v.empty
    }

    if not valid:
        valid = {
            "No Data": pd.DataFrame({
                "Info": ["No data available."]
            })
        }

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:

        for name, df in valid.items():

            df.to_excel(
                writer,
                sheet_name=name[:31],
                index=False
            )

    return buf.getvalue()


def records_to_df(table):

    rows = get_records(table)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    return df

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:

    badge = "👑 Admin" if role == "admin" else "👤 User"

    st.markdown(f"### {badge}")
    st.markdown(f"Logged in as: `{uname}`")

    if st.button("🚪 Logout", use_container_width=True):

        for k in [
            "authenticated",
            "username",
            "role"
        ]:
            st.session_state.pop(k, None)

        st.rerun()

    st.markdown("---")

    st.markdown("### 🚌 MOLO SACCO")
    st.markdown("Route: Nakuru ↔ Naivasha")
    st.markdown("Vehicle: KBW 066S")

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🚌 MOLO SACCO – Daily Earnings Dashboard</h1>
    <p>KBW 066S | Nakuru ↔ Naivasha</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────────────────────
all_records = records_to_df("daily_earnings")

total_gross = 0
total_exp = 0
total_net = 0

if not all_records.empty:

    if "gross_earnings" in all_records.columns:

        total_gross = pd.to_numeric(
            all_records["gross_earnings"],
            errors="coerce"
        ).sum()

    if "total_expenditures" in all_records.columns:

        total_exp = pd.to_numeric(
            all_records["total_expenditures"],
            errors="coerce"
        ).sum()

    total_net = total_gross - total_exp

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f'<div class="metric-card blue"><h3>Total Gross Earnings</h3><h2>{fmt_kes(total_gross)}</h2></div>',
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f'<div class="metric-card red"><h3>Total Expenditures</h3><h2>{fmt_kes(total_exp)}</h2></div>',
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f'<div class="metric-card green"><h3>Total Net Income</h3><h2>{fmt_kes(total_net)}</h2></div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
tab_labels = [
    "📅 Enter Daily Record",
    "📋 Records & Reports"
]

if role == "admin":
    tab_labels.append("⚙️ Admin")

tabs = st.tabs(tab_labels)

# ═════════════════════════════════════════════════════════════
# TAB 1 — DAILY RECORD ENTRY
# ═════════════════════════════════════════════════════════════
with tabs[0]:

    st.markdown(
        '<div class="section-header">📅 Enter Daily Record</div>',
        unsafe_allow_html=True
    )

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
            "📆 Date",
            value=date.today()
        )

    with col2:
        gross = st.number_input(
            "💰 Gross Earnings (KES)",
            min_value=0.0,
            step=100.0,
            format="%.2f"
        )

    st.markdown(
        '<div class="section-header">➕ Expenditures</div>',
        unsafe_allow_html=True
    )

    for i, row in enumerate(st.session_state.exp_rows):

        col_a, col_b, col_c = st.columns([3,2,0.6])

        with col_a:

            st.session_state.exp_rows[i]["description"] = st.text_input(
                f"Description #{i+1}",
                value=row["description"],
                key=f"desc_{i}"
            )

        with col_b:

            st.session_state.exp_rows[i]["amount"] = st.number_input(
                f"Amount #{i+1}",
                value=float(row["amount"]),
                min_value=0.0,
                step=50.0,
                format="%.2f",
                key=f"amt_{i}"
            )

        with col_c:

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🗑️", key=f"del_{i}"):

                st.session_state.exp_rows.pop(i)

                st.rerun()

    if st.button("➕ Add Expenditure Item"):

        st.session_state.exp_rows.append({
            "description": "",
            "amount": 0.0
        })

        st.rerun()

    total_exp_entry = sum(
        r["amount"] for r in st.session_state.exp_rows
    )

    net_income = gross - total_exp_entry

    st.markdown(
        f"""
        <div class="net-box">
            <h3>Net Daily Income</h3>
            <h1>{fmt_kes(net_income)}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "💾 Save Daily Record",
        type="primary",
        use_container_width=True
    ):

        exp_list = [
            r for r in st.session_state.exp_rows
            if r["description"].strip()
        ]

        add_record("daily_earnings", {
            "date": str(entry_date),
            "gross_earnings": gross,
            "expenditures": exp_list,
            "total_expenditures": total_exp_entry,
            "net_daily_income": net_income,
            "entered_by": uname
        })

        st.success("Daily record saved successfully.")

        st.session_state.exp_rows = [
            {
                "description": "",
                "amount": 0.0
            }
        ]

        st.rerun()

# ═════════════════════════════════════════════════════════════
# TAB 2 — REPORTS
# ═════════════════════════════════════════════════════════════
with tabs[1]:

    st.markdown(
        '<div class="section-header">📋 Records & Reports</div>',
        unsafe_allow_html=True
    )

    df = records_to_df("daily_earnings")

    if df.empty:

        st.info("No records found.")

    else:

        df["date"] = pd.to_datetime(df["date"])

        for col in [
            "gross_earnings",
            "total_expenditures",
            "net_daily_income"
        ]:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

        # CHART
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df["date"],
            y=df["gross_earnings"],
            name="Gross Earnings"
        ))

        fig.add_trace(go.Bar(
            x=df["date"],
            y=df["total_expenditures"],
            name="Expenditures"
        ))

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["net_daily_income"],
            mode="lines+markers",
            name="Net Income"
        ))

        fig.update_layout(
            barmode="group",
            height=400
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # SUMMARY TABLE
        st.markdown(
            '<div class="section-header">Daily Summary</div>',
            unsafe_allow_html=True
        )

        summary = df[[
            "_id",
            "date",
            "gross_earnings",
            "total_expenditures",
            "net_daily_income",
            "entered_by"
        ]]

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True
        )

        # EXPENDITURE BREAKDOWN
        st.markdown(
            '<div class="section-header">Expenditure Breakdown</div>',
            unsafe_allow_html=True
        )

        exp_rows = []

        for _, record in df.iterrows():

            exp_list = record.get(
                "expenditures",
                []
            )

            if isinstance(exp_list, list):

                for item in exp_list:

                    exp_rows.append({
                        "Date": record["date"],
                        "Description": item.get("description", ""),
                        "Amount": item.get("amount", 0)
                    })

        if exp_rows:

            exp_df = pd.DataFrame(exp_rows)

            st.dataframe(
                exp_df,
                use_container_width=True,
                hide_index=True
            )

            pie = px.pie(
                exp_df,
                names="Description",
                values="Amount",
                hole=0.4
            )

            st.plotly_chart(
                pie,
                use_container_width=True
            )

# ═════════════════════════════════════════════════════════════
# TAB 3 — ADMIN
# ═════════════════════════════════════════════════════════════
if role == "admin":

    with tabs[2]:

        st.markdown(
            '<div class="section-header">⚙️ Admin Panel</div>',
            unsafe_allow_html=True
        )

        creds = load_credentials()

        users = list(creds.keys())

        # USERS
        st.markdown("### 👥 Registered Users")

        if users:

            st.dataframe(
                pd.DataFrame({
                    "Username": users
                }),
                use_container_width=True,
                hide_index=True
            )

        # CREATE USER
        st.markdown("---")
        st.markdown("### ➕ Create User")

        new_user = st.text_input(
            "Username",
            key="new_user"
        )

        new_pw = st.text_input(
            "Password",
            type="password",
            key="new_pw"
        )

        confirm_pw = st.text_input(
            "Confirm Password",
            type="password",
            key="confirm_pw"
        )

        if st.button(
            "Create User",
            type="primary",
            use_container_width=True
        ):

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
        st.markdown("---")
        st.markdown("### 🗑️ Delete User")

        if users:

            selected_user = st.selectbox(
                "Select User",
                users
            )

            if st.button(
                "Delete User",
                use_container_width=True
            ):

                ok, msg = delete_user(selected_user)

                if ok:

                    st.success(msg)

                    st.rerun()

                else:
                    st.error(msg)

        # RESET PASSWORD
        st.markdown("---")
        st.markdown("### 🔑 Reset Password")

        if users:

            reset_user = st.selectbox(
                "Select User",
                users,
                key="reset_user"
            )

            new_password = st.text_input(
                "New Password",
                type="password"
            )

            if st.button(
                "Reset Password",
                use_container_width=True
            ):

                ok, msg = change_user_password(
                    reset_user,
                    new_password
                )

                if ok:
                    st.success(msg)

                else:
                    st.error(msg)

        # EDIT TRANSACTIONS
        st.markdown("---")
        st.markdown("### ✏️ Edit Transactions")

        records_df = records_to_df(
            "daily_earnings"
        )

        if not records_df.empty:

            records_df["display"] = (
                records_df["date"].astype(str)
                + " | Gross: KES "
                + records_df["gross_earnings"].astype(str)
            )

            selected_record = st.selectbox(
                "Select Transaction",
                records_df["display"]
            )

            selected_row = records_df[
                records_df["display"] == selected_record
            ].iloc[0]

            edit_gross = st.number_input(
                "Edit Gross Earnings",
                value=float(
                    selected_row["gross_earnings"]
                ),
                step=100.0
            )

            edit_exp = st.number_input(
                "Edit Total Expenditures",
                value=float(
                    selected_row["total_expenditures"]
                ),
                step=100.0
            )

            new_net = edit_gross - edit_exp

            st.info(
                f"Updated Net Income: {fmt_kes(new_net)}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "💾 Update Transaction",
                    use_container_width=True
                ):

                    ok = update_record(
                        "daily_earnings",
                        selected_row["_id"],
                        {
                            "gross_earnings": edit_gross,
                            "total_expenditures": edit_exp,
                            "net_daily_income": new_net
                        }
                    )

                    if ok:

                        st.success(
                            "Transaction updated successfully."
                        )

                        st.rerun()

                    else:
                        st.error("Update failed.")

            with col2:

                if st.button(
                    "🗑️ Delete Transaction",
                    use_container_width=True
                ):

                    ok = delete_record(
                        "daily_earnings",
                        selected_row["_id"]
                    )

                    if ok:

                        st.success(
                            "Transaction deleted successfully."
                        )

                        st.rerun()

                    else:
                        st.error("Delete failed.")

st.markdown("---")

st.markdown("""
<center>
<small>
MOLO SACCO · KBW 066S · Nakuru ↔ Naivasha Route
</small>
</center>
""", unsafe_allow_html=True)
