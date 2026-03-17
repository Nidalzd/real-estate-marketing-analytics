---
name: visualization
description: Use this skill when creating any chart, graph, plot, or visual for this project. Triggers on any mention of plotting, charting, visualizing, creating figures, building dashboards, or exporting charts. Also use when a chart looks wrong, needs restyling, or when choosing between chart types for a given analysis.
---

# Visualization Skill

## Chart Library Decisions

| Use Case | Library | Reason |
|----------|---------|--------|
| Interactive charts (dashboards, notebooks) | **Plotly** | Hover tooltips, zoom, export |
| Static publication charts (reports, README) | **Seaborn + Matplotlib** | Clean, print-ready |
| Funnel / Sankey diagrams | **Plotly** | Built-in funnel and sankey |
| Heatmaps | **Seaborn** or **Plotly** | Both work, Seaborn for static |
| Geographic maps | **Plotly** choropleth | Built-in world map |

## Color Palette (from src/config.py)

```python
COLORS = {
    'primary': '#1B2A4A',      # Dark navy — headers, primary bars
    'secondary': '#2E75B6',    # Blue — secondary elements
    'accent': '#E07C24',       # Orange — highlights, callouts
    'success': '#548235',      # Green — positive metrics
    'danger': '#C0392B',       # Red — negative metrics, warnings
    'neutral': '#666666',      # Gray — labels, secondary text
    'light': '#F2F2F2',        # Light gray — backgrounds
}

# For categorical data (campaigns, agents, etc.)
CATEGORY_COLORS = ['#2E75B6', '#E07C24', '#548235', '#C0392B',
                   '#6C3483', '#1ABC9C', '#E74C3C', '#3498DB', '#F39C12']

# For sequential data (heatmaps, intensity)
SEQUENTIAL = 'Blues'  # Seaborn/Plotly colorscale
```

## Chart Function Signatures (src/visualization.py)

Every function returns a `plotly.graph_objects.Figure` and optionally saves:

```python
def plot_horizontal_bar(data, x, y, title, color=None, save_name=None):
    """Sorted horizontal bar chart with value labels."""

def plot_stacked_bar(data, x, y, color, title, save_name=None):
    """Stacked bar chart with legend."""

def plot_funnel(stages, counts, title, save_name=None):
    """Funnel chart using go.Funnel."""

def plot_heatmap(data, x, y, values, title, save_name=None):
    """Annotated heatmap."""

def plot_box(data, x, y, title, save_name=None):
    """Box plot with jittered individual points."""

def plot_donut(labels, values, title, save_name=None):
    """Donut chart with percentage labels."""

def plot_radar(categories, values_dict, title, save_name=None):
    """Radar chart. values_dict = {'Agent A': [v1,v2,...], ...}."""

def save_fig(fig, filename):
    """Save to reports/figures/ as PNG and interactive HTML."""
    fig.write_image(f'reports/figures/{filename}.png', scale=2)
    fig.write_html(f'reports/figures/{filename}.html')
```

## Styling Rules

Apply these to ALL charts:

```python
# Standard layout template
layout_defaults = dict(
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(family='Arial, sans-serif', size=12, color='#333'),
    title=dict(font=dict(size=16, color='#1B2A4A')),
    margin=dict(l=60, r=30, t=60, b=40),
)

# Apply to every figure
fig.update_layout(**layout_defaults)
```

- Horizontal bars: sort descending (largest at top), add text labels with `textposition='outside'`
- Donut charts: hole=0.4, show percentages
- Box plots: always show individual points with `jitter=0.3`
- Heatmaps: annotate every cell with the value
- Always include axis titles with units: "Response Time (hours)", "Lead Count", "Conversion Rate (%)"

## Chart Catalog

These charts must be produced across the notebooks:

| Chart | Notebook | Filename |
|-------|----------|----------|
| Lead status donut | 03 | `lead_status_distribution.png` |
| Daily lead volume | 03 | `daily_lead_volume.png` |
| Campaign volume bars | 03 | `campaign_volume.png` |
| Lead funnel | 03 | `lead_funnel.png` |
| Agent lead distribution | 04 | `agent_lead_distribution.png` |
| Agent status stacked bar | 04 | `agent_status_breakdown.png` |
| Response time box plot | 04 | `response_time_by_agent.png` |
| Agent-campaign heatmap | 04 | `agent_campaign_heatmap.png` |
| Campaign contact rate | 05 | `campaign_contact_rate.png` |
| Campaign quality rate | 05 | `campaign_quality_rate.png` |
| Campaign type radar | 05 | `campaign_type_comparison.png` |
| Performance matrix heatmap | 05 | `campaign_performance_matrix.png` |
| Phone country bars | 06 | `phone_country_distribution.png` |
| Targeting accuracy heatmap | 06 | `targeting_accuracy.png` |
| Follow-up decay line | 06 | `followup_decay.png` |
| Sankey diagram | 07 | `lead_flow_sankey.png` |
| Response time vs outcome | 07 | `response_time_impact.png` |
| Lead score histogram | 08 | `lead_score_distribution.png` |
| Segment breakdown | 08 | `segment_distribution.png` |
| Geographic treemap | 08 | `geographic_segments.png` |
