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
    register_user
)

from database import (
    add_record,
    get_records,
    update_record,
    delete_record
)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MOLO SACCO – Daily Earnings",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── AUTH GATE ────────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    render_login_page()
    st.stop()

role = st.session_state.get("role", "user")
uname = st.session_state.get("username", "")

# ── CSS ──────────────────────────────────────────────────────────────────────
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

.net-box h3{
    margin:0 0 6px;
    font-size:.85rem;
    opacity:.9;
    text-transform:uppercase;
}

.net-box h1{
    margin:0;
    font-size:2.2rem;
    font-weight:700;
}

</style>
""", unsafe_allow_html=True)

# ── HELPERS ──────────────────────────────────────────────────────────────────

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

    return df


def to_excel_bytes(sheets):

    buf = BytesIO()

    with pd.ExcelWriter(
        buf,
        engine="openpyxl"
    ) as writer:

        for name, df in sheets.items():

            if not df.empty:

                df.to_excel(
                    writer,
                    sheet_name=name[:31],
                    index=False
                )

    return buf.getvalue()

# ── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:

    badge = (
        "👑 Admin"
        if role == "admin"
        else "👤 User"
    )

    st.markdown(
        f"**{badge}** · `{uname}`"
    )

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        for k in [
            "authenticated",
            "username",
            "role"
        ]:
            st.session_state.pop(k, None)

        st.rerun()

    st.markdown("---")

    st.markdown("**🚌 KBW 066S | MOLO SACCO**")
    st.markdown("Route: Nakuru ↔ Naivasha")
    st.markdown("Owner: Josphat Njuguna Kimani")

# ── HEADER ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
  <h1>🚌 MOLO SACCO – Daily Earnings Dashboard</h1>
  <p>KBW 066S | Nakuru ↔ Naivasha | 2026/2027 Financial Year</p>
</div>
""", unsafe_allow_html=True)

# ── KPI SECTION ──────────────────────────────────────────────────────────────

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

# ── TABS ─────────────────────────────────────────────────────────────────────

tab_labels = [
    "📅 Enter Daily Record",
    "📋 Records & Reports"
]

if role == "admin":
    tab_labels.append("⚙️ Admin")

tabs = st.tabs(tab_labels)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – DAILY ENTRY
# ══════════════════════════════════════════════════════════════════════════════

with tabs[0]:

    st.markdown(
        '<div class="section-header">📅 Enter Daily Record</div>',
        unsafe_allow_html=True
    )

    entry_date = st.date_input(
        "📆 Date",
        value=date.today()
    )

    gross = st.number_input(
        "💰 Gross Earnings (KES)",
        min_value=0.0,
        step=100.0
    )

    total_exp_entry = st.number_input(
        "💸 Total Expenditures (KES)",
        min_value=0.0,
        step=100.0
    )

    net_income = gross - total_exp_entry

    cls = (
        "net-box"
        if net_income >= 0
        else "net-box loss"
    )

    st.markdown(
        f'<div class="{cls}"><h3>Net Daily Income</h3><h1>{fmt_kes(net_income)}</h1></div>',
        unsafe_allow_html=True
    )

    if st.button(
        "💾 Save Daily Record",
        type="primary",
        use_container_width=True
    ):

        result = add_record(
            "daily_earnings",
            {
                "date": str(entry_date),
                "gross_earnings": gross,
                "total_expenditures": total_exp_entry,
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

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – RECORDS
# ══════════════════════════════════════════════════════════════════════════════

with tabs[1]:

    st.markdown(
        '<div class="section-header">📋 Records & Reports</div>',
        unsafe_allow_html=True
    )

    df = records_to_df("daily_earnings")

    if df.empty:

        st.info(
            "No records yet."
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

        df["date"] = pd.to_datetime(df["date"])

        summary = df[
            [
                "date",
                "gross_earnings",
                "total_expenditures",
                "net_daily_income",
                "entered_by"
            ]
        ].copy()

        summary["date"] = summary["date"].dt.strftime("%d %b %Y")

        summary.columns = [
            "Date",
            "Gross Earnings",
            "Total Expenditures",
            "Net Income",
            "Entered By"
        ]

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True
        )

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["gross_earnings"],
                name="Gross"
            )
        )

        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["total_expenditures"],
                name="Expenditures"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["net_daily_income"],
                name="Net Income",
                mode="lines+markers"
            )
        )

        fig.update_layout(
            barmode="group",
            height=400
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – ADMIN
# ══════════════════════════════════════════════════════════════════════════════

if role == "admin":

    with tabs[2]:

        st.markdown(
            '<div class="section-header">⚙️ Admin Panel</div>',
            unsafe_allow_html=True
        )

        # ── USERS ─────────────────────────────────────────

        creds = load_credentials()

        users = list(creds.keys())

        st.markdown("### 👥 Registered Users")

        if users:

            st.dataframe(
                pd.DataFrame({
                    "Username": users
                }),
                use_container_width=True,
                hide_index=True
            )

        # ── CREATE USER ──────────────────────────────────

        st.markdown("---")
        st.markdown("### ➕ Create User")

        nu_user = st.text_input(
            "Username"
        )

        nu_pass = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Create User"
        ):

            ok, msg = register_user(
                nu_user,
                nu_pass
            )

            if ok:

                st.success(msg)

                st.rerun()

            else:

                st.error(msg)

        # ── DELETE USER ──────────────────────────────────

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

        # ── RESET PASSWORD ───────────────────────────────

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

        # ── MANAGE TRANSACTIONS ──────────────────────────

        st.markdown("---")
        st.markdown("### ✏️ Edit / Delete Transactions")

        tx_df = records_to_df(
            "daily_earnings"
        )

        if not tx_df.empty:

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
                "#### Edit Selected Transaction"
            )

            new_gross = st.number_input(
                "Edit Gross Earnings",
                value=float(
                    row["gross_earnings"]
                )
            )

            new_exp = st.number_input(
                "Edit Total Expenditures",
                value=float(
                    row["total_expenditures"]
                )
            )

            new_net = (
                new_gross - new_exp
            )

            st.info(
                f"Net Income: KES {new_net:,.0f}"
            )

            col1, col2 = st.columns(2)

            # UPDATE

            with col1:

                if st.button(
                    "💾 Update Transaction"
                ):

                    updated_record = row.to_dict()

                    updated_record[
                        "gross_earnings"
                    ] = new_gross

                    updated_record[
                        "total_expenditures"
                    ] = new_exp

                    updated_record[
                        "net_daily_income"
                    ] = new_net

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

            # DELETE

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

# ── FOOTER ───────────────────────────────────────────────────────────────────

st.markdown("---")

st.markdown(
    "<center><small>MOLO SACCO · KBW 066S · Nakuru–Naivasha Route</small></center>",
    unsafe_allow_html=True
)
