import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
from datetime import date, timedelta
from auth import render_login_page, delete_user, change_user_password, load_credentials, register_user
from database import add_record, get_records, update_record, delete_record

st.set_page_config(
    page_title="MOLO SACCO – Daily Earnings",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth Gate ─────────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    render_login_page()
    st.stop()

role  = st.session_state.get("role", "user")
uname = st.session_state.get("username", "")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
        padding:20px 30px;border-radius:12px;margin-bottom:20px;color:white;}
    .main-header h1{margin:0;font-size:1.8rem;}
    .main-header p{margin:4px 0 0;opacity:.75;font-size:.9rem;}
    .metric-card{padding:20px;border-radius:12px;color:white;text-align:center;margin-bottom:8px;}
    .metric-card.blue{background:linear-gradient(135deg,#2193b0,#6dd5ed);}
    .metric-card.green{background:linear-gradient(135deg,#11998e,#38ef7d);}
    .metric-card.red{background:linear-gradient(135deg,#eb3349,#f45c43);}
    .metric-card.purple{background:linear-gradient(135deg,#667eea,#764ba2);}
    .metric-card h3{font-size:.8rem;margin:0 0 6px;opacity:.9;text-transform:uppercase;letter-spacing:.5px;}
    .metric-card h2{font-size:1.5rem;margin:0;font-weight:700;}
    .section-header{border-left:4px solid #667eea;padding-left:12px;
        margin:24px 0 12px;font-size:1.1rem;font-weight:600;}
    .net-box{border-radius:12px;padding:20px;text-align:center;color:white;margin:16px 0;}
    .net-box.profit{background:linear-gradient(135deg,#11998e,#38ef7d);}
    .net-box.loss{background:linear-gradient(135deg,#eb3349,#f45c43);}
    .net-box h3{margin:0 0 6px;font-size:.85rem;opacity:.9;text-transform:uppercase;}
    .net-box h1{margin:0;font-size:2rem;font-weight:700;}
    .week-badge{background:#667eea;color:white;padding:4px 12px;border-radius:20px;font-size:.8rem;font-weight:600;}
    .stDownloadButton>button{background:linear-gradient(135deg,#11998e,#38ef7d);
        color:#fff;border:none;border-radius:8px;padding:8px 18px;font-weight:600;}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_kes(val):
    try: return f"KES {float(val):,.0f}"
    except: return "KES 0"

def to_excel_bytes(sheets):
    buf = BytesIO()
    valid = {k: v for k, v in sheets.items() if isinstance(v, pd.DataFrame) and not v.empty}
    if not valid:
        valid = {"No Data": pd.DataFrame({"Info": ["No data entered yet."]})}
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in valid.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return buf.getvalue()

def records_to_df(table):
    rows = get_records(table)
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows)

def get_week_range(ref_date=None):
    """Returns (monday, sunday) of the week containing ref_date."""
    ref = ref_date or date.today()
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    badge = "👑 Admin" if role == "admin" else "👤 User"
    st.markdown(f"**{badge}** · `{uname}`")
    if st.button("🚪 Logout", use_container_width=True):
        for k in ["authenticated","username","role"]:
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown("---")
    st.markdown("**🚌 KBW 066S | MOLO SACCO**")
    st.markdown("Route: Nakuru ↔ Naivasha")
    st.markdown("Owner: Josphat Njuguna Kimani")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🚌 MOLO SACCO – Daily Earnings Dashboard</h1>
  <p>KBW 066S &nbsp;|&nbsp; Nakuru ↔ Naivasha &nbsp;|&nbsp; 2026/2027 Financial Year</p>
</div>
""", unsafe_allow_html=True)

# ── Load all records ──────────────────────────────────────────────────────────
all_df = records_to_df("daily_earnings")
if not all_df.empty:
    all_df["date"] = pd.to_datetime(all_df["date"])
    for col in ["gross_earnings","total_expenditures","net_daily_income"]:
        if col not in all_df.columns:
            all_df[col] = 0.0
        all_df[col] = pd.to_numeric(all_df[col], errors="coerce").fillna(0)

# ── This week's data ──────────────────────────────────────────────────────────
mon, sun = get_week_range()
if not all_df.empty:
    week_df = all_df[(all_df["date"].dt.date >= mon) & (all_df["date"].dt.date <= sun)]
else:
    week_df = pd.DataFrame()

# ── KPIs (this week) ─────────────────────────────────────────────────────────
week_gross = week_df["gross_earnings"].sum()    if not week_df.empty else 0
week_exp   = week_df["total_expenditures"].sum() if not week_df.empty else 0
week_net   = week_df["net_daily_income"].sum()   if not week_df.empty else 0
week_days  = len(week_df)                        if not week_df.empty else 0

st.markdown(f'<span class="week-badge">📅 This Week: {mon.strftime("%d %b")} – {sun.strftime("%d %b %Y")}</span>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
with c1: st.markdown(f'<div class="metric-card blue"><h3>Week Gross Earnings</h3><h2>{fmt_kes(week_gross)}</h2></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-card red"><h3>Week Expenditures</h3><h2>{fmt_kes(week_exp)}</h2></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-card green"><h3>Week Net Income</h3><h2>{fmt_kes(week_net)}</h2></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-card purple"><h3>Days Recorded</h3><h2>{week_days} / 7</h2></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_labels = ["📅 Enter Daily Record", "📊 This Week", "📋 All Records"]
if role == "admin":
    tab_labels.append("⚙️ Admin")
tabs = st.tabs(tab_labels)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – Enter Daily Record
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-header">📅 Enter Daily Record</div>', unsafe_allow_html=True)

    if "exp_rows" not in st.session_state:
        st.session_state.exp_rows = [{"description": "", "amount": 0.0}]

    col1, col2 = st.columns(2)
    with col1:
        entry_date = st.date_input("📆 Date", value=date.today())
    with col2:
        gross = st.number_input("💰 Gross Earnings (KES)", min_value=0.0, step=100.0, format="%.2f")

    st.markdown('<div class="section-header">➕ Expenditures</div>', unsafe_allow_html=True)
    st.caption("Add each expenditure item with a description and amount.")

    for i, row in enumerate(st.session_state.exp_rows):
        col_a, col_b, col_c = st.columns([3, 2, 0.5])
        with col_a:
            st.session_state.exp_rows[i]["description"] = st.text_input(
                f"Description #{i+1}", value=row["description"],
                placeholder="e.g. Fuel, Driver wage, SACCO fee...",
                key=f"desc_{i}"
            )
        with col_b:
            st.session_state.exp_rows[i]["amount"] = st.number_input(
                f"Amount (KES) #{i+1}", value=float(row["amount"]),
                min_value=0.0, step=50.0, format="%.2f", key=f"amt_{i}"
            )
        with col_c:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{i}", help="Remove"):
                st.session_state.exp_rows.pop(i)
                st.rerun()

    if st.button("➕ Add Expenditure Item"):
        st.session_state.exp_rows.append({"description": "", "amount": 0.0})
        st.rerun()

    total_exp_entry = sum(r["amount"] for r in st.session_state.exp_rows)
    net_income      = gross - total_exp_entry

    st.markdown("<br>", unsafe_allow_html=True)
    ea, eb, ec = st.columns(3)
    with ea: st.markdown(f'<div class="metric-card blue"><h3>Gross Earnings</h3><h2>{fmt_kes(gross)}</h2></div>', unsafe_allow_html=True)
    with eb: st.markdown(f'<div class="metric-card red"><h3>Total Expenditures</h3><h2>{fmt_kes(total_exp_entry)}</h2></div>', unsafe_allow_html=True)
    with ec:
        cls = "net-box profit" if net_income >= 0 else "net-box loss"
        st.markdown(f'<div class="{cls}"><h3>Net Daily Income</h3><h1>{fmt_kes(net_income)}</h1></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Daily Record", type="primary", use_container_width=True):
        if gross <= 0:
            st.error("❌ Please enter a gross earnings amount.")
        elif not any(r["description"].strip() for r in st.session_state.exp_rows):
            st.error("❌ Please add at least one expenditure with a description.")
        else:
            exp_list = [r for r in st.session_state.exp_rows if r["description"].strip()]
            add_record("daily_earnings", {
                "date": str(entry_date),
                "gross_earnings": gross,
                "expenditures": exp_list,
                "total_expenditures": total_exp_entry,
                "net_daily_income": net_income,
                "entered_by": uname,
            })
            st.success("✅ Daily record saved!")
            st.session_state.exp_rows = [{"description": "", "amount": 0.0}]
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – This Week
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown(f'<div class="section-header">📊 This Week\'s Records &nbsp;<span class="week-badge">{mon.strftime("%d %b")} – {sun.strftime("%d %b %Y")}</span></div>', unsafe_allow_html=True)

    if week_df.empty:
        st.info("No records entered for this week yet.")
    else:
        # Chart
        fig = go.Figure()
        fig.add_trace(go.Bar(x=week_df["date"], y=week_df["gross_earnings"],
                             name="Gross Earnings", marker_color="#667eea"))
        fig.add_trace(go.Bar(x=week_df["date"], y=week_df["total_expenditures"],
                             name="Expenditures", marker_color="#eb3349"))
        fig.add_trace(go.Scatter(x=week_df["date"], y=week_df["net_daily_income"],
                                 name="Net Income", mode="lines+markers",
                                 line=dict(color="#38ef7d", width=2.5)))
        fig.update_layout(barmode="group", height=380,
                          title=f"This Week: {mon.strftime('%d %b')} – {sun.strftime('%d %b %Y')}",
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig, use_container_width=True)

        # Weekly summary table
        disp = week_df[["date","gross_earnings","total_expenditures","net_daily_income","entered_by"]].copy()
        disp["date"] = disp["date"].dt.strftime("%A, %d %b %Y")
        disp.columns = ["Date","Gross Earnings (KES)","Total Expenditures (KES)","Net Income (KES)","Entered By"]
        st.dataframe(disp.style.format({
            "Gross Earnings (KES)":     "KES {:,.0f}",
            "Total Expenditures (KES)": "KES {:,.0f}",
            "Net Income (KES)":         "KES {:,.0f}",
        }), use_container_width=True, hide_index=True)

        # Expenditure breakdown for this week
        st.markdown('<div class="section-header">Expenditure Breakdown</div>', unsafe_allow_html=True)
        exp_rows = []
        for _, record in week_df.iterrows():
            exp_list = record.get("expenditures", [])
            if isinstance(exp_list, list):
                for item in exp_list:
                    exp_rows.append({
                        "Date": record["date"].strftime("%d %b %Y"),
                        "Description": item.get("description",""),
                        "Amount (KES)": item.get("amount", 0),
                    })
        if exp_rows:
            exp_bd = pd.DataFrame(exp_rows)
            exp_bd["Amount (KES)"] = pd.to_numeric(exp_bd["Amount (KES)"], errors="coerce").fillna(0)
            col_a, col_b = st.columns([2,1])
            with col_a:
                st.dataframe(exp_bd.style.format({"Amount (KES)":"KES {:,.0f}"}),
                             use_container_width=True, hide_index=True)
            with col_b:
                cat = exp_bd.groupby("Description")["Amount (KES)"].sum().reset_index()
                fig_pie = px.pie(cat, names="Description", values="Amount (KES)",
                                 title="By Category", hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(height=300, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pie, use_container_width=True)

        # Download this week
        st.download_button(
            "⬇️ Download This Week as Excel",
            data=to_excel_bytes({"This Week": disp}),
            file_name=f"week_{mon.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_week"
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – All Records
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="section-header">📋 All Records</div>', unsafe_allow_html=True)

    if all_df.empty:
        st.info("No records yet.")
    else:
        all_df["Month"] = all_df["date"].dt.to_period("M").astype(str)
        months = ["All"] + sorted(all_df["Month"].unique().tolist(), reverse=True)
        sel = st.selectbox("Filter by Month", months, key="all_month")
        view = all_df if sel == "All" else all_df[all_df["Month"] == sel]

        # Totals
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Days",            len(view))
        m2.metric("Total Gross",     fmt_kes(view["gross_earnings"].sum()))
        m3.metric("Total Expenses",  fmt_kes(view["total_expenditures"].sum()))
        m4.metric("Total Net",       fmt_kes(view["net_daily_income"].sum()))

        # Chart
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=view["date"], y=view["gross_earnings"], name="Gross", marker_color="#667eea"))
        fig2.add_trace(go.Bar(x=view["date"], y=view["total_expenditures"], name="Expenditures", marker_color="#eb3349"))
        fig2.add_trace(go.Scatter(x=view["date"], y=view["net_daily_income"],
                                  name="Net", mode="lines+markers", line=dict(color="#38ef7d",width=2)))
        fig2.update_layout(barmode="group", height=360,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           legend=dict(orientation="h",y=-0.25))
        st.plotly_chart(fig2, use_container_width=True)

        # Monthly summary
        st.markdown('<div class="section-header">Monthly Summary</div>', unsafe_allow_html=True)
        monthly = all_df.groupby("Month").agg(
            Days=("date","count"),
            Gross=("gross_earnings","sum"),
            Expenditures=("total_expenditures","sum"),
            Net=("net_daily_income","sum"),
        ).reset_index()
        monthly["Cumulative Net"] = monthly["Net"].cumsum()
        st.dataframe(monthly.style.format({
            "Gross":"KES {:,.0f}","Expenditures":"KES {:,.0f}",
            "Net":"KES {:,.0f}","Cumulative Net":"KES {:,.0f}",
        }), use_container_width=True)

        # Admin: edit / delete records
        if role == "admin":
            st.markdown('<div class="section-header">✏️ Edit or Delete a Record</div>', unsafe_allow_html=True)
            st.caption("Select a record by date to edit or delete it.")

            view_sorted = view.sort_values("date", ascending=False).copy()
            view_sorted["label"] = view_sorted["date"].dt.strftime("%d %b %Y") + \
                                   "  |  Gross: " + view_sorted["gross_earnings"].apply(fmt_kes) + \
                                   "  |  Net: "   + view_sorted["net_daily_income"].apply(fmt_kes)

            selected_label = st.selectbox("Select record", view_sorted["label"].tolist(), key="edit_select")
            selected_row   = view_sorted[view_sorted["label"] == selected_label].iloc[0]
            record_id      = selected_row["_id"]

            action = st.radio("Action", ["✏️ Edit", "🗑️ Delete"], horizontal=True, key="edit_action")

            if action == "🗑️ Delete":
                st.warning(f"Are you sure you want to delete the record for **{selected_row['date'].strftime('%d %b %Y')}**?")
                if st.button("🗑️ Confirm Delete", type="primary"):
                    delete_record("daily_earnings", record_id)
                    st.success("Record deleted.")
                    st.rerun()

            elif action == "✏️ Edit":
                with st.form("edit_form"):
                    st.markdown("**Edit Record**")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        e_date  = st.date_input("Date", value=selected_row["date"].date())
                    with ec2:
                        e_gross = st.number_input("Gross Earnings (KES)",
                                                  value=float(selected_row["gross_earnings"]),
                                                  min_value=0.0, step=100.0)

                    st.markdown("**Expenditures**")
                    existing_exp = selected_row.get("expenditures", [])
                    if not isinstance(existing_exp, list):
                        existing_exp = []

                    e_descs   = []
                    e_amounts = []
                    for j, item in enumerate(existing_exp):
                        ec_a, ec_b = st.columns([3,2])
                        with ec_a:
                            e_descs.append(st.text_input(f"Description #{j+1}",
                                           value=item.get("description",""), key=f"e_desc_{j}"))
                        with ec_b:
                            e_amounts.append(st.number_input(f"Amount #{j+1}",
                                             value=float(item.get("amount",0)),
                                             min_value=0.0, step=50.0, key=f"e_amt_{j}"))

                    if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                        new_exp   = [{"description": d, "amount": a}
                                     for d, a in zip(e_descs, e_amounts) if d.strip()]
                        new_total = sum(i["amount"] for i in new_exp)
                        new_net   = e_gross - new_total
                        update_record("daily_earnings", record_id, {
                            "date":               str(e_date),
                            "gross_earnings":     e_gross,
                            "expenditures":       new_exp,
                            "total_expenditures": new_total,
                            "net_daily_income":   new_net,
                            "entered_by":         selected_row.get("entered_by",""),
                        })
                        st.success("✅ Record updated!")
                        st.rerun()

        # Download
        st.markdown('<div class="section-header">⬇️ Download</div>', unsafe_allow_html=True)
        dl_cols = st.columns(2)
        with dl_cols[0]:
            export = view[["date","gross_earnings","total_expenditures","net_daily_income","entered_by"]].copy()
            export["date"] = export["date"].dt.strftime("%d %b %Y")
            export.columns = ["Date","Gross (KES)","Expenditures (KES)","Net Income (KES)","Entered By"]
            st.download_button("⬇️ Download Daily Summary",
                data=to_excel_bytes({"Daily Summary": export}),
                file_name=f"daily_summary_{sel}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_daily")
        with dl_cols[1]:
            st.download_button("⬇️ Download Full Report",
                data=to_excel_bytes({"Daily Summary": export, "Monthly Summary": monthly}),
                file_name="MOLO_SACCO_full_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_full")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 – Admin Panel
# ══════════════════════════════════════════════════════════════════════════════
if role == "admin":
    with tabs[3]:
        st.markdown('<div class="section-header">⚙️ Admin Panel – User Management</div>', unsafe_allow_html=True)
        creds     = load_credentials()
        all_users = list(creds.keys())

        st.markdown("#### 👥 Registered Users")
        if all_users:
            st.dataframe(pd.DataFrame({"Username": all_users, "Role": ["user"]*len(all_users)}),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No users registered yet.")

        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### ➕ Create New User")
            nu_user  = st.text_input("Username", key="admin_new_user", placeholder="min. 3 chars")
            nu_pass  = st.text_input("Password", type="password", key="admin_new_pass")
            nu_pass2 = st.text_input("Confirm Password", type="password", key="admin_new_pass2")
            if st.button("Create User", type="primary", use_container_width=True):
                if nu_pass != nu_pass2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(nu_user, nu_pass)
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()
        with col_b:
            st.markdown("#### 🗑️ Delete User")
            if all_users:
                del_target = st.selectbox("Select user to delete", all_users, key="del_user")
                if st.button("Delete User", type="secondary", use_container_width=True):
                    ok, msg = delete_user(del_target)
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()
            st.markdown("#### 🔑 Reset Password")
            if all_users:
                reset_target = st.selectbox("Select user", all_users, key="reset_user")
                new_pw = st.text_input("New Password", type="password", key="reset_pw")
                if st.button("Reset Password", use_container_width=True):
                    ok, msg = change_user_password(reset_target, new_pw)
                    st.success(msg) if ok else st.error(msg)

        st.markdown("---")
        st.info("Admin password is set in `auth.py` → `ADMIN_PASSWORD_HASH`.")

st.markdown("---")
st.markdown("<center><small>MOLO SACCO · KBW 066S · Nakuru–Naivasha Route · Built with Streamlit</small></center>",
            unsafe_allow_html=True)
