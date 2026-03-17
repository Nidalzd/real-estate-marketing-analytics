---
name: streamlit-dashboard
description: Use this skill when building, editing, debugging, or running the Streamlit dashboard. Triggers on any mention of dashboard, Streamlit, app.py, dashboard pages, interactive filters, KPI cards, or when the dashboard crashes or looks wrong. Also use when adding new pages or modifying dashboard layout.
---

# Streamlit Dashboard Skill

## Architecture

```
dashboard/
├── app.py                    # Main entry point with sidebar nav
├── pages/
│   ├── 01_overview.py        # KPI cards + funnel + status donut
│   ├── 02_campaigns.py       # Campaign comparison + type analysis
│   ├── 03_agents.py          # Agent scorecards + radar + response time
│   └── 04_lead_explorer.py   # Searchable lead table + score distribution
└── components/
    └── shared.py             # Reusable UI components (KPI card, filters)
```

## Running the Dashboard

```bash
cd real-estate-marketing-analytics
streamlit run dashboard/app.py
```

## App.py Template

```python
import streamlit as st

st.set_page_config(
    page_title="Real Estate Marketing Analytics",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
st.sidebar.title("🏠 RE Analytics")
st.sidebar.markdown("---")
st.sidebar.markdown("**Data:** Week 2 Campaign Performance")
st.sidebar.markdown("**Period:** March 9-13, 2026")
```

## Data Loading Pattern

Every page loads data the same way:

```python
import sys
sys.path.insert(0, '.')  # Project root
import pandas as pd
from src.config import PATHS, COLORS

@st.cache_data
def load_data():
    return pd.read_parquet(PATHS['enriched'])

df = load_data()
```

## Sidebar Filters Pattern

```python
def apply_filters(df):
    """Standard sidebar filters used across pages."""
    with st.sidebar:
        st.header("Filters")

        # Campaign filter
        campaigns = ['All'] + sorted(df['campaign_name'].unique().tolist())
        selected_campaign = st.selectbox("Campaign", campaigns)
        if selected_campaign != 'All':
            df = df[df['campaign_name'] == selected_campaign]

        # Agent filter
        agents = ['All'] + sorted(df['contact_owner'].unique().tolist())
        selected_agent = st.selectbox("Agent", agents)
        if selected_agent != 'All':
            df = df[df['contact_owner'] == selected_agent]

        # Region filter
        regions = ['All'] + sorted(df['target_region'].unique().tolist())
        selected_region = st.selectbox("Region", regions)
        if selected_region != 'All':
            df = df[df['target_region'] == selected_region]

    return df
```

## KPI Card Component

```python
def kpi_card(label, value, delta=None, delta_color="normal"):
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)

# Usage in columns
col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Total Leads", len(df))
with col2:
    contact_rate = df['was_contacted'].mean() * 100
    kpi_card("Contact Rate", f"{contact_rate:.1f}%")
with col3:
    qual_rate = df[df['lead_status'].isin(['Qualified','Hot Lead'])].shape[0] / len(df) * 100
    kpi_card("Qualification Rate", f"{qual_rate:.1f}%")
with col4:
    avg_rt = df['response_time_hours'].mean()
    kpi_card("Avg Response Time", f"{avg_rt:.1f}h")
```

## Common Issues

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: src` | Run from project root: `streamlit run dashboard/app.py` |
| Charts not showing | Use `st.plotly_chart(fig, use_container_width=True)` |
| Slow loading | Add `@st.cache_data` on data loading functions |
| Filters reset on interaction | Use `st.session_state` for filter persistence |
| Page not appearing | File must be in `dashboard/pages/` and start with a number |
