"""
visualization.py — Reusable Plotly chart functions for the Real Estate Analytics project.

Generic factory functions (plot_*) accept arbitrary DataFrames so they can be
reused across all notebooks and the dashboard.  Specialized wrappers
(bar_lead_status, funnel_chart, etc.) remain for direct notebook convenience.

Every function returns a plotly.graph_objects.Figure.
Call save_fig(fig, name) to export as PNG + HTML to reports/figures/.
Colors and paths come from config.py — never hardcode them here.
"""

import logging

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src import config

logger = logging.getLogger(__name__)

# ── Shared layout defaults ─────────────────────────────────────────────────────

_LAYOUT = dict(
    plot_bgcolor=config.COLORS["background"],
    paper_bgcolor=config.COLORS["background"],
    font=dict(family="Arial, sans-serif", size=12, color=config.COLORS["text"]),
    title=dict(
        font=dict(size=16, color=config.COLORS["primary"]),
        x=0.5,
        xanchor="center",
    ),
    margin=dict(l=80, r=60, t=70, b=60),
    legend=dict(
        bgcolor=config.COLORS["background"],
        bordercolor=config.COLORS["neutral"],
        borderwidth=1,
    ),
)


# ── 9. save_fig ────────────────────────────────────────────────────────────────

def save_fig(fig: go.Figure, name: str) -> None:
    """Export a figure as both PNG (scale=2) and interactive HTML.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure to export.
    name : str
        Base filename without extension (e.g. 'lead_funnel').
        Files land in FIGURES_DIR/<name>.png and .html.
    """
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path  = config.FIGURES_DIR / f"{name}.png"
    html_path = config.FIGURES_DIR / f"{name}.html"
    fig.write_image(str(png_path), scale=2)
    fig.write_html(str(html_path))
    logger.info("Saved figure → %s (.png + .html)", name)


# ── 1. Horizontal bar chart ────────────────────────────────────────────────────

def plot_horizontal_bar(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    save_name: str | None = None,
) -> go.Figure:
    """Sorted horizontal bar chart with outside value labels.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing the columns referenced by x and y.
    x : str
        Column name for the numeric axis (bar length).
    y : str
        Column name for the categorical axis (bar labels).
    title : str
        Chart title displayed above the figure.
    color : str | None
        Hex color for all bars.  Defaults to COLORS['primary'].
    save_name : str | None
        If provided, saves PNG + HTML via save_fig().

    Returns
    -------
    go.Figure
    """
    bar_color = color or config.COLORS["primary"]
    df = data.sort_values(x, ascending=True)  # ascending → largest bar at top

    fig = go.Figure(
        go.Bar(
            x=df[x],
            y=df[y],
            orientation="h",
            marker_color=bar_color,
            text=df[x],
            textposition="outside",
            texttemplate="%{text:,}",
            cliponaxis=False,
        )
    )

    fig.update_layout(
        **_LAYOUT,
        title_text=title,
        xaxis=dict(showgrid=True, gridcolor=config.COLORS["surface"], zeroline=False),
        yaxis=dict(showgrid=False),
    )

    if save_name:
        save_fig(fig, save_name)

    return fig


# ── 2. Stacked bar chart ───────────────────────────────────────────────────────

def plot_stacked_bar(
    data: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str,
    save_name: str | None = None,
) -> go.Figure:
    """Stacked bar chart where each segment is a unique value in `color` column.

    Parameters
    ----------
    data : pd.DataFrame
        Long-format DataFrame with columns x, y, and color.
    x : str
        Column for the x-axis categories.
    y : str
        Column for bar heights (numeric).
    color : str
        Column whose unique values become individual stacked segments.
    title : str
        Chart title.
    save_name : str | None
        If provided, saves PNG + HTML via save_fig().

    Returns
    -------
    go.Figure
    """
    categories = data[color].unique().tolist()
    fig = go.Figure()

    for i, cat in enumerate(categories):
        subset = data[data[color] == cat]
        fig.add_trace(
            go.Bar(
                name=str(cat),
                x=subset[x],
                y=subset[y],
                marker_color=config.PALETTE[i % len(config.PALETTE)],
                text=subset[y],
                textposition="inside",
                texttemplate="%{text:,}",
            )
        )

    fig.update_layout(
        **_LAYOUT,
        title_text=title,
        barmode="stack",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=config.COLORS["surface"]),
    )

    if save_name:
        save_fig(fig, save_name)

    return fig


