import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
from datetime import date
from bson import ObjectId

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
    update_record
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
}

.metric-card h2{
    font-size:1.5rem;
    margin:0;
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
            df.to_excel(writer, sheet_name=name[:31], index=False)

    return buf.getvalue()


def records_to_df(table):
    rows = get_records(table)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if "_id" in df.columns:
        df["_id"] = df["_id"].astype(str)

    return df

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:

    badge = "👑 Admin" if role == "admin" else "👤 User"

    st.markdown(f"### {badge}")
    st.markdown(f"Logged in as: `{uname}`")

    if st.button("🚪 Logout", use_container_width=True):
        for k in ["authenticated", "username", "role"]:
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
    <p>Nakuru ↔ Naivasha Route</p>
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

    total_gross = pd.to_numeric(
        all_records["gross_earnings"],
        errors="coerce"
    ).sum()

    total_exp = pd.to_numeric(
        all_records["total_expenditures"],
        errors="coerce"
    ).sum()

    total_net = total_gross - total_exp

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f'<div class="metric-card blue"><h3>Total Gross</h3><h2>{fmt_kes(total_gross)}</h2></div>',
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f'<div class="metric-card red"><h3>Total Expenses</h3><h2>{fmt_kes(total_exp)}</h2></div>',
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f'<div class="metric-card green"><h3>Total Net</h3><h2>{fmt_kes(total_net)}</h2></div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
tab_labels = [
    "📅 Enter Daily Record",
    "📋 Reports"
]

if role == "admin":
    tab_labels.append("⚙️ Admin")

tabs = st.tabs(tab_labels)

# ═════════════════════════════════════════════════════════════
# TAB 1
# ═════════════════════════════════════════════════════════════
with tabs[0]:

    st.markdown(
        '<div class="section-header">📅 Enter Daily Record</div>',
        unsafe_allow_html=True
    )

    if "exp_rows" not in st.session_state:
        st.session_state.exp_rows = [
            {"description": "", "amount": 0.0}
        ]

    col1, col2 = st.columns(2)

    with col1:
        entry_date = st.date_input(
            "Date",
            value=date.today()
        )

    with col2:
        gross = st.number_input(
            "Gross Earnings (KES)",
            min_value=0.0,
            step=100.0
        )

    st.markdown(
        '<div class="section-header">➕ Expenditures</div>',
        unsafe_allow_html=True
    )

    for i, row in enumerate(st.session_state.exp_rows):

        a, b, c = st.columns([3, 2, 0.5])

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

            if st.button("🗑️", key=f"del_{i}"):

                st.session_state.exp_rows.pop(i)
                st.rerun()

    if st.button("➕ Add Expenditure"):

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
            "entered_by": uname,
        })

        st.success("Record saved successfully.")

        st.session_state.exp_rows = [
            {"description": "", "amount": 0.0}
        ]

        st.rerun()

# ═════════════════════════════════════════════════════════════
# TAB 2
# ═════════════════════════════════════════════════════════════
with tabs[1]:

    st.markdown(
        '<div class="section-header">📋 Reports</div>',
        unsafe_allow_html=True
    )

    df = records_to_df("daily_earnings")

    if df.empty:
        st.info("No records available.")

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

        summary = df[[
            "date",
            "gross_earnings",
            "total_expenditures",
            "net_daily_income",
            "entered_by"
        ]]

        st.dataframe(
            summary,
            use_container_width=True
        )

# ═════════════════════════════════════════════════════════════
# TAB 3 - ADMIN
# ═════════════════════════════════════════════════════════════
if role == "admin":

    with tabs[2]:

        st.markdown(
            '<div class="section-header">⚙️ Admin Panel</div>',
            unsafe_allow_html=True
        )

        creds = load_credentials()

        all_users = list(creds.keys())

        # ─────────────────────────────────────────
        # USERS
        # ─────────────────────────────────────────
        st.markdown("## 👥 Users")

        if all_users:

            st.dataframe(
                pd.DataFrame({
                    "Username": all_users
                }),
                use_container_width=True,
                hide_index=True
            )

        # ─────────────────────────────────────────
        # CREATE USER
        # ─────────────────────────────────────────
        st.markdown("## ➕ Create User")

        new_user = st.text_input(
            "Username",
            key="new_user"
        )

        new_pass = st.text_input(
            "Password",
            type="password",
            key="new_pass"
        )

        confirm_pass = st.text_input(
            "Confirm Password",
            type="password",
            key="confirm_pass"
        )

        if st.button(
            "Create User",
            type="primary"
        ):

            if new_pass != confirm_pass:
                st.error("Passwords do not match.")

            else:
                ok, msg = register_user(
                    new_user,
                    new_pass
                )

                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        # ─────────────────────────────────────────
        # DELETE USER
        # ─────────────────────────────────────────
        st.markdown("## 🗑️ Delete User")

        if all_users:

            del_user = st.selectbox(
                "Select User",
                all_users
            )

            if st.button("Delete User"):

                ok, msg = delete_user(del_user)

                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        # ─────────────────────────────────────────
        # RESET PASSWORD
        # ─────────────────────────────────────────
        st.markdown("## 🔑 Reset Password")

        if all_users:

            reset_user = st.selectbox(
                "User",
                all_users,
                key="reset_user"
            )

            new_pw = st.text_input(
                "New Password",
                type="password"
            )

            if st.button("Reset Password"):

                ok, msg = change_user_password(
                    reset_user,
                    new_pw
                )

                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        # ─────────────────────────────────────────
        # EDIT TRANSACTIONS
        # ─────────────────────────────────────────
        st.markdown("---")
        st.markdown("## ✏️ Edit Transactions")

        records_df = records_to_df("daily_earnings")

        if not records_df.empty:

            records_df["display"] = (
                records_df["date"].astype(str)
                + " | Gross: KES "
                + records_df["gross_earnings"].astype(str)
            )

            selected = st.selectbox(
                "Select Transaction",
                records_df["display"]
            )

            selected_row = records_df[
                records_df["display"] == selected
            ].iloc[0]

            edit_date = st.date_input(
                "Edit Date",
                value=pd.to_datetime(
                    selected_row["date"]
                )
            )

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

            edit_net = edit_gross - edit_exp

            st.info(
                f"Net Income: {fmt_kes(edit_net)}"
            )

            if st.button(
                "💾 Update Transaction",
                type="primary"
            ):

                ok = update_record(
                    "daily_earnings",
                    selected_row["_id"],
                    {
                        "date": str(edit_date),
                        "gross_earnings": edit_gross,
                        "total_expenditures": edit_exp,
                        "net_daily_income": edit_net,
                    }
                )

                if ok:
                    st.success(
                        "Transaction updated successfully."
                    )
                    st.rerun()

                else:
                    st.error("No changes made.")

st.markdown("---")

st.markdown("""
<center>
<small>
MOLO SACCO · KBW 066S · Nakuru–Naivasha Route
</small>
</center>
""", unsafe_allow_html=True)
