"""
00_upload_data.py — Data upload page.

Accepts a new weekly HubSpot Excel export, runs the full pipeline
(clean → features → score), and writes the processed data so all
other dashboard pages pick it up immediately.
"""

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_DASHBOARD = Path(__file__).resolve().parent.parent
for _p in [str(_ROOT), str(_DASHBOARD)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd
import streamlit as st

from src import config
from components.shared import page_footer

st.set_page_config(page_title="Upload Data – RE Analytics", layout="wide")

st.title("Upload Weekly Data")
st.markdown(
    "Upload a new HubSpot Excel export to refresh the dashboard. "
    "The pipeline runs automatically: clean → features → score."
)

# ── Upload widget ──────────────────────────────────────────────────────────────

uploaded = st.file_uploader("Select HubSpot Excel export (.xlsx)", type=["xlsx"])

mode = st.radio(
    "Upload mode",
    ["Replace existing data", "Append to existing data (multi-week analysis)"],
    help=(
        "**Replace** overwrites processed files with data from this file only.  \n"
        "**Append** merges new leads with existing data, deduplicating on record_id."
    ),
)

# ── Preview ────────────────────────────────────────────────────────────────────

if uploaded is not None:
    with st.expander("Preview uploaded file (first 10 rows, raw)"):
        try:
            preview_df = pd.read_excel(uploaded, sheet_name=0, engine="openpyxl", nrows=10)
            st.dataframe(preview_df, use_container_width=True)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not preview file: {exc}")
        finally:
            # Reset file pointer so the pipeline can re-read it
            uploaded.seek(0)

# ── Process button ─────────────────────────────────────────────────────────────

if uploaded is not None:
    if st.button("Process & Update Dashboard", type="primary"):
        progress = st.progress(0, text="Starting pipeline…")
        status_area = st.empty()

        try:
            # ── Step 1: Save upload to a temp file ────────────────────────────
            progress.progress(10, text="Saving uploaded file…")
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(uploaded.read())
                tmp_path = Path(tmp.name)

            # ── Step 2: Clean ─────────────────────────────────────────────────
            progress.progress(25, text="Running cleaning pipeline…")
            from src.cleaning import clean_dataset  # noqa: PLC0415
            cleaned_df = clean_dataset(tmp_path)
            status_area.info(f"Cleaning complete — {len(cleaned_df)} rows")

            # ── Step 3: Feature engineering ───────────────────────────────────
            progress.progress(50, text="Engineering features…")
            from src.features import engineer_features  # noqa: PLC0415
            enriched_df = engineer_features(cleaned_df)
            status_area.info(f"Features complete — {len(enriched_df.columns)} columns")

            # ── Step 4: Add week_label ────────────────────────────────────────
            if config.COL_CREATE_DATE in enriched_df.columns:
                dates = pd.to_datetime(enriched_df[config.COL_CREATE_DATE], utc=True, errors="coerce")
                min_date = dates.min()
                week_label = f"Week of {min_date.strftime('%b %-d')}" if pd.notna(min_date) else "Unknown Week"
                enriched_df["week_label"] = week_label

            # ── Step 5: Replace or Append ─────────────────────────────────────
            progress.progress(65, text="Saving enriched data…")

            if mode.startswith("Replace"):
                rows_before = (
                    len(pd.read_parquet(config.ENRICHED_PARQUET))
                    if config.ENRICHED_PARQUET.exists()
                    else 0
                )
                enriched_df.to_parquet(config.ENRICHED_PARQUET, index=False)
                enriched_df.to_csv(config.ENRICHED_CSV, index=False)
                rows_after = len(enriched_df)
                mode_summary = f"Replaced {rows_before} rows → {rows_after} rows"

            else:  # Append
                if config.ENRICHED_PARQUET.exists():
                    existing_df = pd.read_parquet(config.ENRICHED_PARQUET)
                    rows_before = len(existing_df)
                    combined = pd.concat([existing_df, enriched_df], ignore_index=True)
                    # Deduplicate: keep the latest copy of each record_id
                    combined = combined.drop_duplicates(
                        subset=[config.COL_RECORD_ID], keep="last"
                    ).reset_index(drop=True)
                    rows_after = len(combined)
                    new_records = rows_after - rows_before
                    combined.to_parquet(config.ENRICHED_PARQUET, index=False)
                    combined.to_csv(config.ENRICHED_CSV, index=False)
                    mode_summary = (
                        f"Appended: {rows_before} existing + upload → "
                        f"{rows_after} rows after dedup "
                        f"({new_records} net new)"
                    )
                else:
                    # No existing file — treat as replace
                    enriched_df.to_parquet(config.ENRICHED_PARQUET, index=False)
                    enriched_df.to_csv(config.ENRICHED_CSV, index=False)
                    rows_after = len(enriched_df)
                    mode_summary = f"No existing data found — saved {rows_after} rows"

            # ── Step 6: Score ─────────────────────────────────────────────────
            progress.progress(80, text="Scoring leads…")
            from src.scoring import run_scoring_pipeline  # noqa: PLC0415
            run_scoring_pipeline(save=True)

            # ── Step 7: Clear Streamlit cache so pages reload fresh ───────────
            progress.progress(95, text="Clearing cache…")
            st.cache_data.clear()

            # ── Done ──────────────────────────────────────────────────────────
            progress.progress(100, text="Done.")
            status_area.empty()

            st.success(
                f"✅ {rows_after} leads processed. Dashboard updated.  \n"
                f"_{mode_summary}_"
            )
            st.info("Navigate to any page in the sidebar — all pages now reflect the new data.")

        except Exception as exc:  # noqa: BLE001
            progress.empty()
            st.error(f"Pipeline failed: {exc}")
            raise  # surface traceback in terminal for debugging

        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass

page_footer()