# ── 3. Funnel chart ────────────────────────────────────────────────────────────

def plot_funnel(
    stages: list[str],
    counts: list[int | float],
    title: str,
    save_name: str | None = None,
) -> go.Figure:
    """Funnel chart using go.Funnel, widest stage at the top.

    Parameters
    ----------
    stages : list[str]
        Stage labels from top (widest) to bottom (narrowest).
    counts : list[int | float]
        Numeric value per stage, matching the order of stages.
    title : str
        Chart title.
    save_name : str | None
        If provided, saves PNG + HTML via save_fig().

    Returns
    -------
    go.Figure
    """
    fig = go.Figure(
        go.Funnel(
            y=stages,
            x=counts,
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(color=config.PALETTE[: len(stages)]),
            connector=dict(line=dict(color=config.COLORS["neutral"], width=1)),
        )
    )

    fig.update_layout(**_LAYOUT, title_text=title)

    if save_name:
        save_fig(fig, save_name)

    return fig


# ── 4. Heatmap ─────────────────────────────────────────────────────────────────

def plot_heatmap(
    data: pd.DataFrame,
    x: str,
    y: str,
    values: str,
    title: str,
    save_name: str | None = None,
) -> go.Figure:
    """Annotated heatmap pivoted from long-format data.

    Parameters
    ----------
    data : pd.DataFrame
        Long-format DataFrame with columns x, y, and values.
    x : str
        Column mapped to heatmap columns.
    y : str
        Column mapped to heatmap rows.
    values : str
        Numeric column encoded as cell colour intensity.
    title : str
        Chart title.
    save_name : str | None
        If provided, saves PNG + HTML via save_fig().

    Returns
    -------
    go.Figure
    """
    pivot = data.pivot_table(
        index=y, columns=x, values=values, aggfunc="sum", fill_value=0
    )

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[
                [0.0, config.COLORS["surface"]],
                [0.5, config.COLORS["light_blue"]],
                [1.0, config.COLORS["primary"]],
            ],
            text=pivot.values,
            texttemplate="%{text}",
            showscale=True,
            hoverongaps=False,
        )
    )

    fig.update_layout(**_LAYOUT, title_text=title)

    if save_name:
        save_fig(fig, save_name)

    return fig


# ── 5. Box plot ────────────────────────────────────────────────────────────────

def plot_box(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    save_name: str | None = None,
) -> go.Figure:
    """Box plot with jittered individual points overlaid.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing columns x and y.
    x : str
        Column for the categorical grouping (x-axis).
    y : str
        Column for the numeric values (y-axis).
    title : str
        Chart title.
    save_name : str | None
        If provided, saves PNG + HTML via save_fig().

    Returns
    -------
    go.Figure
    """
    categories = data[x].dropna().unique().tolist()
    fig = go.Figure()

    for i, cat in enumerate(categories):
        subset = data[data[x] == cat][y].dropna()
        clr = config.PALETTE[i % len(config.PALETTE)]
        fig.add_trace(
            go.Box(
                y=subset,
                name=str(cat),
                marker_color=clr,
                line=dict(color=clr),
                boxpoints="all",
                jitter=0.3,
                pointpos=0,
            )
        )

    fig.update_layout(
        **_LAYOUT,
        title_text=title,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=config.COLORS["surface"]),
        showlegend=False,
    )

    if save_name:
        save_fig(fig, save_name)

    return fig


# ── 6. Time series ─────────────────────────────────────────────────────────────

