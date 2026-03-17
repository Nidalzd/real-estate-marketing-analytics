"""
dashboard/app.py — Streamlit multi-page dashboard entry point (home page).

Run with:
    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Make src and dashboard importable
_ROOT = Path(__file__).resolve().parent.parent
_DASHBOARD = Path(__file__).resolve().parent
for _p in [str(_ROOT), str(_DASHBOARD)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st

st.set_page_config(
    page_title="Nidal Zeineldine | RE Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src import config  # noqa: E402
from components.shared import page_footer  # noqa: E402

# ── Sidebar ────────────────────────────────────────────────────────────────────

st.sidebar.title("📊 Nidal Zeineldine | Data Analytics")
st.sidebar.markdown("---")
st.sidebar.markdown("**Client:** A.S. Properties, Dubai")
st.sidebar.markdown("**Dataset:** Week 2 Campaign Performance")
st.sidebar.markdown("**Period:** March 9–13, 2026")
st.sidebar.markdown("**Leads:** 169 | **Campaigns:** 9")
st.sidebar.markdown("---")
st.sidebar.markdown("**Navigate using the pages above ↑**")

# ── Professional header banner ─────────────────────────────────────────────────

st.markdown(
    f"""
    <div style="
        background: linear-gradient(135deg, {config.COLORS['primary']} 0%, {config.COLORS['light_blue']} 100%);
        padding: 2rem 2.5rem;
        border-radius: 0.75rem;
        margin-bottom: 1.5rem;
        color: white;
    ">
        <div style="font-size: 0.85rem; font-weight: 600; letter-spacing: 0.1em;
                    text-transform: uppercase; opacity: 0.8; margin-bottom: 0.4rem;">
            A.S. Properties · Dubai · Portfolio Analytics
        </div>
        <h1 style="margin: 0; color: white; font-size: 2.1rem; font-weight: 700; line-height: 1.2;">
            Real Estate Marketing Analytics
        </h1>
        <p style="margin: 0.4rem 0 0 0; opacity: 0.85; font-size: 1rem; font-weight: 500; letter-spacing: 0.02em;">
            by Nidal Zeineldine
        </p>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.05rem; font-weight: 400;">
            Facebook Lead Campaign Performance — Week 2, March 9–13 2026
        </p>
        <p style="margin: 0.3rem 0 0 0; opacity: 0.7; font-size: 0.9rem;">
            169 leads &nbsp;·&nbsp; 9 campaigns &nbsp;·&nbsp; UAE / Europe / UK / GCC markets
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Highlight KPIs ─────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Leads", "169",          help="Facebook Lead Ads across all campaigns, March 9–13 2026")
col2.metric("Avg Response Time", "18.6 h", delta="-13.6 h vs benchmark", delta_color="inverse",
            help="Industry benchmark is 5 minutes. Slow response is the #1 conversion killer.")
col3.metric("No Answer Rate", "57%",        help="57% of leads never picked up the phone — the dominant outcome.")
col4.metric("Never Contacted", "18%",       delta="31 leads", delta_color="off",
            help="31 leads were never called at all — pure lost opportunity.")

st.divider()

# ── Page directory ─────────────────────────────────────────────────────────────

st.subheader("Dashboard Pages")

_pages = [
    ("📊", "Overview",       "KPI cards · Lead funnel · Status distribution · Daily volume · Date / campaign / agent filters"),
    ("📣", "Campaigns",      "Campaign scorecard table · Type radar · Geographic targeting accuracy · Form version trends"),
    ("👥", "Agents",         "Agent scorecards · Performance radar · Response-time box plots · Follow-up depth · Agent × Campaign heatmap"),
    ("🔍", "Lead Explorer",  "Full lead table · Free-text search · Score histogram · Segment breakdown · CSV export"),
]

left_col, right_col = st.columns(2)
for i, (icon, name, description) in enumerate(_pages):
    col = left_col if i % 2 == 0 else right_col
    with col:
        with st.container(border=True):
            st.markdown(f"#### {icon} {name}")
            st.markdown(f"<small style='color: #555;'>{description}</small>", unsafe_allow_html=True)

page_footer()
