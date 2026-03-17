"""
shared.py — Shared data loading and sidebar filter helpers for the dashboard.

Import from pages via:
    from components.shared import load_data, load_scored_data
"""

import sys
from pathlib import Path

# Resolve project root: components/ -> dashboard/ -> project root
_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in [str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd
import streamlit as st

from src import config


@st.cache_data(ttl=0)
def load_data() -> pd.DataFrame:
    """Load enriched leads parquet with Streamlit caching.

    Returns
    -------
    pd.DataFrame
        Enriched leads dataframe from data/processed/enriched.parquet.
    """
    df = pd.read_parquet(config.ENRICHED_PARQUET)
    if config.COL_CREATE_DATE in df.columns:
        df[config.COL_CREATE_DATE] = pd.to_datetime(df[config.COL_CREATE_DATE])
    return df


@st.cache_data(ttl=0)
def load_scored_data() -> pd.DataFrame:
    """Load scored leads CSV (includes lead_score + lead_segment) with caching.

    Falls back to scoring enriched.parquet on the fly if the CSV doesn't exist yet.

    Returns
    -------
    pd.DataFrame
        Scored and segmented leads dataframe.
    """
    if config.SCORED_LEADS_CSV.exists():
        df = pd.read_csv(config.SCORED_LEADS_CSV)
        if config.COL_CREATE_DATE in df.columns:
            df[config.COL_CREATE_DATE] = pd.to_datetime(df[config.COL_CREATE_DATE])
        return df

    # Fall back: score on the fly from enriched data
    df = load_data()
    from src.scoring import calculate_lead_score, segment_leads  # noqa: PLC0415
    df = calculate_lead_score(df)
    return segment_leads(df)


def page_footer() -> None:
    """Render the standard dashboard footer on every page."""
    st.divider()
    st.caption(
        "Data: March 9–13 2026  ·  169 leads  ·  9 campaigns  ·  "
        "A.S. Properties, Dubai  ·  Source: HubSpot CRM / Facebook Lead Ads"
    )