def plot_time_series(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    save_name: str | None = None,
) -> go.Figure:
    """Line chart for time-series data with markers at each data point.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame with x (datetime or ordinal) and y (numeric) columns.
    x : str
        Column for the x-axis (dates or ordered categories).
    y : str
        Column for the y-axis numeric metric.
    title : str
        Chart title.
    color : str | None
        Optional column name to split into multiple labelled lines.
    save_name : str | None
        If provided, saves PNG + HTML via save_fig().

    Returns
    -------
    go.Figure
    """
    fig = go.Figure()

    if color and color in data.columns:
        for i, grp in enumerate(data[color].unique()):
            subset = data[data[color] == grp].sort_values(x)
            fig.add_trace(
                go.Scatter(
                    x=subset[x],
                    y=subset[y],
                    mode="lines+markers",
                    name=str(grp),
                    line=dict(color=config.PALETTE[i % len(config.PALETTE)], width=2),
                    marker=dict(size=7),
                )
            )
    else:
        df = data.sort_values(x)
        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[y],
                mode="lines+markers",
                showlegend=False,
                line=dict(color=config.COLORS["primary"], width=2),
                marker=dict(size=7, color=config.COLORS["secondary"]),
            )
        )

    fig.update_layout(
        **_LAYOUT,
        title_text=title,
        xaxis=dict(showgrid=True, gridcolor=config.COLORS["surface"]),
        yaxis=dict(showgrid=True, gridcolor=config.COLORS["surface"], zeroline=False),
    )

    if save_name:
        save_fig(fig, save_name)

    return fig


# ── 7. Donut chart ─────────────────────────────────────────────────────────────

def plot_donut(
    labels: list[str],
    values: list[int | float],
    title: str,
    save_name: str | None = None,
) -> go.Figure:
    """Donut chart with percentage and label annotations outside the ring.

    Parameters
    ----------
    labels : list[str]
        Slice labels.
    values : list[int | float]
        Numeric value for each slice.
    title : str
        Chart title.
    save_name : str | None
        If provided, saves PNG + HTML via save_fig().

    Returns
    -------
    go.Figure
    """
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(
                colors=config.PALETTE[: len(labels)],
                line=dict(color=config.COLORS["background"], width=2),
            ),
            textinfo="label+percent",
            textposition="outside",
            pull=[0.03] * len(labels),
        )
    )

    fig.update_layout(**_LAYOUT, title_text=title, showlegend=True)

    if save_name:
        save_fig(fig, save_name)

    return fig


# ── 8. Radar chart ─────────────────────────────────────────────────────────────

def plot_radar(
    categories: list[str],
    values_dict: dict[str, list[float]],
    title: str,
    save_name: str | None = None,
) -> go.Figure:
    """Radar / spider chart comparing multiple series across the same axes.

    Parameters
    ----------
    categories : list[str]
        Spoke labels.  Length must match each values list.
    values_dict : dict[str, list[float]]
        Series name → list of values (one per category).
        Example: {'Campaign A': [0.8, 0.5, 0.9], 'Campaign B': [0.4, 0.7, 0.6]}
    title : str
        Chart title.
    save_name : str | None
        If provided, saves PNG + HTML via save_fig().

    Returns
    -------
    go.Figure
    """
    closed_cats = categories + [categories[0]]  # close the polygon
    fig = go.Figure()

    for i, (name, vals) in enumerate(values_dict.items()):
        closed_vals = list(vals) + [vals[0]]
        clr = config.PALETTE[i % len(config.PALETTE)]
        fig.add_trace(
            go.Scatterpolar(
                r=closed_vals,
                theta=closed_cats,
                fill="toself",
                name=name,
                line=dict(color=clr, width=2),
                fillcolor=clr,
                opacity=0.25,
            )
        )

    fig.update_layout(
        **_LAYOUT,
        title_text=title,
        polar=dict(
            bgcolor=config.COLORS["surface"],
            radialaxis=dict(visible=True, gridcolor=config.COLORS["neutral"]),
            angularaxis=dict(gridcolor=config.COLORS["neutral"]),
        ),
        showlegend=True,
    )

    if save_name:
        save_fig(fig, save_name)

    return fig


