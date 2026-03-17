---
name: notebook-creation
description: Use this skill when creating, editing, or debugging Jupyter notebooks for this project. Triggers on any mention of notebooks, .ipynb files, Jupyter, creating analysis notebooks, or when a notebook fails to execute. Also use when improving notebook narrative quality or adding markdown explanations.
---

# Notebook Creation Skill

## Notebook Inventory

| # | Filename | Purpose | Depends On |
|---|----------|---------|------------|
| 01 | `01_data_exploration.ipynb` | Raw data profiling | Raw Excel file |
| 02 | `02_data_cleaning.ipynb` | Cleaning pipeline walkthrough | Raw Excel + src/cleaning.py |
| 03 | `03_eda_part1_volume.ipynb` | Lead volume & distribution | enriched.parquet |
| 04 | `04_eda_part2_agents.ipynb` | Agent performance analysis | enriched.parquet |
| 05 | `05_eda_part3_campaigns.ipynb` | Campaign deep-dive | enriched.parquet |
| 06 | `06_eda_part4_geography.ipynb` | Geography & notes mining | enriched.parquet |
| 07 | `07_marketing_insights.ipynb` | Core business analysis | enriched.parquet + src/analysis.py |
| 08 | `08_segmentation.ipynb` | Scoring & segmentation | enriched.parquet + src/scoring.py |

## Notebook Structure Template

Every notebook follows this structure:

```
Cell 1 (Markdown):  # Title
                    Brief description (2-3 sentences)
                    Key questions this notebook answers

Cell 2 (Code):      Imports and data loading
                    import pandas as pd
                    import sys; sys.path.insert(0, '..')
                    from src.config import *
                    from src.visualization import *
                    df = pd.read_parquet('../data/processed/enriched.parquet')

Cell 3+ (Alternating):
                    Markdown → explain WHAT we're investigating and WHY
                    Code → perform the analysis
                    Markdown → interpret the RESULTS as business insight
                    Code → create visualization
                    Markdown → explain what the chart reveals

Final Cell (Markdown): ## Key Takeaways
                       Numbered list of 3-5 most important findings
```

## Writing Narrative Text

### DO:
- "57% of leads never answer the phone, suggesting the sales team's 18.6-hour average response time may be letting leads go cold before the first call."
- "The UAE Teaser campaign generates the most leads (53) but has a 13% disqualification rate — volume without quality."
- "Only 16% of leads receive a second follow-up attempt, despite industry research showing persistence through 5+ attempts significantly improves conversion."

### DON'T:
- "57% of leads have status 'No Answer'." (just restating the data)
- "The bar chart below shows the distribution." (describing mechanics)
- "Let's look at the next analysis." (filler transitions)

## Creating Notebooks Programmatically

Use `nbformat` to generate notebooks from Python:

```python
import nbformat as nbf
nb = nbf.v4.new_notebook()

nb.cells.append(nbf.v4.new_markdown_cell("# Title"))
nb.cells.append(nbf.v4.new_code_cell("import pandas as pd"))
nb.cells.append(nbf.v4.new_markdown_cell("## Analysis Section"))

with open('notebooks/01_example.ipynb', 'w') as f:
    nbf.write(nb, f)
```

To execute a notebook after creation:
```bash
jupyter nbconvert --to notebook --execute notebooks/01_example.ipynb --output 01_example.ipynb
```

## Path Configuration Inside Notebooks

Notebooks live in `notebooks/` so paths go up one level:

```python
import sys
sys.path.insert(0, '..')

from src.config import PATHS, COLORS, STATUS_MAPPING
from src.visualization import plot_horizontal_bar, save_fig
from src.analysis import campaign_scorecard

df = pd.read_parquet(PATHS['enriched'])
# where PATHS['enriched'] = 'data/processed/enriched.parquet'
# Adjust: '../data/processed/enriched.parquet' OR set working directory
import os
os.chdir('..')  # Change to project root so all paths work
```

## Common Notebook Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: src` | Path not set | Add `sys.path.insert(0, '..')` |
| `FileNotFoundError: data/processed/` | Wrong working directory | Add `os.chdir('..')` in cell 2 |
| `kaleido` error on `write_image` | Missing kaleido | `pip install kaleido` |
| Plotly not rendering | Notebook renderer | Add `import plotly.io as pio; pio.renderers.default = 'notebook'` |
