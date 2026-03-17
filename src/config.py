"""
config.py — Project-wide constants.

All file paths, column names, color palette, and business mappings
are defined here. Import from this module everywhere; never hardcode.
"""

from pathlib import Path

# ── Directory paths ───────────────────────────────────────────────────────────
ROOT_DIR      = Path(__file__).resolve().parent.parent
DATA_DIR      = ROOT_DIR / "data"
RAW_DIR       = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REFERENCE_DIR = DATA_DIR / "reference"
REPORTS_DIR   = ROOT_DIR / "reports"
FIGURES_DIR   = REPORTS_DIR / "figures"

# ── File paths ────────────────────────────────────────────────────────────────
RAW_FILE          = RAW_DIR / "week 2 campaign performance.xlsx"
CLEANED_PARQUET   = PROCESSED_DIR / "cleaned.parquet"
CLEANED_CSV       = PROCESSED_DIR / "cleaned.csv"
ENRICHED_PARQUET  = PROCESSED_DIR / "enriched.parquet"
ENRICHED_CSV      = PROCESSED_DIR / "enriched.csv"
SCORED_LEADS_CSV  = PROCESSED_DIR / "scored_leads.csv"

# ── Raw column names (as they arrive from HubSpot export) ────────────────────
RAW_RECORD_ID     = "Record ID"
RAW_FIRST_NAME    = "First Name"
RAW_LAST_NAME     = "Last Name"
RAW_EMAIL         = "Email"
RAW_PHONE         = "Phone Number"
RAW_LEAD_STATUS   = "Lead Status"
RAW_CAMPAIGN      = "Original Source Drill-Down 2"   # Facebook campaign/ad name
RAW_CREATE_DATE   = "Create Date"
RAW_LAST_ACTIVITY = "Last Activity Date"
RAW_OWNER         = "HubSpot Owner"
RAW_NOTES         = "Associated Note IDs"
RAW_LIFECYCLE     = "Lifecycle Stage"
RAW_COUNTRY       = "Country/Region"
RAW_CITY          = "City"

# ── Cleaned / derived column names (snake_case) ───────────────────────────────
COL_RECORD_ID          = "record_id"
COL_FIRST_NAME         = "first_name"
COL_LAST_NAME          = "last_name"
COL_EMAIL              = "email"
COL_PHONE              = "phone_number"
COL_LEAD_STATUS        = "lead_status"
COL_CAMPAIGN           = "campaign_name"
COL_CREATE_DATE        = "create_date"
COL_LAST_ACTIVITY      = "last_activity_date"
COL_OWNER              = "hubspot_owner"
COL_NOTES              = "associated_note_ids"
COL_ASSOCIATED_NOTE    = "associated_note"       # Note text (D1/D2/D3 tags live here)
COL_RECENT_CONVERSION  = "recent_conversion"     # Facebook Lead Ad form name (has currency)
COL_LIFECYCLE          = "lifecycle_stage"
COL_COUNTRY            = "country"
COL_CITY               = "city"
# Derived
COL_PHONE_COUNTRY_CODE = "phone_country_code"
COL_PHONE_COUNTRY      = "phone_country"
COL_RESPONSE_HOURS     = "response_time_hours"
COL_CAMPAIGN_REGION    = "campaign_region"
COL_CAMPAIGN_TYPE      = "campaign_type"
COL_FUNNEL_STAGE       = "funnel_stage"
COL_CONTACT_ATTEMPTS   = "contact_attempts"      # D1 / D2 / D3 from note text
COL_FORM_CURRENCY      = "form_currency"         # AED / EUR / GBP extracted from form name
COL_TARGET_REGION      = "target_region"         # Geographic target derived from form currency
COL_LEAD_QUALITY_SCORE   = "lead_quality_score"
COL_LEAD_SCORE           = "lead_score"            # kept for scoring.py compatibility
COL_LEAD_SEGMENT         = "lead_segment"          # A/B/C/D tier from scoring.py
COL_FOLLOW_UP_DAY        = "follow_up_day"         # legacy alias — prefer COL_CONTACT_ATTEMPTS
COL_WAS_CONTACTED        = "was_contacted"
COL_FORM_VERSION         = "form_version"
COL_HAS_VERIFIED_NUMBER  = "has_verified_number"
COL_IS_ARABIC_FORM       = "is_arabic_form"
COL_REGION_MATCH         = "region_match"
COL_FUNNEL_STAGE_WEIGHT  = "funnel_stage_weight"
COL_CREATE_HOUR          = "create_hour"
COL_CREATE_DAY_NAME      = "create_day_name"

