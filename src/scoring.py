"""
scoring.py — Rule-based lead scoring pipeline.

Assigns an additive point score to each lead based on observable signals,
then bins each lead into an A/B/C/D segment tier.

Score components
----------------
  +2  verified_phone       — form used a verified-numbers audience
  +3  phone_answered       — status is not No Answer or Uncontacted
  +1  region_match         — phone country matches campaign target region
  +1  contact_D2           — at least a D2 follow-up attempt recorded
  +1  contact_D3           — at least a D3 follow-up attempt recorded
  +3  contacted_status     — lead reached Contacted / Future Opportunity / Hot / Qualified
  +5  high_value_status    — lead is Hot Lead, Qualified, or Future Opportunity
  -3  negative_status      — lead is Junk Lead or Unqualified
  -1  slow_response        — first response took more than 24 hours
  -1  language_barrier     — note mentions a language barrier

Segments
--------
  A - High Value   score >= 8
  B - Promising    score  4–7
  C - Needs Work   score  1–3
  D - Low Quality  score <= 0

Public API
----------
  calculate_lead_score(df)  -> DataFrame   (adds lead_score + 10 breakdown columns)
  segment_leads(df)         -> DataFrame   (adds lead_segment column)
  run_scoring_pipeline()    -> DataFrame   (full pipeline, saves scored_leads.csv)
"""

import logging

import pandas as pd

from src import config

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

_CONTACTED_OR_BETTER = {"Contacted", "Future Opportunity", "Hot Lead", "Qualified"}
_HIGH_VALUE_STATUSES  = {"Hot Lead", "Qualified", "Future Opportunity"}
_NEGATIVE_STATUSES    = {"Junk Lead", "Unqualified"}
_UNANSWERED_STATUSES  = {"No Answer", "Uncontacted"}

# Patterns that suggest a language barrier in the note text
_LANGUAGE_BARRIER_RE = (
    r"language barrier|no english|doesn.t speak|arabic only"
    r"|لا يتكلم|barrier|no english|language issue"
)

# Score-component column names (visible in output CSV)
_SCORE_COLS = [
    "score_verified_phone",
    "score_phone_answered",
    "score_region_match",
    "score_contact_D2",
    "score_contact_D3",
    "score_contacted_status",
    "score_high_value_status",
    "score_negative_status",
    "score_slow_response",
    "score_language_barrier",
]


# ── Core scoring function ──────────────────────────────────────────────────────

def calculate_lead_score(df: pd.DataFrame) -> pd.DataFrame:
    """Apply rule-based scoring to each lead and add score breakdown columns.

    Reads the following enriched columns:
      has_verified_number, lead_status, region_match, contact_attempts,
      response_time_hours, associated_note.

    Adds ten ``score_*`` component columns and a ``lead_score`` total column.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched dataframe (output of features.engineer_features).

    Returns
    -------
    pd.DataFrame
        Same dataframe with lead_score and ten score_* columns appended.
        Previous lead_score / lead_quality_score columns are preserved.
    """
    df = df.copy()

    # +2  verified phone audience
    df["score_verified_phone"] = (
        df.get(config.COL_HAS_VERIFIED_NUMBER, pd.Series(False, index=df.index))
        .fillna(False)
        .astype(int) * 2
    )

    # +3  phone was answered (not stuck at No Answer / Uncontacted)
    df["score_phone_answered"] = (
        ~df[config.COL_LEAD_STATUS].isin(_UNANSWERED_STATUSES)
    ).astype(int) * 3

    # +1  phone country matches campaign target region
    df["score_region_match"] = (
        df.get(config.COL_REGION_MATCH, pd.Series(False, index=df.index))
        .fillna(False)
        .astype(int)
    )

    # +1 for D2, +1 for D3 (each additional follow-up day earns a point)
    attempts = df.get(config.COL_CONTACT_ATTEMPTS, pd.Series(None, index=df.index))
    df["score_contact_D2"] = attempts.isin(["D2", "D3"]).astype(int)
    df["score_contact_D3"] = (attempts == "D3").astype(int)

    # +3  reached Contacted or a better pipeline stage
    df["score_contacted_status"] = (
        df[config.COL_LEAD_STATUS].isin(_CONTACTED_OR_BETTER)
    ).astype(int) * 3

    # +5  high-value status (Hot Lead / Qualified / Future Opportunity)
    df["score_high_value_status"] = (
        df[config.COL_LEAD_STATUS].isin(_HIGH_VALUE_STATUSES)
    ).astype(int) * 5

    # -3  negative outcome (Junk / Unqualified)
    df["score_negative_status"] = (
        df[config.COL_LEAD_STATUS].isin(_NEGATIVE_STATUSES)
    ).astype(int) * -3

    # -1  slow first response (> 24 h)
    rt = df.get(config.COL_RESPONSE_HOURS, pd.Series(float("nan"), index=df.index))
    df["score_slow_response"] = ((rt > 24) & rt.notna()).astype(int) * -1

    # -1  language barrier mentioned in note
    note_col = df.get(
        config.COL_ASSOCIATED_NOTE, pd.Series("", index=df.index)
    ).fillna("")
    df["score_language_barrier"] = (
        note_col.str.contains(_LANGUAGE_BARRIER_RE, case=False, regex=True)
    ).astype(int) * -1

    # Total
    df[config.COL_LEAD_SCORE] = df[_SCORE_COLS].sum(axis=1).astype(int)

    logger.info(
        "Scoring complete — mean: %.2f, max: %d, min: %d",
        df[config.COL_LEAD_SCORE].mean(),
        df[config.COL_LEAD_SCORE].max(),
        df[config.COL_LEAD_SCORE].min(),
    )
    return df


