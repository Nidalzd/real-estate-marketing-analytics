---
name: data-cleaning
description: Use this skill when cleaning, transforming, or preparing the CRM dataset. Triggers on any mention of cleaning data, fixing phone numbers, handling nulls, parsing campaign names, standardizing columns, or running the cleaning pipeline. Also use when debugging data quality issues or when a downstream notebook fails because of data problems.
---

# Data Cleaning Skill

## Pipeline Overview

The cleaning pipeline runs in strict order. Each step depends on the previous one.

```
raw Excel (data/raw/) → clean_dataset() → cleaned.parquet
cleaned.parquet → engineer_features() → enriched.parquet
enriched.parquet → calculate_lead_score() → scored_leads.csv
```

## Cleaning Operations (src/cleaning.py)

Run these in order inside `clean_dataset(filepath)`:

### Step 1: Load & Drop
```python
df = pd.read_excel(filepath, sheet_name='Week 2 - Campaign Performance')
# Drop 6 empty columns
drop_cols = ['Source 3', 'Are you an investor or a broker', 'Unit Type',
             'Unit Value', 'Original Create Date', 'Recent Deal Close Date']
df.drop(columns=drop_cols, inplace=True)
# Drop zero-variance columns
df.drop(columns=['Marketing contact status', 'Original Source',
                 'Original Source Drill-Down 1'], inplace=True)
```

### Step 2: Phone Number Fix (CRITICAL)
```python
# Float → int → string. Do NOT use str(float) — gives scientific notation
df['Phone Number'] = df['Phone Number'].apply(
    lambda x: str(int(x)) if pd.notna(x) else None
)
# Verify: should look like "971508912345" not "9.71509e+11"
```

### Step 3: Fill Missing Values
```python
df['Lead Status'] = df['Lead Status'].fillna('Uncontacted')  # 31 blanks
df['Contact owner'] = df['Contact owner'].fillna('Unassigned').str.title()  # 4 blanks
```

### Step 4: Rename to snake_case
```python
rename_map = {
    'Record ID': 'record_id',
    'First Name': 'first_name',
    'Last Name': 'last_name',
    'Phone Number': 'phone_number',
    'Contact owner': 'contact_owner',
    'Lead Status': 'lead_status',
    'Associated Note': 'associated_note',
    'Create Date': 'create_date',
    'Original Source Drill-Down 2': 'campaign_name',
    'Email': 'email',
    'Recent Conversion': 'recent_conversion',
    'Last Activity Date': 'last_activity_date',
    'Associated Note IDs': 'associated_note_ids',
}
df.rename(columns=rename_map, inplace=True)
```

### Step 5: Save
```python
df.to_parquet('data/processed/cleaned.parquet', index=False)
df.to_csv('data/processed/cleaned.csv', index=False)
```

## Feature Engineering Operations (src/features.py)

See `src/config.py` for all mapping dictionaries. Key derived features:

| Feature | Logic |
|---------|-------|
| `response_time_hours` | `(last_activity_date - create_date).total_seconds() / 3600` |
| `was_contacted` | `1 if last_activity_date is not null` |
| `contact_attempts` | Count of `D\d` patterns in `associated_note` |
| `target_region` | Parse campaign_name → UAE/Europe/UK & Ireland/GCC/Other |
| `campaign_type` | Parse campaign_name → teaser/leadgen/lookalike/optimized/other |
| `form_currency` | Parse recent_conversion → AED/EUR/USD/GBP |
| `phone_country` | Map first 2-3 digits of phone_number to country name |
| `region_match` | 1 if phone_country's region matches target_region |
| `funnel_stage` | Map lead_status → Top/Middle/Bottom/Lost/Nurture |

## Validation Checks

After cleaning, verify:
- `df.shape[0]` == 169 (no rows lost)
- `df['phone_number'].str.contains('e\+').sum()` == 0 (no scientific notation)
- `df['lead_status'].isna().sum()` == 0 (no nulls)
- `df['contact_owner'].isna().sum()` == 0 (no nulls)
- Column count should be 13 (22 original - 9 dropped)

After feature engineering, verify:
- All new columns exist
- `target_region` has no "Unknown" for the 9 known campaigns
- `phone_country` is populated for records with phone numbers
