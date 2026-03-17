"""
cleaning.py — Raw data ingestion and cleaning pipeline.

Public API: clean_dataset(filepath) — runs all cleaning steps end-to-end
and saves cleaned.parquet + cleaned.csv to data/processed/.
"""

import pandas as pd

from src import config


# Columns that are 100 % empty in this dataset — drop unconditionally.
_EMPTY_COLUMNS = [
    "Source 3",
    "Are you an investor or a broker",
    "Unit Type",
    "Unit Value",
    "Original Create Date",
    "Recent Deal Close Date",
]

# Columns with zero variance (single value across all rows) — useless for analysis.
_ZERO_VARIANCE_COLUMNS = [
    "Marketing contact status",
    "Original Source",
    "Original Source Drill-Down 1",
]

# Rename map: raw HubSpot column name -> clean snake_case name.
_RENAME_MAP = {
    "Record ID":                    "record_id",
    "First Name":                   "first_name",
    "Last Name":                    "last_name",
    "Email":                        "email",
    "Phone Number":                 "phone_number",
    "Lead Status":                  "lead_status",
    "Original Source Drill-Down 2": "campaign_name",
    "Create Date":                  "create_date",
    "Last Activity Date":           "last_activity_date",
    "Contact owner":                "hubspot_owner",
    "HubSpot Owner":                "hubspot_owner",   # alternate header spelling
    "Associated Note IDs":          "associated_note_ids",
    "Lifecycle Stage":              "lifecycle_stage",
    "Country/Region":               "country",
    "City":                         "city",
}


def clean_dataset(filepath=None) -> pd.DataFrame:
    """Read, clean, and save the raw HubSpot Excel export.

    Steps (in order):
      1. Read first sheet of Excel file.
      2. Drop 6 completely empty columns.
      3. Drop 3 zero-variance columns.
      4. Convert Phone Number float -> int -> string.
      5. Fill blank Lead Status with "Uncontacted".
      6. Standardize Contact owner: title-case, fill blanks with "Unassigned".
      7. Parse Create Date and Last Activity Date as datetime (UTC).
      8. Rename all columns to snake_case.
      9. Save to data/processed/cleaned.parquet and cleaned.csv.

    Parameters
    ----------
    filepath : Path or str, optional
        Path to the source Excel file. Defaults to config.RAW_FILE.

    Returns
    -------
    pd.DataFrame
        Fully cleaned dataframe.
    """
    filepath = filepath or config.RAW_FILE

    # ── Step 1: Load ──────────────────────────────────────────────────────────
    df = pd.read_excel(filepath, sheet_name=0, engine="openpyxl")
    rows_before = len(df)
    cols_before = list(df.columns)
    print(f"\n{'='*60}")
    print("  CLEANING PIPELINE")
    print(f"{'='*60}")
    print(f"\n[1] Loaded: {rows_before} rows × {len(cols_before)} columns")
    print(f"    Source: {filepath}")

    # ── Step 2: Drop empty columns ────────────────────────────────────────────
    present_empty = [c for c in _EMPTY_COLUMNS if c in df.columns]
    df = df.drop(columns=present_empty)
    print(f"\n[2] Dropped {len(present_empty)} empty columns:")
    for c in present_empty:
        print(f"    - {c}")

    # ── Step 3: Drop zero-variance columns ────────────────────────────────────
    present_zv = [c for c in _ZERO_VARIANCE_COLUMNS if c in df.columns]
    df = df.drop(columns=present_zv)
    print(f"\n[3] Dropped {len(present_zv)} zero-variance columns:")
    for c in present_zv:
        print(f"    - {c}")

    # ── Step 4: Phone number float -> string ───────────────────────────────────
    phone_col = "Phone Number"
    if phone_col in df.columns:
        phone_null_before = df[phone_col].isna().sum()
        df[phone_col] = df[phone_col].apply(
            lambda x: str(int(x)) if pd.notna(x) else None
        )
        phone_null_after = df[phone_col].isna().sum()
        converted = rows_before - phone_null_before
        print(f"\n[4] Phone Number: converted {converted} values float -> string")
        print(f"    Nulls unchanged: {phone_null_after}")

    # ── Step 5: Fill blank Lead Status ───────────────────────────────────────
    lead_col = "Lead Status"
    if lead_col in df.columns:
        filled = df[lead_col].isna().sum()
        df[lead_col] = df[lead_col].fillna("Uncontacted")
        print(f"\n[5] Lead Status: filled {filled} blank(s) -> 'Uncontacted'")

    # ── Step 6: Standardize Contact owner ────────────────────────────────────
    owner_col = "Contact owner" if "Contact owner" in df.columns else "HubSpot Owner"
    if owner_col in df.columns:
        blank_owners = df[owner_col].isna().sum()
        df[owner_col] = df[owner_col].str.strip().str.title().fillna("Unassigned")
        print(f"\n[6] Contact owner: applied title-case, filled {blank_owners} blank(s) -> 'Unassigned'")

    # ── Step 7: Parse dates ───────────────────────────────────────────────────
    date_cols = ["Create Date", "Last Activity Date"]
    parsed = []
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
            null_count = df[col].isna().sum()
            parsed.append(f"{col} ({null_count} unparseable -> NaT)")
    print(f"\n[7] Parsed {len(parsed)} date column(s):")
    for p in parsed:
        print(f"    - {p}")

    # ── Step 8: Rename columns to snake_case ─────────────────────────────────
    rename_applied = {k: v for k, v in _RENAME_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_applied)
    # Any remaining columns not in the map: auto-convert to snake_case
    auto_renamed = {}
    for col in df.columns:
        snake = col.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")
        if snake != col:
            auto_renamed[col] = snake
    if auto_renamed:
        df = df.rename(columns=auto_renamed)
    total_renamed = len(rename_applied) + len(auto_renamed)
    print(f"\n[8] Renamed {total_renamed} column(s) to snake_case")
    print(f"    Final columns ({len(df.columns)}): {list(df.columns)}")

    # ── Step 9: Save outputs ──────────────────────────────────────────────────
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.CLEANED_PARQUET, index=False)
    df.to_csv(config.CLEANED_CSV, index=False)
    print(f"\n[9] Saved outputs:")
    print(f"    -> {config.CLEANED_PARQUET}")
    print(f"    -> {config.CLEANED_CSV}")

    # ── Summary ───────────────────────────────────────────────────────────────
    cols_dropped = len(cols_before) - len(df.columns)
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    print(f"  Rows:           {rows_before} -> {len(df)} (unchanged)")
    print(f"  Columns:        {len(cols_before)} -> {len(df.columns)} ({cols_dropped} dropped)")
    print(f"  Nulls in key columns:")
    for col in ["lead_status", "hubspot_owner", "phone_number", "campaign_name"]:
        if col in df.columns:
            n = df[col].isna().sum()
            print(f"    {col:<25} {n} null(s)")
    print(f"{'='*60}\n")

    return df