# ── Segmentation ───────────────────────────────────────────────────────────────

def segment_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Assign A/B/C/D segment tier based on lead_score.

    Segment thresholds
    ------------------
    A - High Value   : score >= 8
    B - Promising    : score  4–7
    C - Needs Work   : score  1–3
    D - Low Quality  : score <= 0

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a ``lead_score`` column (run calculate_lead_score first).

    Returns
    -------
    pd.DataFrame
        Same dataframe with ``lead_segment`` column appended.
    """
    if config.COL_LEAD_SCORE not in df.columns:
        raise ValueError("lead_score column not found — run calculate_lead_score() first.")

    def _tier(score: int) -> str:
        if score >= 8:
            return "A - High Value"
        if score >= 4:
            return "B - Promising"
        if score >= 1:
            return "C - Needs Work"
        return "D - Low Quality"

    df[config.COL_LEAD_SEGMENT] = df[config.COL_LEAD_SCORE].apply(_tier)

    dist = df[config.COL_LEAD_SEGMENT].value_counts().to_dict()
    logger.info("Segment distribution: %s", dist)
    return df


# ── Pipeline orchestrator ──────────────────────────────────────────────────────

def run_scoring_pipeline(save: bool = True) -> pd.DataFrame:
    """Load enriched.parquet, score all leads, segment, export scored_leads.csv.

    Output CSV is sorted by lead_score descending and includes all score
    component columns so every decision is auditable.

    Parameters
    ----------
    save : bool
        If True, write output to SCORED_LEADS_CSV path in config.

    Returns
    -------
    pd.DataFrame
        Scored and segmented dataframe.
    """
    df = pd.read_parquet(config.ENRICHED_PARQUET)
    df = calculate_lead_score(df)
    df = segment_leads(df)

    # Sort: highest score first, then alphabetically by segment for ties
    df = df.sort_values(
        [config.COL_LEAD_SCORE, config.COL_LEAD_SEGMENT],
        ascending=[False, True],
    ).reset_index(drop=True)

    if save:
        # Put identity + score cols first for readability
        priority_cols = [
            config.COL_RECORD_ID,
            config.COL_FIRST_NAME,
            config.COL_LAST_NAME,
            config.COL_LEAD_STATUS,
            config.COL_LEAD_SCORE,
            config.COL_LEAD_SEGMENT,
            *_SCORE_COLS,
        ]
        remaining = [c for c in df.columns if c not in priority_cols]
        df_out = df[priority_cols + remaining]
        df_out.to_csv(config.SCORED_LEADS_CSV, index=False)
        logger.info("Saved scored leads -> %s", config.SCORED_LEADS_CSV)

    return df
