# Real Estate Marketing Analytics

End-to-end analysis of 169 Facebook-generated leads for A.S. Properties, a Dubai-based real estate company. Raw HubSpot CRM data is transformed through a reproducible Python pipeline into actionable marketing insights: campaign scoring, agent performance benchmarking, geographic targeting analysis, and a lead scoring model — all surfaced through an interactive Streamlit dashboard and a series of Jupyter notebooks.

---

## Key Findings

- **56.8% of leads were never successfully reached** (No Answer), pointing to a systemic follow-up execution problem rather than a lead quality problem.
- **Average response time was 18.6 hours** against an industry benchmark of 5 minutes — placing the team well outside the optimal contact window for the majority of leads.
- **31 leads (18.3%) were never contacted at all**, representing the highest-ROI recovery opportunity with zero additional ad spend required.
- **Verified-number form variants produced higher contact rates** than open-entry forms, suggesting a form configuration change alone could meaningfully expand the reachable lead pool.
- **Phone country code analysis revealed geographic targeting gaps**: a material share of leads from UAE-targeted campaigns resolved to Indian (+91) or other non-UAE numbers, indicating audience definitions need tightening.

---

## Project Structure

```
real-estate-marketing-analytics/
│
├── data/
│   ├── raw/                        # Original HubSpot Excel export (gitignored)
│   ├── processed/                  # Cleaned and enriched pipeline outputs (parquet + csv)
│   └── reference/                  # Lookup tables: country codes, campaign mappings
│
├── src/
│   ├── config.py                   # All constants: paths, column names, color palette, mappings
│   ├── cleaning.py                 # clean_dataset() — raw Excel → cleaned.parquet
│   ├── features.py                 # engineer_features() — cleaned → enriched.parquet
│   ├── analysis.py                 # Analysis helpers: campaign scorecard, funnel, agent stats
│   ├── visualization.py            # Plotly chart functions — all return Figure objects
│   └── scoring.py                  # calculate_lead_score() and segment_leads()
│
├── notebooks/
│   ├── 01_data_exploration.ipynb   # Initial data profile: shape, types, nulls, distributions
│   ├── 02_data_cleaning.ipynb      # Cleaning walkthrough: decisions, before/after comparisons
│   ├── 03_eda_part1_volume.ipynb   # Lead volume, daily trends, status breakdown, funnel
│   ├── 04_eda_part2_agents.ipynb   # Agent performance: response time, contact rate, follow-up depth
│   ├── 05_eda_part3_campaigns.ipynb # Campaign scoring: volume vs quality, type and region analysis
│   ├── 06_eda_part4_geography.ipynb # Geographic targeting: phone codes vs campaign targets
│   ├── 07_marketing_insights.ipynb # Synthesized business insights and strategic implications
│   └── 08_segmentation.ipynb       # Lead scoring model (0–100) and A/B/C/D segment profiles
│
├── dashboard/
│   ├── app.py                      # Streamlit entry point and home page
│   ├── components/shared.py        # Shared data loaders with caching
│   └── pages/
│       ├── 01_overview.py          # KPI cards, lead funnel, status distribution, daily volume
│       ├── 02_campaigns.py         # Campaign scorecard, type radar, targeting heatmap
│       ├── 03_agents.py            # Agent scorecards, response time, follow-up depth
│       └── 04_lead_explorer.py     # Searchable lead table, score histogram, CSV export
│
├── reports/
│   ├── figures/                    # Exported chart PNGs and HTMLs
│   └── recommendations.md          # Business memo: findings and prioritized recommendations
│
├── tests/                          # Unit tests for the cleaning pipeline
├── run_cleaning.py                 # CLI entry point: runs full cleaning pipeline
├── run_features.py                 # CLI entry point: runs feature engineering
└── requirements.txt                # Python dependencies
```

---

## Methodology

### Data Cleaning
- Dropped 6 columns with 100% null values and 1 zero-variance column
- Converted phone numbers from float64 (Excel artifact) to clean string format
- Standardized all column names to snake_case
- Parsed create date and first contact date into datetime types
- Retained original data in `data/raw/` as read-only; all outputs go to `data/processed/`

### Feature Engineering
- **Phone country code** extracted via the `phonenumbers` library to determine actual lead origin
- **Campaign attributes** (region, type, version) parsed from campaign name strings
- **Response time** calculated in hours from lead creation to first contact attempt
- **Funnel stage** mapped from HubSpot lead status to ordered pipeline stages
- **Follow-up depth** (D1/D2/D3) inferred from structured coding in agent notes

