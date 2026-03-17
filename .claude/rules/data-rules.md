# Data Rules

Files in `data/raw/` are READ-ONLY. Never modify, overwrite, or delete the original Excel file.

All pipeline outputs go to `data/processed/`:
- `cleaned.parquet` and `cleaned.csv` — output of cleaning pipeline
- `enriched.parquet` and `enriched.csv` — output of feature engineering
- `scored_leads.csv` — output of lead scoring

Always save both `.parquet` (for fast loading in Python) and `.csv` (for human inspection).

When loading data for analysis, always use `.parquet` format for speed.
