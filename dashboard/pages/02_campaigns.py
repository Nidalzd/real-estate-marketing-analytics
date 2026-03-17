"""
02_campaigns.py — Campaign analysis: scorecard, type radar, targeting heatmap, form versions.
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
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Campaigns | Nidal Zeineldine", page_icon="📊", layout="wide")

from src import analysis, config
from src.visualization import plot_radar
from components.shared import load_data, page_footer

# ── Data ───────────────────────────────────────────────────────────────────────

df_all = load_data()

# ── Sidebar filters ────────────────────────────────────────────────────────────

st.sidebar.header("Filters")

regions = ["All"] + sorted(df_all[config.COL_TARGET_REGION].dropna().unique().tolist())
sel_region = st.sidebar.selectbox("Region", regions)

camp_types = ["All"] + sorted(df_all[config.COL_CAMPAIGN_TYPE].dropna().unique().tolist())
sel_type = st.sidebar.selectbox("Campaign Type", camp_types)

# Apply filters
df = df_all.copy()
if sel_region != "All":
    df = df[df[config.COL_TARGET_REGION] == sel_region]
if sel_type != "All":
    df = df[df[config.COL_CAMPAIGN_TYPE] == sel_type]

# ── Page header ────────────────────────────────────────────────────────────────

st.title("📣 Campaign Performance")
st.markdown(
    f"Showing **{len(df):,}** of {len(df_all):,} leads · "
    "9 campaigns across UAE / Europe / UK / GCC"
)

if len(df) == 0:
    st.warning("No leads match the current filters.")
    st.stop()

# ── Campaign scorecard table ───────────────────────────────────────────────────

st.subheader("Campaign Scorecard")

scorecard = analysis.campaign_scorecard(df)

# Rename for display
display_cols = {
    config.COL_CAMPAIGN: "Campaign",
    "lead_count": "Leads",
    "contact_rate": "Contact Rate %",
    "quality_rate": "Quality Rate %",
    "disqualification_rate": "Disqual. Rate %",
    "avg_response_time": "Avg Response (h)",
    "avg_attempts": "Avg Attempts",
    "region_match_rate": "Region Match %",
}
scorecard_display = scorecard[list(display_cols.keys())].rename(columns=display_cols)

st.dataframe(
    scorecard_display,
    use_container_width=True,
    column_config={
        "Contact Rate %": st.column_config.ProgressColumn(
            "Contact Rate %", min_value=0, max_value=100, format="%.1f%%"
        ),
        "Quality Rate %": st.column_config.ProgressColumn(
            "Quality Rate %", min_value=0, max_value=100, format="%.1f%%"
        ),
        "Region Match %": st.column_config.ProgressColumn(
            "Region Match %", min_value=0, max_value=100, format="%.1f%%"
        ),
    },
    hide_index=True,
)
st.caption(
    "Quality Rate = % leads reaching Contacted, Future Opportunity, Hot Lead, or Qualified status."
)

st.divider()

# ── Campaign type radar + targeting heatmap ────────────────────────────────────

left, right = st.columns(2)

with left:
    st.subheader("Campaign Type Performance Radar")

    type_data = analysis.campaign_type_comparison(df)

    if len(type_data) > 0:
        radar_metrics = ["contact_rate", "quality_rate", "region_match_rate"]
        radar_labels = ["Contact Rate", "Quality Rate", "Region Match"]

        values_dict = {}
        for _, row in type_data.iterrows():
            camp_type = row[config.COL_CAMPAIGN_TYPE]
            values_dict[camp_type] = [row[m] for m in radar_metrics]

        fig_radar = plot_radar(
            categories=radar_labels,
            values_dict=values_dict,
            title="Campaign Type Comparison (0–100 scale)",
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("Not enough data for radar chart with current filters.")

with right:
    st.subheader("Geographic Targeting Accuracy")

    # Cross-tab: target_region vs phone_country (drop Total margins)
    if config.COL_TARGET_REGION in df.columns and config.COL_PHONE_COUNTRY in df.columns:
        acc_matrix = analysis.targeting_accuracy_matrix(df)
        # Remove the margins row/column added by the function
        acc_matrix = acc_matrix.drop(index="Total", errors="ignore").drop(columns="Total", errors="ignore")

        fig_heat = px.imshow(
            acc_matrix,
            text_auto=True,
            color_continuous_scale=[
                [0.0, config.COLORS["surface"]],
                [0.5, config.COLORS["light_blue"]],
                [1.0, config.COLORS["primary"]],
            ],
            title="Target Region vs Actual Phone Country",
            labels=dict(x="Phone Country (Actual)", y="Target Region (Intended)", color="Leads"),
            aspect="auto",
        )
        fig_heat.update_layout(
            plot_bgcolor=config.COLORS["background"],
            paper_bgcolor=config.COLORS["background"],
            font=dict(color=config.COLORS["text"]),
            title_font=dict(color=config.COLORS["primary"]),
            margin=dict(t=60, b=80, l=120),
            xaxis=dict(tickangle=-45),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption(
            "Diagonal = in-region matches (good targeting). "
            "Off-diagonal = geographic mismatch between campaign target and lead origin."
        )
    else:
        st.info("Targeting accuracy data not available.")

st.divider()

# ── Form version trend ────────────────────────────────────────────────────────

st.subheader("Form Version Performance by Day")

if config.COL_FORM_VERSION in df.columns and config.COL_CREATE_DATE in df.columns:
    daily_form = (
        df.assign(_date=pd.to_datetime(df[config.COL_CREATE_DATE]).dt.date)
        .groupby(["_date", config.COL_FORM_VERSION])
        .size()
        .reset_index(name="leads")
    )
    daily_form["_date"] = daily_form["_date"].astype(str)

    if len(daily_form) > 0:
        fig_trend = px.line(
            daily_form,
            x="_date",
            y="leads",
            color=config.COL_FORM_VERSION,
            markers=True,
            title="Daily Lead Volume by Form Version",
            labels={"_date": "Date", "leads": "Leads", config.COL_FORM_VERSION: "Form Version"},
            color_discrete_sequence=config.PALETTE,
        )
        fig_trend.update_layout(
            plot_bgcolor=config.COLORS["background"],
            paper_bgcolor=config.COLORS["background"],
            font=dict(color=config.COLORS["text"]),
            title_font=dict(color=config.COLORS["primary"]),
            xaxis=dict(showgrid=True, gridcolor=config.COLORS["surface"]),
            yaxis=dict(showgrid=True, gridcolor=config.COLORS["surface"]),
            legend_title="Form Version",
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        st.caption(
            "Form version encodes the lead ad creative and audience variant. "
            "AED = UAE market, EUR = Europe, GBP = UK."
        )
    else:
        st.info("No form version data available for current filters.")

    # Form version summary table
    form_summary = analysis.form_version_analysis(df)
    if len(form_summary) > 0:
        st.dataframe(
            form_summary.rename(
                columns={
                    config.COL_FORM_VERSION: "Form Version",
                    "lead_count": "Leads",
                    "contact_rate": "Contact %",
                    "quality_rate": "Quality %",
                    "disqualification_rate": "Disqual. %",
                    "avg_response_time": "Avg Response (h)",
                    "region_match_rate": "Region Match %",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
else:
    st.info("Form version data not available.")

page_footer()
