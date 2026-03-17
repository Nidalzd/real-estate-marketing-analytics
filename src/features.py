"""
features.py — Feature engineering pipeline.

Reads cleaned.parquet, adds 17 derived columns, saves enriched.parquet + enriched.csv.

Derived columns (in pipeline order):
  phone_country_code      — numeric calling code parsed from phone_number
  phone_country           — country name mapped from calling code
  campaign_type           — Teaser / Lead Generation / Lookalike from campaign_name
  response_time_hours     — hours between create_date and last_activity_date
  funnel_stage            — Top / Middle / Bottom / Negative / Nurture from lead_status
  contact_attempts        — D1 / D2 / D3 tag from associated_note text
  form_currency           — AED / EUR / GBP / USD extracted from recent_conversion
  target_region           — UAE / Europe / UK / International from form_currency
  was_contacted           — True if lead_status != 'Uncontacted'
  form_version            — version string (V6, V7.1.1, V8.3) from recent_conversion
  has_verified_number     — True if 'verified numbers' in recent_conversion
  is_arabic_form          — True if Arabic script detected in note or form name
  region_match            — True if phone country region matches target_region
  funnel_stage_weight     — numeric weight: Bottom=4, Middle=3, Top=2, Nurture=1, Negative=0
  create_hour             — integer hour (0-23) from create_date (UTC)
  create_day_name         — day name (Monday…Sunday) from create_date (UTC)
  lead_quality_score      — 0-100 composite score
"""

import logging
import re

import numpy as np
import pandas as pd
import phonenumbers

from src import config

logger = logging.getLogger(__name__)


# ── Phone features ─────────────────────────────────────────────────────────────

def extract_phone_country_code(phone: str) -> int | None:
    """Parse a phone number string and return its country calling code.

    Parameters
    ----------
    phone : str
        Digits-only phone number without leading '+'.

    Returns
    -------
    int or None
        Calling code (e.g. 971) or None if unparseable.
    """
    if not phone or pd.isna(phone):
        return None
    try:
        parsed = phonenumbers.parse("+" + str(phone))
        return parsed.country_code
    except phonenumbers.NumberParseException:
        return None


def add_phone_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add phone_country_code and phone_country columns.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_PHONE not in df.columns:
        return df
    df[config.COL_PHONE_COUNTRY_CODE] = df[config.COL_PHONE].apply(
        extract_phone_country_code
    )
    df[config.COL_PHONE_COUNTRY] = df[config.COL_PHONE_COUNTRY_CODE].map(
        config.PHONE_COUNTRY_CODES
    )
    return df


# ── Campaign features ──────────────────────────────────────────────────────────

def extract_campaign_region(name: str) -> str:
    """Infer campaign region from campaign name keywords.

    Parameters
    ----------
    name : str
        Campaign name (from Original Source Drill-Down 2).

    Returns
    -------
    str
        Region label or 'Unknown'.
    """
    if not name or pd.isna(name):
        return "Unknown"
    lower = name.lower()
    for keyword, region in config.CAMPAIGN_REGION_KEYWORDS.items():
        if keyword in lower:
            return region
    return "Unknown"


def extract_campaign_type(name: str) -> str:
    """Infer campaign type from campaign name keywords.

    Parameters
    ----------
    name : str
        Campaign name (from Original Source Drill-Down 2).

    Returns
    -------
    str
        Type label or 'Unknown'.
    """
    if not name or pd.isna(name):
        return "Unknown"
    lower = name.lower()
    for keyword, ctype in config.CAMPAIGN_TYPE_KEYWORDS.items():
        if keyword in lower:
            return ctype
    return "Unknown"


def add_campaign_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add campaign_region and campaign_type columns.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_CAMPAIGN not in df.columns:
        return df
    df[config.COL_CAMPAIGN_REGION] = df[config.COL_CAMPAIGN].apply(extract_campaign_region)
    df[config.COL_CAMPAIGN_TYPE]   = df[config.COL_CAMPAIGN].apply(extract_campaign_type)
    return df


# ── Response time ──────────────────────────────────────────────────────────────