# ── Specialized wrappers (kept for notebook convenience) ──────────────────────

def bar_lead_status(df_counts) -> go.Figure:
    """Horizontal bar chart of lead status distribution.

    Parameters
    ----------
    df_counts : pd.DataFrame
        Output of analysis.lead_status_distribution() with columns
        'lead_status', 'count', 'pct'.

    Returns
    -------
    go.Figure
    """
    fig = px.bar(
        df_counts.sort_values("count"),
        x="count",
        y=config.COL_LEAD_STATUS,
        orientation="h",
        text="pct",
        color_discrete_sequence=[config.COLORS["primary"]],
        labels={"count": "Number of Leads", config.COL_LEAD_STATUS: "Lead Status"},
        title="Lead Status Distribution",
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(**_LAYOUT)
    return fig


def bar_campaign_performance(df_summary) -> go.Figure:
    """Horizontal bar chart of total leads per campaign.

    Parameters
    ----------
    df_summary : pd.DataFrame
        Output of analysis.campaign_performance() with column 'total_leads'.

    Returns
    -------
    go.Figure
    """
    fig = px.bar(
        df_summary.sort_values("total_leads"),
        x="total_leads",
        y=config.COL_CAMPAIGN,
        orientation="h",
        text="total_leads",
        color_discrete_sequence=[config.COLORS["secondary"]],
        labels={"total_leads": "Total Leads", config.COL_CAMPAIGN: "Campaign"},
        title="Leads per Campaign",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(**_LAYOUT)
    return fig


def bar_geographic(df_geo) -> go.Figure:
    """Horizontal bar chart of leads by phone-derived country.

    Parameters
    ----------
    df_geo : pd.DataFrame
        Output of analysis.geographic_breakdown() with columns
        'phone_country', 'count', 'pct'.

    Returns
    -------
    go.Figure
    """
    fig = px.bar(
        df_geo.sort_values("count"),
        x="count",
        y=config.COL_PHONE_COUNTRY,
        orientation="h",
        text="pct",
        color_discrete_sequence=[config.COLORS["accent"]],
        labels={"count": "Number of Leads", config.COL_PHONE_COUNTRY: "Country"},
        title="Lead Origin by Phone Country Code",
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(**_LAYOUT)
    return fig


def hist_response_time(df) -> go.Figure:
    """Histogram of response time in hours.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched dataframe with response_time_hours column.

    Returns
    -------
    go.Figure
    """
    fig = px.histogram(
        df.dropna(subset=[config.COL_RESPONSE_HOURS]),
        x=config.COL_RESPONSE_HOURS,
        nbins=30,
        color_discrete_sequence=[config.COLORS["light_blue"]],
        labels={config.COL_RESPONSE_HOURS: "Response Time (hours)"},
        title="Response Time Distribution",
    )
    fig.update_layout(**_LAYOUT, bargap=0.05)
    return fig


def funnel_chart(df_funnel) -> go.Figure:
    """Funnel chart of lead pipeline stages.

    Parameters
    ----------
    df_funnel : pd.DataFrame
        Output of analysis.funnel_summary() with columns
        'funnel_stage' and 'count'.

    Returns
    -------
    go.Figure
    """
    ordered = (
        df_funnel
        .set_index(config.COL_FUNNEL_STAGE)
        .reindex([s for s in config.FUNNEL_ORDER if s in df_funnel[config.COL_FUNNEL_STAGE].values])
        .reset_index()
    )
    fig = go.Figure(
        go.Funnel(
            y=ordered[config.COL_FUNNEL_STAGE],
            x=ordered["count"],
            textinfo="value+percent initial",
            marker=dict(color=config.PALETTE[: len(ordered)]),
        )
    )
    fig.update_layout(title="Lead Funnel", **_LAYOUT)
    return fig
