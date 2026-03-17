"""
01_overview.py — Campaign overview: KPIs, funnel, status distribution, daily volume.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_DASHBOARD = Path(__file__).resolve().parent.parent
for _p in [str(_ROOT), str(_DASHBOARD)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Overview | Nidal Zeineldine", page_icon="📊", layout="wide")

from src import analysis, config
from src.visualization import plot_funnel, plot_donut
from components.shared import load_data, page_footer

# ── Data ───────────────────────────────────────────────────────────────────────

df_all = load_data()

# ── Sidebar filters ────────────────────────────────────────────────────────────

st.sidebar.header("Filters")

# Date range
dates = pd.to_datetime(df_all[config.COL_CREATE_DATE]).dt.date
min_date, max_date = dates.min(), dates.max()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Filter leads by the date they were created in HubSpot.",
)

# Campaign
campaigns = ["All"] + sorted(df_all[config.COL_CAMPAIGN].dropna().unique().tolist())
sel_campaign = st.sidebar.selectbox("Campaign", campaigns, help="Filter to a specific Facebook ad campaign.")

# Agent
agents = ["All"] + sorted(df_all[config.COL_OWNER].dropna().unique().tolist())
sel_agent = st.sidebar.selectbox("Agent", agents, help="Filter to leads assigned to a specific sales agent.")

# Apply filters
df = df_all.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    df = df[pd.to_datetime(df[config.COL_CREATE_DATE]).dt.date.between(date_range[0], date_range[1])]
if sel_campaign != "All":
    df = df[df[config.COL_CAMPAIGN] == sel_campaign]
if sel_agent != "All":
    df = df[df[config.COL_OWNER] == sel_agent]

# ── Page header ────────────────────────────────────────────────────────────────

st.title("📊 Campaign Overview")
st.markdown(
    f"Showing **{len(df):,}** of {len(df_all):,} leads · "
    "March 9–13, 2026 · A.S. Properties Facebook campaigns"
)

if len(df) == 0:
    st.warning("No leads match the current filters.")
    st.stop()

# ── KPI cards ─────────────────────────────────────────────────────────────────

st.subheader("Key Performance Indicators")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total = len(df)
contact_rate = df[config.COL_WAS_CONTACTED].mean() * 100 if config.COL_WAS_CONTACTED in df.columns else 0.0
qual_statuses = {"Hot Lead", "Qualified", "Future Opportunity"}
qual_rate = df[config.COL_LEAD_STATUS].isin(qual_statuses).mean() * 100
avg_rt = df[config.COL_RESPONSE_HOURS].dropna().mean()
no_answer_pct = df[config.COL_LEAD_STATUS].eq("No Answer").mean() * 100

with kpi1:
    st.metric(
        "Total Leads",
        f"{total:,}",
        help="Total number of Facebook Lead Ad submissions in the selected date range and filters.",
    )
with kpi2:
    st.metric(
        "Contact Rate",
        f"{contact_rate:.1f}%",
        delta=f"{contact_rate - 43:.1f}% vs 43% baseline",
        help=(
            "Percentage of leads where the sales team successfully reached the prospect. "
            "Includes any response beyond 'No Answer' or 'Uncontacted'. "
            "Industry average for real estate cold outreach is ~43%."
        ),
    )
with kpi3:
    st.metric(
        "Qualification Rate",
        f"{qual_rate:.1f}%",
        help=(
            "Percentage of leads that reached Hot Lead, Qualified, or Future Opportunity status. "
            "These are leads with genuine purchase intent confirmed by an agent. "
            "Lower values indicate audience mismatch or poor follow-up."
        ),
    )
with kpi4:
    st.metric(
        "Avg Response Time",
        f"{avg_rt:.1f} h",
        delta=f"{avg_rt - 0.083:.1f} h vs 5-min benchmark",
        delta_color="inverse",
        help=(
            "Average hours between lead creation and first agent contact. "
            "Industry benchmark: ≤ 5 minutes (0.083 h). "
            "Leads contacted within 5 min are 21× more likely to qualify. "
            "This dataset averages 18.6 h — 224× slower than benchmark."
        ),
    )

st.divider()

# ── Funnel + Donut ─────────────────────────────────────────────────────────────

left, right = st.columns(2)

with left:
    st.subheader("Lead Funnel")
    funnel_counts = analysis.calculate_funnel(df)
    stages = list(funnel_counts.keys())
    counts = list(funnel_counts.values())
    fig_funnel = plot_funnel(stages=stages, counts=counts, title="Lead Pipeline Stages")
    st.plotly_chart(fig_funnel, use_container_width=True)
    st.caption(
        f"{no_answer_pct:.0f}% of leads stall at 'No Answer' (Top funnel). "
        "Only ~10% reach a qualified or hot lead stage."
    )

with right:
    st.subheader("Lead Status Distribution")
    status_data = analysis.lead_status_distribution(df)
    fig_donut = plot_donut(
        labels=status_data[config.COL_LEAD_STATUS].tolist(),
        values=status_data["count"].tolist(),
        title="Lead Status Breakdown",
    )
    st.plotly_chart(fig_donut, use_container_width=True)
    st.caption(
        "Dominant outcome: No Answer. Negative statuses (Junk/Unqualified/Not Interested) "
        "represent wasted acquisition spend."
    )

st.divider()

# ── Daily lead volume ─────────────────────────────────────────────────────────

st.subheader("Daily Lead Volume")

daily = (
    df.assign(_date=pd.to_datetime(df[config.COL_CREATE_DATE]).dt.date)
    .groupby("_date")
    .size()
    .reset_index(name="leads")
)
daily["_date"] = daily["_date"].astype(str)

fig_daily = go.Figure(
    go.Bar(
        x=daily["_date"],
        y=daily["leads"],
        marker_color=config.COLORS["primary"],
        text=daily["leads"],
        textposition="outside",
    )
)
fig_daily.update_layout(
    title="Leads Received per Day",
    xaxis_title="Date",
    yaxis_title="Number of Leads",
    plot_bgcolor=config.COLORS["background"],
    paper_bgcolor=config.COLORS["background"],
    font=dict(color=config.COLORS["text"]),
    title_font=dict(color=config.COLORS["primary"]),
    margin=dict(t=60, b=50),
)
st.plotly_chart(fig_daily, use_container_width=True)
st.caption(
    "Data spans only 5 days — avoid reading trend significance into day-over-day fluctuations."
)

st.divider()

# ── Download Summary CSV ───────────────────────────────────────────────────────

st.subheader("Download Summary Report")

# Build summary: KPIs + status breakdown + campaign top-line
never_contacted = int(df[config.COL_LEAD_STATUS].eq("Uncontacted").sum())

kpi_rows = [
    ("Total Leads",             str(total)),
    ("Contact Rate",            f"{contact_rate:.1f}%"),
    ("Qualification Rate",      f"{qual_rate:.1f}%"),
    ("No Answer Rate",          f"{no_answer_pct:.1f}%"),
    ("Avg Response Time (h)",   f"{avg_rt:.1f}"),
    ("Never Contacted Leads",   str(never_contacted)),
    ("Date Range (from)",       str(df[config.COL_CREATE_DATE].min())[:10]),
    ("Date Range (to)",         str(df[config.COL_CREATE_DATE].max())[:10]),
]

status_dist = analysis.lead_status_distribution(df)
status_rows = [
    (f"Status: {row[config.COL_LEAD_STATUS]}", f"{row['count']} ({row['pct']}%)")
    for _, row in status_dist.iterrows()
]

camp_perf = analysis.campaign_scorecard(df)[
    [config.COL_CAMPAIGN, "lead_count", "contact_rate", "quality_rate", "avg_response_time"]
]
camp_rows = [
    (
        f"Campaign: {row[config.COL_CAMPAIGN]}",
        f"{int(row['lead_count'])} leads, {row['contact_rate']:.1f}% contact, "
        f"{row['quality_rate']:.1f}% quality, {row['avg_response_time']:.1f}h response",
    )
    for _, row in camp_perf.iterrows()
]

all_rows = (
    [("--- KEY METRICS ---", "")]
    + kpi_rows
    + [("", ""), ("--- STATUS BREAKDOWN ---", "")]
    + status_rows
    + [("", ""), ("--- CAMPAIGN SUMMARY ---", "")]
    + camp_rows
)

summary_csv = (
    pd.DataFrame(all_rows, columns=["Metric", "Value"])
    .to_csv(index=False)
    .encode("utf-8")
)

dl_col, info_col = st.columns([1, 3])
with dl_col:
    st.download_button(
        label="Download Summary CSV",
        data=summary_csv,
        file_name="campaign_summary.csv",
        mime="text/csv",
        type="primary",
        help="Exports KPIs, status breakdown, and campaign performance for the current filter selection.",
    )
with info_col:
    st.markdown(
        f"Exports **{len(kpi_rows)} KPIs**, "
        f"**{len(status_rows)} status categories**, and "
        f"**{len(camp_rows)} campaigns** for the current filter selection."
    )

page_footer()