def add_response_time(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate response_time_hours between create_date and last_activity_date.

    Negative values (activity before create) are set to NaN.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_CREATE_DATE not in df.columns or config.COL_LAST_ACTIVITY not in df.columns:
        return df
    delta = df[config.COL_LAST_ACTIVITY] - df[config.COL_CREATE_DATE]
    hours = delta.dt.total_seconds() / 3600
    df[config.COL_RESPONSE_HOURS] = hours.where(hours >= 0, other=np.nan)
    return df


# ── Funnel stage ───────────────────────────────────────────────────────────────

def add_funnel_stage(df: pd.DataFrame) -> pd.DataFrame:
    """Map lead_status to funnel_stage using FUNNEL_STAGES mapping.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_LEAD_STATUS not in df.columns:
        return df
    df[config.COL_FUNNEL_STAGE] = (
        df[config.COL_LEAD_STATUS]
        .map(config.FUNNEL_STAGES)
        .fillna("Unknown")
    )
    return df


# ── Contact attempts (D1/D2/D3) ───────────────────────────────────────────────

def extract_contact_attempt(note: str) -> str | None:
    """Extract the highest D-day tag from a note text string.

    Scans for D1, D2, D3 patterns (case-insensitive, optional space before colon).
    Returns the highest day found so that a note mentioning D2 follow-up
    counts as D2 even if it references a prior D1 attempt.

    Parameters
    ----------
    note : str
        Free-text note from associated_note column.

    Returns
    -------
    str or None
        'D1', 'D2', 'D3', or None if no tag found.
    """
    if not note or pd.isna(note):
        return None
    # Matches: D1, D2, D3, D 1, D 2, Day 1, day 1, day 2, etc.
    matches = re.findall(r"\b[Dd](?:ay)?\s*([123])\b", str(note))
    if not matches:
        return None
    return "D" + max(matches)   # return highest day mentioned


def add_contact_attempts(df: pd.DataFrame) -> pd.DataFrame:
    """Add contact_attempts column (D1/D2/D3) from associated_note text.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_ASSOCIATED_NOTE not in df.columns:
        return df
    df[config.COL_CONTACT_ATTEMPTS] = df[config.COL_ASSOCIATED_NOTE].apply(
        extract_contact_attempt
    )
    return df


# ── Form currency ──────────────────────────────────────────────────────────────

def extract_form_currency(form_name: str) -> str | None:
    """Extract ISO currency code from a Facebook Lead Ad form name.

    The form name (recent_conversion column) encodes the target market currency,
    e.g. '... - AED' for UAE leads or '... - EUR - verified numbers' for Europe.

    Parameters
    ----------
    form_name : str
        Value from the recent_conversion column.

    Returns
    -------
    str or None
        Currency code (AED, EUR, GBP, SAR, USD) or None if not found.
    """
    if not form_name or pd.isna(form_name):
        return None
    currencies = "|".join(config.FORM_CURRENCY_TO_REGION.keys())
    match = re.search(rf"\b({currencies})\b", str(form_name))
    return match.group(1) if match else None


def add_form_currency(df: pd.DataFrame) -> pd.DataFrame:
    """Add form_currency column extracted from recent_conversion.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_RECENT_CONVERSION not in df.columns:
        return df
    df[config.COL_FORM_CURRENCY] = df[config.COL_RECENT_CONVERSION].apply(
        extract_form_currency
    )
    return df


# ── Target region ──────────────────────────────────────────────────────────────

def add_target_region(df: pd.DataFrame) -> pd.DataFrame:
    """Add target_region column mapped from form_currency.

    Falls back to campaign_region if form_currency is null.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_FORM_CURRENCY not in df.columns:
        return df
    currency_region = df[config.COL_FORM_CURRENCY].map(config.FORM_CURRENCY_TO_REGION)
    if config.COL_CAMPAIGN_REGION in df.columns:
        df[config.COL_TARGET_REGION] = currency_region.fillna(df[config.COL_CAMPAIGN_REGION])
    else:
        df[config.COL_TARGET_REGION] = currency_region.fillna("Unknown")
    return df


# ── Lead quality score ─────────────────────────────────────────────────────────

# Points by lead status
_STATUS_SCORES: dict[str, int] = {
    "Qualified":              100,
    "Hot Lead":                80,
    "Future Opportunity":      60,
    "Contacted":               40,
    "Newsletter Subscription": 30,
    "No Answer":               10,
    "Uncontacted":              5,
    "Not Interested":           0,
    "Unqualified":              0,
    "Junk Lead":                0,
}

# Bonus by campaign type
_CAMPAIGN_TYPE_BONUS: dict[str, int] = {
    "Lead Generation": 10,
    "Lookalike":        5,
    "Teaser":           2,
    "Unknown":          0,
}

# Bonus by phone country (proxy for buyer intent quality)
_COUNTRY_BONUS: dict[str, int] = {
    "UAE":          15,
    "Saudi Arabia": 10,
    "UK":           10,
    "India":         5,
    "Ukraine":       5,
}


def _score_lead(row: pd.Series) -> float:
    """Compute a 0-100 quality score for a single lead row.

    Components:
      - Lead status base score (0-100)
      - Campaign type bonus (0-10)
      - Phone country bonus (0-15)
      - Response time bonus (0-10, faster = better)

    Parameters
    ----------
    row : pd.Series

    Returns
    -------
    float
        Score capped at 100.
    """
    score = _STATUS_SCORES.get(row.get(config.COL_LEAD_STATUS, ""), 0)
    score += _CAMPAIGN_TYPE_BONUS.get(row.get(config.COL_CAMPAIGN_TYPE, "Unknown"), 0)
    score += _COUNTRY_BONUS.get(row.get(config.COL_PHONE_COUNTRY, ""), 0)

    rt = row.get(config.COL_RESPONSE_HOURS)
    if rt is not None and not np.isnan(float(rt)) and rt > 0:
        if rt <= 1:
            score += 10
        elif rt <= 5:
            score += 5
        elif rt <= 24:
            score += 2

    return float(min(score, 100))


def add_lead_quality_score(df: pd.DataFrame) -> pd.DataFrame:
    """Add lead_quality_score column (0-100 composite score).

    Depends on: lead_status, campaign_type, phone_country, response_time_hours.
    Must be called after all upstream feature functions.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df[config.COL_LEAD_QUALITY_SCORE] = df.apply(_score_lead, axis=1)
    return df


# ── Was contacted ─────────────────────────────────────────────────────────────

def add_was_contacted(df: pd.DataFrame) -> pd.DataFrame:
    """Add was_contacted boolean: True if lead_status is not 'Uncontacted'.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_LEAD_STATUS not in df.columns:
        return df
    df[config.COL_WAS_CONTACTED] = df[config.COL_LEAD_STATUS] != "Uncontacted"
    return df


# ── Form version ───────────────────────────────────────────────────────────────

def extract_form_version(form_name: str) -> str | None:
    """Extract the version tag (e.g. V6, V7.1.1, V8.3) from a form name.

    Parameters
    ----------
    form_name : str
        Value from the recent_conversion column.

    Returns
    -------
    str or None
        Version string such as 'V8.3' or None if not found.
    """
    if not form_name or pd.isna(form_name):
        return None
    match = re.search(r"\b(V\d+(?:\.\d+)*)\b", str(form_name), re.IGNORECASE)
    return match.group(1).upper() if match else None


def add_form_version(df: pd.DataFrame) -> pd.DataFrame:
    """Add form_version column parsed from recent_conversion.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_RECENT_CONVERSION not in df.columns:
        return df
    df[config.COL_FORM_VERSION] = df[config.COL_RECENT_CONVERSION].apply(
        extract_form_version
    )
    return df


# ── Has verified number ────────────────────────────────────────────────────────

def add_has_verified_number(df: pd.DataFrame) -> pd.DataFrame:
    """Add has_verified_number boolean: True if 'verified numbers' in form name.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_RECENT_CONVERSION not in df.columns:
        return df
    df[config.COL_HAS_VERIFIED_NUMBER] = (
        df[config.COL_RECENT_CONVERSION]
        .fillna("")
        .str.contains("verified numbers", case=False, regex=False)
    )
    return df


# ── Is Arabic form ─────────────────────────────────────────────────────────────

def add_is_arabic_form(df: pd.DataFrame) -> pd.DataFrame:
    """Add is_arabic_form boolean: True if Arabic script detected in note or form name.

    Checks associated_note and recent_conversion for any Unicode Arabic characters
    (U+0600–U+06FF).

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    arabic_pattern = re.compile(r"[\u0600-\u06FF]")

    def _has_arabic(val) -> bool:
        if pd.isna(val):
            return False
        return bool(arabic_pattern.search(str(val)))

    note_arabic = df[config.COL_ASSOCIATED_NOTE].apply(_has_arabic) \
        if config.COL_ASSOCIATED_NOTE in df.columns \
        else pd.Series(False, index=df.index)

    form_arabic = df[config.COL_RECENT_CONVERSION].apply(_has_arabic) \
        if config.COL_RECENT_CONVERSION in df.columns \
        else pd.Series(False, index=df.index)

    df[config.COL_IS_ARABIC_FORM] = note_arabic | form_arabic
    return df


# ── Region match ───────────────────────────────────────────────────────────────

def add_region_match(df: pd.DataFrame) -> pd.DataFrame:
    """Add region_match boolean: True if phone country region equals target_region.

    Maps phone_country to a region using PHONE_COUNTRY_TO_REGION, then compares
    against the campaign's target_region.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_PHONE_COUNTRY not in df.columns or config.COL_TARGET_REGION not in df.columns:
        return df
    phone_region = df[config.COL_PHONE_COUNTRY].map(config.PHONE_COUNTRY_TO_REGION)
    df[config.COL_REGION_MATCH] = phone_region == df[config.COL_TARGET_REGION]
    return df


# ── Funnel stage weight ────────────────────────────────────────────────────────

def add_funnel_stage_weight(df: pd.DataFrame) -> pd.DataFrame:
    """Add funnel_stage_weight numeric column mapped from funnel_stage.

    Weights: Bottom=4, Middle=3, Top=2, Nurture=1, Negative=0, Unknown=0.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_FUNNEL_STAGE not in df.columns:
        return df
    df[config.COL_FUNNEL_STAGE_WEIGHT] = (
        df[config.COL_FUNNEL_STAGE]
        .map(config.FUNNEL_STAGE_WEIGHTS)
        .fillna(0)
        .astype(int)
    )
    return df


# ── Create date features ───────────────────────────────────────────────────────

def add_create_date_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add create_hour (int) and create_day_name (str) from create_date (UTC).

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    if config.COL_CREATE_DATE not in df.columns:
        return df
    dt = df[config.COL_CREATE_DATE]
    df[config.COL_CREATE_HOUR]     = dt.dt.hour
    df[config.COL_CREATE_DAY_NAME] = dt.dt.day_name()
    return df


# ── Pipeline orchestrator ──────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature engineering steps to a cleaned dataframe.

    Adds 17 derived columns and drops the intermediate campaign_region column
    (target_region supersedes it as the canonical geographic target field).

    Parameters
    ----------
    df : pd.DataFrame
        Output of clean_dataset().

    Returns
    -------
    pd.DataFrame
        Enriched dataframe with exactly 17 derived columns added.
    """
    df = add_phone_features(df)
    df = add_campaign_features(df)       # adds campaign_region (intermediate) + campaign_type
    df = add_response_time(df)
    df = add_funnel_stage(df)
    df = add_contact_attempts(df)
    df = add_form_currency(df)
    df = add_target_region(df)           # uses campaign_region as fallback, then drop it
    df = add_was_contacted(df)
    df = add_form_version(df)
    df = add_has_verified_number(df)
    df = add_is_arabic_form(df)
    df = add_region_match(df)
    df = add_funnel_stage_weight(df)
    df = add_create_date_features(df)
    df = add_lead_quality_score(df)

    # Drop intermediate column not in the canonical 17
    df = df.drop(columns=[config.COL_CAMPAIGN_REGION], errors="ignore")
    return df


def run_feature_pipeline(save: bool = True) -> pd.DataFrame:
    """Load cleaned.parquet, engineer all features, save enriched outputs.

    Parameters
    ----------
    save : bool
        If True, write enriched.parquet and enriched.csv.

    Returns
    -------
    pd.DataFrame
        Enriched dataframe.
    """
    df = pd.read_parquet(config.CLEANED_PARQUET)
    df = engineer_features(df)

    if save:
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(config.ENRICHED_PARQUET, index=False)
        df.to_csv(config.ENRICHED_CSV, index=False)
        logger.info("Saved enriched data -> %s", config.ENRICHED_PARQUET)

    return df
