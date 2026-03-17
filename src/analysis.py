"""
analysis.py — Business analysis functions.

Computes summary statistics, funnel breakdowns, campaign comparisons,
response time distributions, and geographic breakdowns.
All functions accept a DataFrame and return a DataFrame or scalar.
"""

import logging

import pandas as pd

from src import config

logger = logging.getLogger(__name__)


def lead_status_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Count leads by status with percentage.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched leads dataframe.

    Returns
    -------
    pd.DataFrame
        Columns: lead_status, count, pct.
    """
    counts = (
        df[config.COL_LEAD_STATUS]
        .value_counts()
        .rename_axis(config.COL_LEAD_STATUS)
        .reset_index(name="count")
    )
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)
    return counts


def funnel_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate leads by funnel stage.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        Columns: funnel_stage, count, pct.
    """
    counts = (
        df[config.COL_FUNNEL_STAGE]
        .value_counts()
        .rename_axis(config.COL_FUNNEL_STAGE)
        .reset_index(name="count")
    )
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)
    return counts


def campaign_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise lead count and qualification rate per campaign.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        Columns: campaign_name, total_leads, qualified_leads, qual_rate_pct.
    """
    positive_statuses = {"Hot Lead", "Qualified", "Future Opportunity", "Contacted"}
    df = df.copy()
    df["_positive"] = df[config.COL_LEAD_STATUS].isin(positive_statuses)
    summary = (
        df.groupby(config.COL_CAMPAIGN)
        .agg(total_leads=(config.COL_RECORD_ID, "count"), positive_leads=("_positive", "sum"))
        .reset_index()
    )
    summary["positive_rate_pct"] = (
        summary["positive_leads"] / summary["total_leads"] * 100
    ).round(1)
    return summary.sort_values("total_leads", ascending=False)


def response_time_stats(df: pd.DataFrame) -> dict:
    """Compute response time summary statistics.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    dict
        mean_hours, median_hours, pct_never_contacted.
    """
    rt = df[config.COL_RESPONSE_HOURS].dropna()
    never_contacted = (df[config.COL_LEAD_STATUS] == "Uncontacted").sum()
    return {
        "mean_hours": round(rt.mean(), 1),
        "median_hours": round(rt.median(), 1),
        "pct_never_contacted": round(never_contacted / len(df) * 100, 1),
    }


def geographic_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Count leads by phone-derived country.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        Columns: phone_country, count, pct.
    """
    counts = (
        df[config.COL_PHONE_COUNTRY]
        .value_counts()
        .rename_axis(config.COL_PHONE_COUNTRY)
        .reset_index(name="count")
    )
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)
    return counts