# ── Color palette (dark blue / orange / green scheme) ────────────────────────
COLORS = {
    "primary":       "#1B3A6B",   # Dark navy blue
    "secondary":     "#F57C00",   # Burnt orange
    "accent":        "#2E7D32",   # Forest green
    "light_blue":    "#4A90D9",   # Mid blue
    "light_orange":  "#FFB74D",   # Amber
    "light_green":   "#66BB6A",   # Leaf green
    "neutral":       "#78909C",   # Blue-grey
    "negative":      "#C62828",   # Deep red (for negative statuses)
    "background":    "#FFFFFF",   # White
    "surface":       "#F5F7FA",   # Off-white surface
    "text":          "#212121",   # Near-black
}

# Ordered list for multi-category charts
PALETTE = [
    COLORS["primary"],
    COLORS["secondary"],
    COLORS["accent"],
    COLORS["light_blue"],
    COLORS["light_orange"],
    COLORS["light_green"],
    COLORS["neutral"],
]

# ── Lead status → funnel stage mappings ──────────────────────────────────────
FUNNEL_STAGES: dict[str, str] = {
    "Uncontacted":              "Top",
    "No Answer":                "Top",
    "Contacted":                "Middle",
    "Future Opportunity":       "Middle",
    "Hot Lead":                 "Bottom",
    "Qualified":                "Bottom",
    "Not Interested":           "Negative",
    "Unqualified":              "Negative",
    "Junk Lead":                "Negative",
    "Newsletter Subscription":  "Nurture",
}

FUNNEL_ORDER = ["Top", "Middle", "Bottom", "Negative", "Nurture"]

LEAD_STATUS_ORDER = [
    "Uncontacted",
    "No Answer",
    "Contacted",
    "Future Opportunity",
    "Hot Lead",
    "Qualified",
    "Not Interested",
    "Unqualified",
    "Junk Lead",
    "Newsletter Subscription",
]

# ── Phone country code → country name ────────────────────────────────────────
PHONE_COUNTRY_CODES: dict[int, str] = {
    971: "UAE",
    380: "Ukraine",
    44:  "UK",
    91:  "India",
    34:  "Spain",
    996: "Kyrgyzstan",
    998: "Uzbekistan",
    966: "Saudi Arabia",
    359: "Bulgaria",
    33:  "France",
    353: "Ireland",
    48:  "Poland",
    90:  "Turkey",
    92:  "Pakistan",
}

# ── Campaign name → region (keyword matching, lower-case keys) ────────────────
CAMPAIGN_REGION_KEYWORDS: dict[str, str] = {
    "uae":    "UAE",
    "europe": "Europe",
    "uk":     "UK",
    "gcc":    "GCC",
}

# ── Campaign name → type (keyword matching, lower-case keys) ─────────────────
CAMPAIGN_TYPE_KEYWORDS: dict[str, str] = {
    "lookalike": "Lookalike",        # must come before "lead gen" — lookalike names also contain "lead gen"
    "teaser":    "Teaser",
    "leadgen":   "Lead Generation",
    "lead gen":  "Lead Generation",
}

# ── Form currency → target region ────────────────────────────────────────────
FORM_CURRENCY_TO_REGION: dict[str, str] = {
    "AED": "UAE",
    "EUR": "Europe",
    "GBP": "UK",
    "SAR": "GCC",
    "USD": "GCC",
}

# ── Phone country → region (for region_match comparison with target_region) ───
PHONE_COUNTRY_TO_REGION: dict[str, str] = {
    "UAE":          "UAE",
    "Saudi Arabia": "UAE",        # Gulf / GCC treated as UAE market
    "UK":           "UK",
    "Ireland":      "UK",
    "France":       "Europe",
    "Spain":        "Europe",
    "Bulgaria":     "Europe",
    "Ukraine":      "Europe",
    "Poland":       "Europe",
    "Turkey":       "Europe",
    "India":        "GCC",
    "Pakistan":     "GCC",
    "Kyrgyzstan":   "GCC",
    "Uzbekistan":   "GCC",
}

# ── Funnel stage → numeric weight (for scoring / ordering) ───────────────────
FUNNEL_STAGE_WEIGHTS: dict[str, int] = {
    "Bottom":   4,
    "Middle":   3,
    "Top":      2,
    "Nurture":  1,
    "Negative": 0,
    "Unknown":  0,
}
