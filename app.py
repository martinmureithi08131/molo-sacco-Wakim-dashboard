import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from datetime import date
from auth import render_login_page, delete_user, change_user_password, load_credentials, register_user
from database import add_record, get_records, update_record

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
    .metric-card h3{font-size:.8rem;margin:0 0 6px;opacity:.9;text-transform:uppercase;letter-spacing:.5px;}
    .metric-card h2{font-size:1.5rem;margin:0;font-weight:700;}
    .section-header{border-left:4px solid #667eea;padding-left:12px;
        margin:24px 0 12px;font-size:1.1rem;font-weight:600;}
    .exp-row{background:#f8f9ff;border:1px solid #e0e4ff;border-radius:10px;padding:12px;margin-bottom:8px;}
    .net-box{background:linear-gradient(135deg,#11998e,#38ef7d);border-radius:12px;
        padding:20px;text-align:center;color:white;margin:16px 0;}
    .net-box h3{margin:0 0 6px;font-size:.85rem;opacity:.9;text-transform:uppercase;}
    .net-box h1{margin:0;font-size:2.2rem;font-weight:700;}
    .net-box.loss{background:linear-gradient(135deg,#eb3349,#f45c43);}
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
    df = pd.DataFrame(rows)
    if "_id" in df.columns: df = df.drop(columns=["_id"])
    return df

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

# ── KPIs ──────────────────────────────────────────────────────────────────────
all_records = records_to_df("daily_earnings")

total_gross = 0
total_exp   = 0
total_net   = 0

if not all_records.empty:
    if "gross_earnings" in all_records.columns:
        total_gross = pd.to_numeric(all_records["gross_earnings"], errors="coerce").sum()
    if "total_expenditures" in all_records.columns:
        total_exp = pd.to_numeric(all_records["total_expenditures"], errors="coerce").sum()
    total_net = total_gross - total_exp

c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="metric-card blue"><h3>Total Gross Earnings</h3><h2>{fmt_kes(total_gross)}</h2></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-card red"><h3>Total Expenditures</h3><h2>{fmt_kes(total_exp)}</h2></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-card green"><h3>Total Net Income</h3><h2>{fmt_kes(total_net)}</h2></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_labels = ["📅 Enter Daily Record", "📋 Records & Reports"]
if role == "admin":
    tab_labels.append("⚙️ Admin")
tabs = st.tabs(tab_labels)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – Enter Daily Record
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-header">📅 Enter Daily Record</div>', unsafe_allow_html=True)

    # ── Initialize expenditure rows in session state
    if "exp_rows" not in st.session_state:
        st.session_state.exp_rows = [{"description": "", "amount": 0.0}]

    # ── Date & Gross Earnings
    col1, col2 = st.columns(2)
    with col1:
        entry_date = st.date_input("📆 Date", value=date.today())
    with col2:
        gross = st.number_input("💰 Gross Earnings (KES)", min_value=0.0, step=100.0, format="%.2f")

    # ── Expenditures Section
    st.markdown('<div class="section-header">➕ Expenditures</div>', unsafe_allow_html=True)
    st.caption("Add each expenditure item with a description and amount.")

    # Render each expenditure row
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
                min_value=0.0, step=50.0, format="%.2f",
                key=f"amt_{i}"
            )
        with col_c:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{i}", help="Remove this row"):
                st.session_state.exp_rows.pop(i)
                st.rerun()

    # Add row button
    if st.button("➕ Add Expenditure Item", use_container_width=False):
        st.session_state.exp_rows.append({"description": "", "amount": 0.0})
        st.rerun()

    # ── Live Net Income Calculation
    total_exp_entry = sum(r["amount"] for r in st.session_state.exp_rows)
    net_income      = gross - total_exp_entry

    st.markdown("<br>", unsafe_allow_html=True)
    ea, eb, ec = st.columns(3)
    with ea: st.markdown(f'<div class="metric-card blue"><h3>Gross Earnings</h3><h2>{fmt_kes(gross)}</h2></div>', unsafe_allow_html=True)
    with eb: st.markdown(f'<div class="metric-card red"><h3>Total Expenditures</h3><h2>{fmt_kes(total_exp_entry)}</h2></div>', unsafe_allow_html=True)
    with ec:
        cls = "net-box" if net_income >= 0 else "net-box loss"
        st.markdown(f'<div class="{cls}"><h3>Net Daily Income</h3><h1>{fmt_kes(net_income)}</h1></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Save Button
    if st.button("💾 Save Daily Record", type="primary", use_container_width=True):
        if gross <= 0:
            st.error("❌ Please enter a gross earnings amount.")
        elif not any(r["description"].strip() for r in st.session_state.exp_rows):
            st.error("❌ Please add at least one expenditure with a description.")
        else:
            # Build expenditure list (filter out blank rows)
            exp_list = [r for r in st.session_state.exp_rows if r["description"].strip()]
            add_record("daily_earnings", {
                "date": str(entry_date),
                "gross_earnings": gross,
                "expenditures": exp_list,           # list of {description, amount}
                "total_expenditures": total_exp_entry,
                "net_daily_income": net_income,
                "entered_by": uname,
            })
            st.success("✅ Daily record saved!")
            # Reset form
            st.session_state.exp_rows = [{"description": "", "amount": 0.0}]
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Records & Reports
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-header">📋 Records & Reports</div>', unsafe_allow_html=True)

    df = records_to_df("daily_earnings")
    if df.empty:
        st.info("No records yet. Enter a daily record in the first tab.")
    else:
        df["date"] = pd.to_datetime(df["date"])
        for col in ["gross_earnings", "total_expenditures", "net_daily_income"]:
            if col not in df.columns:
                df[col] = 0.0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df["Month"] = df["date"].dt.to_period("M").astype(str)

        # Month filter
        months = ["All"] + sorted(df["Month"].unique().tolist(), reverse=True)
        sel = st.selectbox("Filter by Month", months)
        view = df if sel == "All" else df[df["Month"] == sel]

        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Days Recorded",       len(view))
        m2.metric("Total Gross",         fmt_kes(view["gross_earnings"].sum()))
        m3.metric("Total Expenditures",  fmt_kes(view["total_expenditures"].sum()))
        m4.metric("Total Net Income",    fmt_kes(view["net_daily_income"].sum()))

        # Chart
        fig = go.Figure()
        fig.add_trace(go.Bar(x=view["date"], y=view["gross_earnings"],
                             name="Gross Earnings", marker_color="#667eea"))
        fig.add_trace(go.Bar(x=view["date"], y=view["total_expenditures"],
                             name="Expenditures", marker_color="#eb3349"))
        fig.add_trace(go.Scatter(x=view["date"], y=view["net_daily_income"],
                                 name="Net Income", mode="lines+markers",
                                 line=dict(color="#38ef7d", width=2.5)))
        fig.update_layout(
            barmode="group", height=400,
            title="Daily Earnings vs Expenditures",
            xaxis_title="Date", yaxis_title="KES",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.25)
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Detailed records table
        st.markdown('<div class="section-header">Daily Summary Table</div>', unsafe_allow_html=True)
        summary = view[["date","gross_earnings","total_expenditures","net_daily_income","entered_by"]].copy()
        summary["date"] = summary["date"].dt.strftime("%d %b %Y")
        summary.columns = ["Date","Gross Earnings (KES)","Total Expenditures (KES)","Net Daily Income (KES)","Entered By"]
        st.dataframe(summary.style.format({
            "Gross Earnings (KES)":      "KES {:,.0f}",
            "Total Expenditures (KES)":  "KES {:,.0f}",
            "Net Daily Income (KES)":    "KES {:,.0f}",
        }), use_container_width=True, hide_index=True)

        # ── Expenditure breakdown table
        st.markdown('<div class="section-header">Expenditure Breakdown</div>', unsafe_allow_html=True)
        st.caption("All individual expenditure items across selected records.")

        exp_rows = []
        for _, record in view.iterrows():
            exp_list = record.get("expenditures", [])
            if isinstance(exp_list, list):
                for item in exp_list:
                    exp_rows.append({
                        "Date": record["date"].strftime("%d %b %Y"),
                        "Description": item.get("description",""),
                        "Amount (KES)": item.get("amount", 0),
                    })

        if exp_rows:
            exp_breakdown = pd.DataFrame(exp_rows)
            exp_breakdown["Amount (KES)"] = pd.to_numeric(exp_breakdown["Amount (KES)"], errors="coerce").fillna(0)

            # Category totals
            cat_totals = exp_breakdown.groupby("Description")["Amount (KES)"].sum().reset_index()
            cat_totals = cat_totals.sort_values("Amount (KES)", ascending=False)

            col_a, col_b = st.columns([2,1])
            with col_a:
                st.dataframe(exp_breakdown.style.format({"Amount (KES)": "KES {:,.0f}"}),
                             use_container_width=True, hide_index=True)
            with col_b:
                import plotly.express as px
                fig_pie = px.pie(cat_totals, names="Description", values="Amount (KES)",
                                 title="Expenditure Categories", hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expenditure details found.")

        # ── Monthly summary
        st.markdown('<div class="section-header">Monthly Summary</div>', unsafe_allow_html=True)
        monthly = df.groupby("Month").agg(
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

        # ── Downloads
        st.markdown('<div class="section-header">⬇️ Download Reports</div>', unsafe_allow_html=True)
        dcol1, dcol2 = st.columns(2)

        with dcol1:
            tag = sel.replace("-","_") if sel != "All" else "All"
            st.download_button(
                "⬇️ Download Daily Summary as Excel",
                data=to_excel_bytes({"Daily Summary": summary}),
                file_name=f"daily_summary_{tag}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_summary"
            )

        with dcol2:
            full_sheets = {"Daily Summary": summary, "Monthly Summary": monthly}
            if exp_rows:
                full_sheets["Expenditure Breakdown"] = pd.DataFrame(exp_rows)
            st.download_button(
                "⬇️ Download Full Report as Excel",
                data=to_excel_bytes(full_sheets),
                file_name="MOLO_SACCO_full_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_full"
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – Admin Panel
# ══════════════════════════════════════════════════════════════════════════════
if role == "admin":
    with tabs[2]:
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
        st.markdown('<div class="section-header">Edit Transaction</div>', unsafe_allow_html=True)
        st.caption("Select a saved daily record to modify its values.")

        all_tx = get_records("daily_earnings")
        if not all_tx:
            st.info("No transactions saved yet.")
        else:
            tx_labels = {
                f"{r.get('date','?')}  |  Gross: {fmt_kes(r.get('gross_earnings',0))}  |  By: {r.get('entered_by','?')}  [id: {r['_id'][:6]}]": r
                for r in sorted(all_tx, key=lambda x: x.get("date",""), reverse=True)
            }
            selected_label = st.selectbox("Select record to edit", list(tx_labels.keys()), key="edit_tx_select")
            tx = tx_labels[selected_label]

            with st.form("edit_tx_form"):
                st.markdown(f"**Editing record for {tx.get('date','?')}**")
                ec1, ec2 = st.columns(2)
                with ec1:
                    edit_date = st.date_input(
                        "Date",
                        value=pd.to_datetime(tx.get("date", str(date.today()))).date(),
                        key="edit_date")
                with ec2:
                    edit_gross = st.number_input(
                        "Gross Earnings (KES)",
                        value=float(tx.get("gross_earnings", 0)),
                        min_value=0.0, step=100.0, format="%.2f", key="edit_gross")

                st.markdown("**Expenditures**")
                existing_exps = tx.get("expenditures", [])
                if not existing_exps:
                    existing_exps = [{"description": "", "amount": 0.0}]

                edited_exps = []
                for ei, erow in enumerate(existing_exps):
                    fa, fb = st.columns([3, 2])
                    with fa:
                        d = st.text_input(f"Description #{ei+1}", value=erow.get("description",""), key=f"edit_desc_{ei}")
                    with fb:
                        a = st.number_input(f"Amount (KES) #{ei+1}", value=float(erow.get("amount", 0)),
                                            min_value=0.0, step=50.0, format="%.2f", key=f"edit_amt_{ei}")
                    edited_exps.append({"description": d, "amount": a})

                submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

            if submitted:
                valid_exps = [e for e in edited_exps if e["description"].strip()]
                new_total_exp = sum(e["amount"] for e in valid_exps)
                new_net = edit_gross - new_total_exp
                update_record("daily_earnings", tx["_id"], {
                    "date":               str(edit_date),
                    "gross_earnings":     edit_gross,
                    "expenditures":       valid_exps,
                    "total_expenditures": new_total_exp,
                    "net_daily_income":   new_net,
                })
                st.success(f"Record for {edit_date} updated successfully!")
                st.rerun()

        st.markdown("---")
        st.info("Admin password is set in `auth.py` → `ADMIN_PASSWORD_HASH`.")

st.markdown("---")
st.markdown("<center><small>MOLO SACCO · KBW 066S · Nakuru–Naivasha Route · Built with Streamlit</small></center>",
            unsafe_allow_html=True)