def region_vs_status(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-tabulate campaign region vs lead status.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        Pivot table: rows=campaign_region, cols=lead_status.
    """
    return pd.crosstab(df[config.COL_CAMPAIGN_REGION], df[config.COL_LEAD_STATUS])


# ── Helper ─────────────────────────────────────────────────────────────────────

def _attempts_numeric(df: pd.DataFrame) -> pd.Series:
    """Extract numeric attempt count from D1/D2/D3 strings (NaN where absent)."""
    return df[config.COL_CONTACT_ATTEMPTS].str.extract(r"(\d)").squeeze().astype(float)


def _quality_flag(df: pd.DataFrame) -> pd.Series:
    """Boolean: funnel stage is Middle or Bottom (contacted / qualified)."""
    return df[config.COL_FUNNEL_STAGE].isin({"Middle", "Bottom"})


def _disq_flag(df: pd.DataFrame) -> pd.Series:
    """Boolean: funnel stage is Negative (disqualified leads)."""
    return df[config.COL_FUNNEL_STAGE] == "Negative"


def _round_pct_cols(result: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Multiply fractional means by 100 and round to 1 dp in-place."""
    for col in cols:
        if col in result.columns:
            result[col] = (result[col] * 100).round(1)
    return result


# ── Public API ─────────────────────────────────────────────────────────────────

def calculate_funnel(df: pd.DataFrame) -> dict:
    """Return lead counts at each funnel stage in pipeline order.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched leads dataframe.

    Returns
    -------
    dict
        Keys are funnel stage names (Top, Middle, Bottom, Negative, Nurture),
        values are integer counts.  Stages with zero leads are included.
    """
    stage_counts = df[config.COL_FUNNEL_STAGE].value_counts().to_dict()
    return {stage: int(stage_counts.get(stage, 0)) for stage in config.FUNNEL_ORDER}


def campaign_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    """Per-campaign performance scorecard.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched leads dataframe.

    Returns
    -------
    pd.DataFrame
        Sorted by lead_count descending. Columns:
        campaign_name, lead_count, contact_rate, quality_rate,
        disqualification_rate, avg_response_time, avg_attempts,
        region_match_rate.
        Rate columns are percentages (0–100). Response time is in hours.
    """
    df = df.copy()
    df["_quality"] = _quality_flag(df)
    df["_disq"] = _disq_flag(df)
    df["_attempts"] = _attempts_numeric(df)

    scorecard = (
        df.groupby(config.COL_CAMPAIGN)
        .agg(
            lead_count=(config.COL_RECORD_ID, "count"),
            contact_rate=(config.COL_WAS_CONTACTED, "mean"),
            quality_rate=("_quality", "mean"),
            disqualification_rate=("_disq", "mean"),
            avg_response_time=(config.COL_RESPONSE_HOURS, "mean"),
            avg_attempts=("_attempts", "mean"),
            region_match_rate=(config.COL_REGION_MATCH, "mean"),
        )
        .reset_index()
    )

    _round_pct_cols(scorecard, ["contact_rate", "quality_rate", "disqualification_rate", "region_match_rate"])
    scorecard["avg_response_time"] = scorecard["avg_response_time"].round(1)
    scorecard["avg_attempts"] = scorecard["avg_attempts"].round(2)

    return scorecard.sort_values("lead_count", ascending=False).reset_index(drop=True)


def agent_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    """Per-agent performance scorecard with best/worst campaign.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched leads dataframe.

    Returns
    -------
    pd.DataFrame
        Sorted by lead_count descending. Columns:
        hubspot_owner, lead_count, contact_rate, quality_rate,
        avg_response_time, avg_attempts, best_campaign, worst_campaign.
        Rate columns are percentages (0–100). Response time is in hours.
        best/worst campaign uses quality_rate among campaigns with ≥3 leads.
    """
    df = df.copy()
    df["_quality"] = _quality_flag(df)
    df["_attempts"] = _attempts_numeric(df)

    scorecard = (
        df.groupby(config.COL_OWNER)
        .agg(
            lead_count=(config.COL_RECORD_ID, "count"),
            contact_rate=(config.COL_WAS_CONTACTED, "mean"),
            quality_rate=("_quality", "mean"),
            avg_response_time=(config.COL_RESPONSE_HOURS, "mean"),
            avg_attempts=("_attempts", "mean"),
        )
        .reset_index()
    )

    # Best / worst campaign per agent (require ≥3 leads for a fair comparison)
    agent_camp = (
        df.groupby([config.COL_OWNER, config.COL_CAMPAIGN])
        .agg(_n=(config.COL_RECORD_ID, "count"), _qr=("_quality", "mean"))
        .reset_index()
    )
    agent_camp = agent_camp[agent_camp["_n"] >= 3]

    if not agent_camp.empty:
        best_idx = agent_camp.groupby(config.COL_OWNER)["_qr"].idxmax()
        worst_idx = agent_camp.groupby(config.COL_OWNER)["_qr"].idxmin()
        best = (
            agent_camp.loc[best_idx, [config.COL_OWNER, config.COL_CAMPAIGN]]
            .rename(columns={config.COL_CAMPAIGN: "best_campaign"})
        )
        worst = (
            agent_camp.loc[worst_idx, [config.COL_OWNER, config.COL_CAMPAIGN]]
            .rename(columns={config.COL_CAMPAIGN: "worst_campaign"})
        )
        scorecard = scorecard.merge(best, on=config.COL_OWNER, how="left")
        scorecard = scorecard.merge(worst, on=config.COL_OWNER, how="left")
    else:
        scorecard["best_campaign"] = pd.NA
        scorecard["worst_campaign"] = pd.NA

    _round_pct_cols(scorecard, ["contact_rate", "quality_rate"])
    scorecard["avg_response_time"] = scorecard["avg_response_time"].round(1)
    scorecard["avg_attempts"] = scorecard["avg_attempts"].round(2)

    return scorecard.sort_values("lead_count", ascending=False).reset_index(drop=True)


def campaign_type_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Compare key metrics grouped by campaign type (Teaser, Lead Generation, Lookalike).

    Parameters
    ----------
    df : pd.DataFrame
        Enriched leads dataframe.

    Returns
    -------
    pd.DataFrame
        Sorted by lead_count descending. Columns:
        campaign_type, lead_count, contact_rate, quality_rate,
        disqualification_rate, avg_response_time, avg_attempts,
        region_match_rate.
    """
    df = df.copy()
    df["_quality"] = _quality_flag(df)
    df["_disq"] = _disq_flag(df)
    df["_attempts"] = _attempts_numeric(df)

    result = (
        df.groupby(config.COL_CAMPAIGN_TYPE)
        .agg(
            lead_count=(config.COL_RECORD_ID, "count"),
            contact_rate=(config.COL_WAS_CONTACTED, "mean"),
            quality_rate=("_quality", "mean"),
            disqualification_rate=("_disq", "mean"),
            avg_response_time=(config.COL_RESPONSE_HOURS, "mean"),
            avg_attempts=("_attempts", "mean"),
            region_match_rate=(config.COL_REGION_MATCH, "mean"),
        )
        .reset_index()
    )

    _round_pct_cols(result, ["contact_rate", "quality_rate", "disqualification_rate", "region_match_rate"])
    result["avg_response_time"] = result["avg_response_time"].round(1)
    result["avg_attempts"] = result["avg_attempts"].round(2)

    return result.sort_values("lead_count", ascending=False).reset_index(drop=True)


def form_version_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Compare key metrics grouped by form version.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched leads dataframe.

    Returns
    -------
    pd.DataFrame
        Sorted by lead_count descending. Columns:
        form_version, lead_count, contact_rate, quality_rate,
        disqualification_rate, avg_response_time, region_match_rate.
    """
    df = df.copy()
    df["_quality"] = _quality_flag(df)
    df["_disq"] = _disq_flag(df)

    result = (
        df.groupby(config.COL_FORM_VERSION)
        .agg(
            lead_count=(config.COL_RECORD_ID, "count"),
            contact_rate=(config.COL_WAS_CONTACTED, "mean"),
            quality_rate=("_quality", "mean"),
            disqualification_rate=("_disq", "mean"),
            avg_response_time=(config.COL_RESPONSE_HOURS, "mean"),
            region_match_rate=(config.COL_REGION_MATCH, "mean"),
        )
        .reset_index()
    )

    _round_pct_cols(result, ["contact_rate", "quality_rate", "disqualification_rate", "region_match_rate"])
    result["avg_response_time"] = result["avg_response_time"].round(1)

    return result.sort_values("lead_count", ascending=False).reset_index(drop=True)


def targeting_accuracy_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-tabulate target region (from form currency) vs actual phone country.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched leads dataframe.

    Returns
    -------
    pd.DataFrame
        Crosstab with target_region as rows, phone_country as columns,
        and a "Total" margin on both axes.  Diagonal cells are in-region matches.
    """
    return pd.crosstab(
        df[config.COL_TARGET_REGION],
        df[config.COL_PHONE_COUNTRY],
        margins=True,
        margins_name="Total",
    )
