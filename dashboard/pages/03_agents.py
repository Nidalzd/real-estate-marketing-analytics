"""
03_agents.py — Agent analysis: scorecards, radar, response time, follow-up depth, heatmap.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_DASHBOARD = Path(__file__).resolve().parent.parent
for _p in [str(_ROOT), str(_DASHBOARD)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Agents | Nidal Zeineldine", page_icon="📊", layout="wide")

from src import analysis, config
from src.visualization import plot_box, plot_radar
from components.shared import load_data, page_footer

# ── Data ───────────────────────────────────────────────────────────────────────

df_all = load_data()

# ── Sidebar filters ────────────────────────────────────────────────────────────

st.sidebar.header("Filters")

agents = ["All"] + sorted(df_all[config.COL_OWNER].dropna().unique().tolist())
sel_agent = st.sidebar.selectbox("Agent", agents)

df = df_all.copy()
if sel_agent != "All":
    df = df[df[config.COL_OWNER] == sel_agent]

# ── Page header ────────────────────────────────────────────────────────────────

st.title("👥 Agent Performance")
st.markdown(
    f"Showing **{len(df):,}** of {len(df_all):,} leads · "
    "Response time benchmark: 5 minutes (industry standard)"
)

if len(df) == 0:
    st.warning("No leads match the current filters.")
    st.stop()

# ── Agent scorecard cards ─────────────────────────────────────────────────────

st.subheader("Agent Scorecards")

scorecard = analysis.agent_scorecard(df_all)  # Always use full data for scorecards

n_agents = len(scorecard)
cols = st.columns(min(n_agents, 4))

for i, (_, row) in enumerate(scorecard.iterrows()):
    col_idx = i % len(cols)
    with cols[col_idx]:
        agent_name = str(row[config.COL_OWNER]).split()[-1] if row[config.COL_OWNER] else f"Agent {i+1}"
        with st.container(border=True):
            st.markdown(f"**{row[config.COL_OWNER]}**")
            st.metric("Leads Assigned", int(row["lead_count"]))
            st.metric("Contact Rate", f"{row['contact_rate']:.1f}%")
            st.metric("Quality Rate", f"{row['quality_rate']:.1f}%")
            st.metric("Avg Response", f"{row['avg_response_time']:.1f} h")
            if "best_campaign" in row and row["best_campaign"] is not None:
                st.caption(f"Best campaign: {row['best_campaign']}")

st.divider()

# ── Agent radar + response time box plot ──────────────────────────────────────

left, right = st.columns(2)

with left:
    st.subheader("Agent Performance Radar")

    radar_metrics = ["contact_rate", "quality_rate", "avg_attempts"]
    radar_labels = ["Contact Rate", "Quality Rate", "Avg Attempts (×10)"]

    # Normalize avg_attempts to same scale (×10 so 3 attempts → 30)
    values_dict = {}
    for _, row in scorecard.iterrows():
        name = str(row[config.COL_OWNER])
        values_dict[name] = [
            float(row["contact_rate"]),
            float(row["quality_rate"]),
            float(row["avg_attempts"]) * 10,
        ]

    if len(values_dict) > 0:
        fig_radar = plot_radar(
            categories=radar_labels,
            values_dict=values_dict,
            title="Agent KPI Comparison",
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("Not enough data for radar chart.")

with right:
    st.subheader("Response Time Distribution by Agent")

    rt_data = df[df[config.COL_RESPONSE_HOURS].notna()].copy()
    if len(rt_data) > 0:
        fig_box = plot_box(
            data=rt_data,
            x=config.COL_OWNER,
            y=config.COL_RESPONSE_HOURS,
            title="Response Time by Agent (hours)",
        )
        fig_box.update_layout(
            xaxis_title="Agent",
            yaxis_title="Response Time (hours)",
            xaxis=dict(tickangle=-20),
        )
        st.plotly_chart(fig_box, use_container_width=True)
        st.caption(
            "Industry benchmark: ≤ 5 minutes (0.08 h). "
            "Leads responded to within 1 hour have 7× higher conversion rates."
        )
    else:
        st.info("No response time data available.")

st.divider()

# ── Follow-up depth comparison ────────────────────────────────────────────────

st.subheader("Follow-up Depth by Agent")

if config.COL_CONTACT_ATTEMPTS in df.columns:
    followup_data = (
        df.fillna({config.COL_CONTACT_ATTEMPTS: "None"})
        .groupby([config.COL_OWNER, config.COL_CONTACT_ATTEMPTS])
        .size()
        .reset_index(name="leads")
    )

    attempt_order = ["None", "D1", "D2", "D3"]
    followup_data[config.COL_CONTACT_ATTEMPTS] = followup_data[config.COL_CONTACT_ATTEMPTS].astype(str)

    fig_followup = px.bar(
        followup_data,
        x=config.COL_OWNER,
        y="leads",
        color=config.COL_CONTACT_ATTEMPTS,
        barmode="stack",
        title="Follow-up Attempts Breakdown per Agent",
        labels={
            config.COL_OWNER: "Agent",
            "leads": "Number of Leads",
            config.COL_CONTACT_ATTEMPTS: "Follow-up Day",
        },
        color_discrete_sequence=config.PALETTE,
        category_orders={config.COL_CONTACT_ATTEMPTS: attempt_order},
    )
    fig_followup.update_layout(
        plot_bgcolor=config.COLORS["background"],
        paper_bgcolor=config.COLORS["background"],
        font=dict(color=config.COLORS["text"]),
        title_font=dict(color=config.COLORS["primary"]),
        xaxis=dict(tickangle=-20),
        legend_title="Follow-up Day",
    )
    st.plotly_chart(fig_followup, use_container_width=True)
    st.caption(
        "D1/D2/D3 = Day 1/2/3 follow-up attempts logged in HubSpot notes. "
        "'None' = no structured follow-up recorded."
    )

st.divider()

# ── Agent-campaign heatmap ─────────────────────────────────────────────────────

st.subheader("Lead Distribution: Agent × Campaign")

agent_camp = (
    df.groupby([config.COL_OWNER, config.COL_CAMPAIGN])
    .size()
    .reset_index(name="leads")
)

if len(agent_camp) > 0:
    pivot = agent_camp.pivot_table(
        index=config.COL_OWNER,
        columns=config.COL_CAMPAIGN,
        values="leads",
        fill_value=0,
    )

    fig_heatmap = px.imshow(
        pivot,
        text_auto=True,
        color_continuous_scale=[
            [0.0, config.COLORS["surface"]],
            [0.5, config.COLORS["light_orange"]],
            [1.0, config.COLORS["secondary"]],
        ],
        title="Leads per Agent per Campaign",
        labels=dict(x="Campaign", y="Agent", color="Leads"),
        aspect="auto",
    )
    fig_heatmap.update_layout(
        plot_bgcolor=config.COLORS["background"],
        paper_bgcolor=config.COLORS["background"],
        font=dict(color=config.COLORS["text"]),
        title_font=dict(color=config.COLORS["primary"]),
        margin=dict(t=60, b=100, l=150),
        xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    st.caption(
        "Uneven distribution may indicate workload imbalance or campaign specialization. "
        "Agents assigned too many high-volume campaigns may have slower response times."
    )
else:
    st.info("Not enough data for heatmap.")

page_footer()
