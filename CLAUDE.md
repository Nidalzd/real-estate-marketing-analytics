# CLAUDE.md

This file provides guidance to Claude Code when working with this project.

## About This Project

Real estate marketing analytics project analyzing 169 Facebook-generated leads from a Dubai-based company (A.S. Properties). The goal is transforming raw HubSpot CRM data into business insights, published as a professional data analytics portfolio project.

**Dataset:** `data/raw/week_2_campaign_performance.xlsx` — 169 leads, 22 columns, March 9-13 2026, 9 Facebook campaigns across UAE/Europe/UK/GCC.

## Project Structure

```
real-estate-marketing-analytics/
├── data/raw/                    # Original Excel (gitignored)
├── data/processed/              # Cleaned CSV/Parquet outputs
├── data/reference/              # Lookup tables (country codes, mappings)
├── src/                         # Python modules (config, cleaning, features, viz, scoring, analysis)
├── notebooks/                   # Jupyter notebooks 01-08 (numbered, run in order)
├── dashboard/                   # Streamlit multi-page app
├── reports/figures/             # Exported chart PNGs and HTMLs
├── reports/                     # Business report and recommendations
└── tests/                       # Unit tests for cleaning pipeline
```

## Commands

```bash
source venv/bin/activate              # Activate virtual environment
python run_cleaning.py                # Run data cleaning pipeline
python run_features.py                # Run feature engineering
jupyter notebook                      # Launch notebook server
streamlit run dashboard/app.py        # Launch interactive dashboard
pytest tests/ -v                      # Run unit tests
python -m nbconvert --execute notebooks/01_data_exploration.ipynb  # Execute a notebook
```

## Tech Stack

- **Python 3.10+** with virtual environment (`venv/`)
- **Pandas** for data manipulation — always use `.parquet` for intermediate storage, `.csv` only for final human-readable exports
- **Plotly** for interactive charts — primary visualization library
- **Seaborn/Matplotlib** for static publication-quality plots only
- **Streamlit** for the dashboard
- **Scikit-learn** for clustering and scoring
- **openpyxl** for reading the source Excel file
- **phonenumbers** library for phone country detection

## Code Standards

- All Python files use **snake_case** naming
- All functions have **docstrings** with parameter descriptions
- Imports are grouped: stdlib → third-party → local (`src.*`)
- DataFrames always use **snake_case column names** (e.g., `lead_status`, `create_date`)
- Never use `print()` in library modules — use `logging` or return values. `print()` is only for `run_*.py` scripts
- Chart functions return `plotly.graph_objects.Figure` and optionally save via `save_fig()`

## Data Pipeline Conventions

- Raw data is read-only — never modify files in `data/raw/`
- Cleaning pipeline: `raw Excel → cleaned.parquet → enriched.parquet → scored_leads.csv`
- Feature engineering always operates on `cleaned.parquet`, outputs `enriched.parquet`
- Scoring operates on `enriched.parquet`, outputs `scored_leads.csv`
- All file paths are defined in `src/config.py` — never hardcode paths elsewhere

## Notebook Standards

- Notebooks are **numbered** and must be **run in sequence** (01 before 02, etc.)
- Every notebook starts with a markdown title cell and a brief description
- Markdown narrative **between every code cell** — explain what and why, not just what
- Write **business insights**, not data descriptions ("57% never answer suggests targeting issues" not "57% are No Answer")
- Every chart gets `save_fig()` called to export to `reports/figures/`
- Final cell of each notebook: summary of key findings

## Visualization Standards

- Color palette defined in `src/config.py` — use it consistently everywhere
- All charts: white background, clear axis labels, descriptive title
- Bar charts: horizontal, sorted by value, with value labels
- Always include units in axis labels (hours, count, percentage)
- Save every chart as both PNG (for reports) and HTML (for interactivity)

## Key Domain Knowledge

- **Lead statuses** (in pipeline order): Uncontacted → No Answer → Contacted → Future Opportunity → Hot Lead → Qualified. Negative: Not Interested, Unqualified, Junk Lead. Special: Newsletter Subscription
- **"No Answer" is 57%** of all leads — the dominant outcome
- **Response time** averages 18.6 hours — industry benchmark is 5 minutes
- **31 leads (18%)** were never contacted at all
- **Phone country codes** reveal actual lead origin (971=UAE, 91=India, 380=Ukraine, 44=UK, 34=Spain, 966=Saudi)
- **Campaign names** encode: region (UAE/Europe/UK/GCC), type (teaser/leadgen/lookalike), and version
- **"D1/D2/D3" in notes** = Day 1/2/3 follow-up attempts

## Important Warnings

- Phone numbers are stored as **float64** in the raw Excel — convert via `int()` then `str()` to avoid scientific notation
- 6 columns are **100% empty** (Source 3, investor/broker, Unit Type, Unit Value, Original Create Date, Recent Deal Close Date) — drop them early
- "Marketing contact status" column has **zero variance** (all "Non-marketing contact") — drop it
- The Excel file has a **second sheet** ("Sheet1") with a pivot table — ignore it, use only the first sheet
- Associated Note IDs are **semicolon-delimited** HubSpot object IDs, not human-readable
- Create Date range is only **5 days** — be cautious about trend claims
