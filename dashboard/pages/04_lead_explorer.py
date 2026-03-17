"""
04_lead_explorer.py — Interactive lead table with search, score distribution, segments, CSV export.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_DASHBOARD = Path(__file__).resolve().parent.parent
for _p in [str(_ROOT), str(_DASHBOARD)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Lead Explorer | Nidal Zeineldine", page_icon="📊", layout="wide")

from src import config
from components.shared import load_scored_data, page_footer

# ── Data ───────────────────────────────────────────────────────────────────────

df_all = load_scored_data()

# ── Sidebar filters ────────────────────────────────────────────────────────────

st.sidebar.header("Filters")

# Status
statuses = ["All"] + sorted(df_all[config.COL_LEAD_STATUS].dropna().unique().tolist())
sel_status = st.sidebar.selectbox("Lead Status", statuses)

# Segment (A/B/C/D)
if config.COL_LEAD_SEGMENT in df_all.columns:
    segments = ["All"] + sorted(df_all[config.COL_LEAD_SEGMENT].dropna().unique().tolist())
    sel_segment = st.sidebar.selectbox("Segment", segments)
else:
    sel_segment = "All"

# Campaign
campaigns = ["All"] + sorted(df_all[config.COL_CAMPAIGN].dropna().unique().tolist())
sel_campaign = st.sidebar.selectbox("Campaign", campaigns)

# Region
regions = ["All"] + sorted(df_all[config.COL_TARGET_REGION].dropna().unique().tolist())
sel_region = st.sidebar.selectbox("Region", regions)

# Agent
agents = ["All"] + sorted(df_all[config.COL_OWNER].dropna().unique().tolist())
sel_agent = st.sidebar.selectbox("Agent", agents)

# Apply filters
df = df_all.copy()
if sel_status != "All":
    df = df[df[config.COL_LEAD_STATUS] == sel_status]
if sel_segment != "All" and config.COL_LEAD_SEGMENT in df.columns:
    df = df[df[config.COL_LEAD_SEGMENT] == sel_segment]
if sel_campaign != "All":
    df = df[df[config.COL_CAMPAIGN] == sel_campaign]
if sel_region != "All":
    df = df[df[config.COL_TARGET_REGION] == sel_region]
if sel_agent != "All":
    df = df[df[config.COL_OWNER] == sel_agent]

# ── Page header ────────────────────────────────────────────────────────────────

st.title("🔍 Lead Explorer")
st.markdown(f"Showing **{len(df):,}** of {len(df_all):,} leads")

# ── Search box ─────────────────────────────────────────────────────────────────

search = st.text_input(
    "Search by name, email, phone, or campaign",
    placeholder="Type to filter leads...",
)
if search:
    mask = (
        df[config.COL_FIRST_NAME].fillna("").str.contains(search, case=False, regex=False)
        | df[config.COL_LAST_NAME].fillna("").str.contains(search, case=False, regex=False)
        | df[config.COL_EMAIL].fillna("").str.contains(search, case=False, regex=False)
        | df[config.COL_PHONE].astype(str).str.contains(search, case=False, regex=False)
        | df[config.COL_CAMPAIGN].fillna("").str.contains(search, case=False, regex=False)
    )
    df = df[mask]
    st.caption(f"Search '{search}' matched {len(df):,} leads.")

if len(df) == 0:
    st.warning("No leads match the current filters and search.")
    st.stop()

# ── Score distribution + segment breakdown ────────────────────────────────────

dist_left, dist_right = st.columns(2)

with dist_left:
    if config.COL_LEAD_SCORE in df.columns:
        st.subheader("Lead Score Distribution")
        fig_hist = px.histogram(
            df,
            x=config.COL_LEAD_SCORE,
            nbins=20,
            title="Lead Score Distribution",
            labels={config.COL_LEAD_SCORE: "Lead Score"},
            color_discrete_sequence=[config.COLORS["primary"]],
        )
        fig_hist.update_layout(
            plot_bgcolor=config.COLORS["background"],
            paper_bgcolor=config.COLORS["background"],
            font=dict(color=config.COLORS["text"]),
            title_font=dict(color=config.COLORS["primary"]),
            xaxis_title="Lead Score (0–15+)",
            yaxis_title="Number of Leads",
            bargap=0.05,
        )
        # Segment boundary lines
        for threshold, label, color in [
            (8, "A threshold", config.COLORS["accent"]),
            (4, "B threshold", config.COLORS["secondary"]),
            (1, "C threshold", config.COLORS["neutral"]),
        ]:
            fig_hist.add_vline(
                x=threshold,
                line_dash="dash",
                line_color=color,
                annotation_text=label,
                annotation_position="top right",
            )
        st.plotly_chart(fig_hist, use_container_width=True)
        st.caption(
            "Scoring: +5 high-value status, +3 contacted/answered, "
            "+2 verified phone, −3 negative status, −1 slow response."
        )

with dist_right:
    if config.COL_LEAD_SEGMENT in df.columns:
        st.subheader("Segment Breakdown")
        seg_counts = (
            df[config.COL_LEAD_SEGMENT]
            .value_counts()
            .reset_index()
            .rename(columns={config.COL_LEAD_SEGMENT: "Segment", "count": "Leads"})
        )
        # Show segment color coding
        segment_colors = {
            "A - High Value": config.COLORS["accent"],
            "B - Promising": config.COLORS["light_blue"],
            "C - Needs Work": config.COLORS["light_orange"],
            "D - Low Quality": config.COLORS["negative"],
        }
        seg_counts["Color"] = seg_counts["Segment"].map(segment_colors)

        fig_seg = px.bar(
            seg_counts.sort_values("Segment"),
            x="Segment",
            y="Leads",
            title="Leads by Segment",
            color="Segment",
            color_discrete_map=segment_colors,
            text="Leads",
        )
        fig_seg.update_traces(textposition="outside")
        fig_seg.update_layout(
            plot_bgcolor=config.COLORS["background"],
            paper_bgcolor=config.COLORS["background"],
            font=dict(color=config.COLORS["text"]),
            title_font=dict(color=config.COLORS["primary"]),
            showlegend=False,
            xaxis_title="Segment",
            yaxis_title="Number of Leads",
        )
        st.plotly_chart(fig_seg, use_container_width=True)
        st.caption(
            "A = High Value (score ≥8) · B = Promising (4–7) · "
            "C = Needs Work (1–3) · D = Low Quality (≤0)"
        )

st.divider()

# ── Lead table ─────────────────────────────────────────────────────────────────

st.subheader(f"Lead Records ({len(df):,})")

# Choose columns to display
display_cols = [c for c in [
    config.COL_RECORD_ID,
    config.COL_FIRST_NAME,
    config.COL_LAST_NAME,
    config.COL_LEAD_STATUS,
    config.COL_LEAD_SCORE,
    config.COL_LEAD_SEGMENT,
    config.COL_CAMPAIGN,
    config.COL_TARGET_REGION,
    config.COL_OWNER,
    config.COL_CREATE_DATE,
    config.COL_PHONE_COUNTRY,
    config.COL_RESPONSE_HOURS,
    config.COL_CONTACT_ATTEMPTS,
] if c in df.columns]

df_display = df[display_cols].copy()
if config.COL_CREATE_DATE in df_display.columns:
    df_display[config.COL_CREATE_DATE] = pd.to_datetime(df_display[config.COL_CREATE_DATE]).dt.strftime("%Y-%m-%d")

# Column config for Streamlit dataframe
col_cfg = {}
if config.COL_LEAD_SCORE in df_display.columns:
    col_cfg[config.COL_LEAD_SCORE] = st.column_config.NumberColumn("Score", format="%d")
if config.COL_RESPONSE_HOURS in df_display.columns:
    col_cfg[config.COL_RESPONSE_HOURS] = st.column_config.NumberColumn("Response (h)", format="%.1f")

st.dataframe(
    df_display,
    use_container_width=True,
    column_config=col_cfg,
    hide_index=True,
)

# ── CSV Export ─────────────────────────────────────────────────────────────────

st.subheader("Export")

csv_data = df[display_cols].to_csv(index=False).encode("utf-8")

st.download_button(
    label=f"Download {len(df):,} leads as CSV",
    data=csv_data,
    file_name="filtered_leads_export.csv",
    mime="text/csv",
    type="primary",
)
st.caption("Export includes all currently filtered and searched leads.")

page_footer()