### Analysis Framework
- **Campaign scorecard:** volume, contact rate, qualification rate, and composite score per campaign
- **Agent scorecard:** response time, contact rate, follow-up depth, and conversion rate per agent
- **Funnel analysis:** conversion rates between each pipeline stage
- **Geographic analysis:** campaign target region vs detected phone country — mismatch rate and distribution
- **Lead scoring:** 0–100 composite score (lead status + campaign type + phone country + response time) mapped to A/B/C/D segments

### Tools Used
- **Python 3.10** — all data work, modeling, and dashboard
- **pandas** — data manipulation and pipeline
- **Plotly** — interactive charts throughout
- **Seaborn / Matplotlib** — static publication-quality figures
- **Streamlit** — interactive dashboard
- **Scikit-learn** — clustering and scoring support
- **phonenumbers** — phone country code detection
- **Jupyter** — analysis notebooks
- **openpyxl** — reading the source Excel file

---

## Dashboard Preview

> Screenshots coming soon. To run the dashboard locally:

```bash
streamlit run dashboard/app.py
```

The dashboard has four pages:

| Page | Description |
|------|-------------|
| Overview | KPI summary, lead funnel, status donut, daily volume trend |
| Campaigns | Scorecard table, campaign type radar, geographic targeting heatmap |
| Agents | Performance scorecards, response time distributions, follow-up depth |
| Lead Explorer | Searchable/filterable lead table with score histogram and CSV export |

---

## Notebooks

Notebooks are numbered and must be run in sequence — each depends on outputs from the previous.

| Notebook | Description |
|----------|-------------|
| `01_data_exploration.ipynb` | First look at the raw dataset: shape, column types, null rates, and value distributions |
| `02_data_cleaning.ipynb` | Step-by-step cleaning walkthrough with before/after comparisons and decision rationale |
| `03_eda_part1_volume.ipynb` | Lead volume analysis: daily intake trends, status breakdown, and pipeline funnel |
| `04_eda_part2_agents.ipynb` | Agent performance deep-dive: response time, contact rate, and follow-up patterns |
| `05_eda_part3_campaigns.ipynb` | Campaign scoring: volume vs quality trade-offs, type and region breakdowns |
| `06_eda_part4_geography.ipynb` | Geographic targeting accuracy: phone country vs campaign target region mismatches |
| `07_marketing_insights.ipynb` | Synthesized business insights: what the data means for marketing strategy |
| `08_segmentation.ipynb` | Lead scoring model (0–100) and segment profiles for sales prioritization |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| Data manipulation | pandas, numpy |
| Interactive charts | Plotly |
| Static charts | Seaborn, Matplotlib |
| Dashboard | Streamlit |
| ML / clustering | Scikit-learn |
| Notebooks | Jupyter |
| Phone parsing | phonenumbers |
| Excel ingestion | openpyxl |

---

## Setup & Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/real-estate-marketing-analytics.git
cd real-estate-marketing-analytics

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the data pipeline
python run_cleaning.py
python run_features.py

# 6. Launch notebooks
jupyter notebook

# 7. Launch the dashboard
streamlit run dashboard/app.py
```

---

## Dataset

- **Source:** HubSpot CRM export from Facebook Lead Ads
- **Records:** 169 leads across 5 days (March 9–13, 2026)
- **Raw columns:** 22 (6 dropped as 100% null; 8 features engineered → 30 final columns)
- **Campaigns:** 9 Facebook campaigns targeting UAE, Europe, UK, and GCC markets
- **Privacy:** Raw data is not included in this repository. The `data/raw/` directory is gitignored. All analysis outputs in `data/processed/` use anonymized/aggregated representations.

---

## Future Work

- **Multi-week analysis:** Extend to 4+ weeks of data to establish baseline conversion rates and identify genuine trends vs. single-week anomalies.
- **ML-driven lead scoring at scale:** The current rule-based scoring model is designed for 169 records. A logistic regression or gradient boosting model becomes viable at 1,000+ labeled leads with known outcomes.
- **Ad spend integration:** Join campaign cost data to calculate true cost-per-qualified-lead and ROI per campaign — currently blocked by the absence of cost data in the CRM export.
- **Live CRM API integration:** Replace the static Excel export workflow with a HubSpot API connection for daily-refresh analysis and near-real-time dashboard updates.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
