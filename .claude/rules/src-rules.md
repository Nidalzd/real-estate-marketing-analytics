# Source Module Rules

All reusable Python code lives in `src/`. Notebooks and dashboard import from here.

## Module Responsibilities

- `config.py` — ALL constants: file paths, column names, color palette, mapping dictionaries. Single source of truth.
- `cleaning.py` — `clean_dataset(filepath)` function. Input: Excel path. Output: saved parquet + dataframe.
- `features.py` — `engineer_features(df)` function. Input: cleaned df. Output: enriched df.
- `analysis.py` — Analysis helper functions: `campaign_scorecard()`, `agent_scorecard()`, `calculate_funnel()`, etc.
- `visualization.py` — Chart functions. Every function returns a Plotly Figure. Every function has an optional `save_name` param.
- `scoring.py` — `calculate_lead_score(df)` and `segment_leads(df)`.

## Rules

- Never put business logic in notebooks — put it in src/ and import it
- Every function has a docstring
- No `print()` statements in library code — return values or use logging
- All file paths come from `config.py` constants
- All color values come from `config.py` palette
