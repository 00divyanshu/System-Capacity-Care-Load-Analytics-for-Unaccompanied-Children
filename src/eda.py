from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .config import DATE_COL, FIGURES_DIR, NUMERIC_COLUMNS


def data_understanding_table() -> pd.DataFrame:
    rows = [
        {
            "Column Name": "Date",
            "Description": "Operational reporting date",
            "Data Type": "datetime",
            "Business Meaning": "The day associated with custody, transfer, care, and discharge counts.",
            "Analytical Importance": "Time-series index for trend, rolling, seasonality, and forecast analysis.",
        },
        {
            "Column Name": "Children apprehended and placed in CBP custody*",
            "Description": "Daily children entering CBP custody",
            "Data Type": "integer",
            "Business Meaning": "Upstream demand entering the federal care pipeline.",
            "Analytical Importance": "Early signal of intake pressure and potential future HHS demand.",
        },
        {
            "Column Name": "Children in CBP custody",
            "Description": "Point-in-time CBP custody count",
            "Data Type": "integer",
            "Business Meaning": "Current short-term holding load before transfer.",
            "Analytical Importance": "Measures immediate border-side pressure and transfer urgency.",
        },
        {
            "Column Name": "Children transferred out of CBP custody",
            "Description": "Daily transfers out of CBP custody",
            "Data Type": "integer",
            "Business Meaning": "Flow moving from CBP custody toward HHS care or another disposition.",
            "Analytical Importance": "Primary inflow pressure on HHS care resources.",
        },
        {
            "Column Name": "Children in HHS Care",
            "Description": "Point-in-time HHS care count",
            "Data Type": "integer",
            "Business Meaning": "Current child population requiring shelter, healthcare, case management, and sponsor work.",
            "Analytical Importance": "Core capacity-load measure for operational planning.",
        },
        {
            "Column Name": "Children discharged from HHS Care",
            "Description": "Daily exits from HHS care",
            "Data Type": "integer",
            "Business Meaning": "Sponsor placements or other exits that relieve HHS care capacity.",
            "Analytical Importance": "Measures throughput and relief capacity against intake.",
        },
    ]
    return pd.DataFrame(rows)


def summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    columns = NUMERIC_COLUMNS + [
        "total_system_load",
        "net_daily_intake",
        "discharge_offset_ratio",
        "care_load_volatility_index",
    ]
    return df[columns].describe().T.reset_index().rename(columns={"index": "metric"})


def correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    columns = NUMERIC_COLUMNS + [
        "total_system_load",
        "net_daily_intake",
        "discharge_offset_ratio",
        "care_load_volatility_index",
    ]
    return df[columns].corr(numeric_only=True).round(3)


def generate_eda_figures(df: pd.DataFrame, output_dir: Path = FIGURES_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures: list[tuple[str, go.Figure]] = []

    load_fig = go.Figure()
    load_fig.add_trace(
        go.Scatter(
            x=df[DATE_COL],
            y=df["total_system_load"],
            mode="lines",
            name="Total system load",
        )
    )
    load_fig.add_trace(
        go.Scatter(
            x=df[DATE_COL],
            y=df["total_system_load_14d_avg"],
            mode="lines",
            name="14-day average",
        )
    )
    load_fig.update_layout(
        title="Total System Load Over Time",
        xaxis_title="Date",
        yaxis_title="Children under CBP/HHS care load",
    )
    figures.append(("total_system_load_trend.html", load_fig))

    cbp_hhs_fig = px.line(
        df,
        x=DATE_COL,
        y=["cbp_custody", "hhs_care"],
        title="CBP Custody vs HHS Care Load",
        labels={"value": "Children", "variable": "Metric"},
    )
    figures.append(("cbp_vs_hhs_load.html", cbp_hhs_fig))

    net_fig = px.bar(
        df[df["is_observed"]],
        x=DATE_COL,
        y="net_daily_intake",
        color="system_state",
        title="Observed Net Intake and Stress State",
        labels={"net_daily_intake": "Transfers minus discharges"},
    )
    figures.append(("net_intake_backlog_trends.html", net_fig))

    vol_fig = px.line(
        df,
        x=DATE_COL,
        y="care_load_volatility_index",
        title="Care Load Volatility Index",
        labels={"care_load_volatility_index": "14-day rolling standard deviation"},
    )
    figures.append(("care_load_volatility.html", vol_fig))

    state_counts = (
        df[df["is_observed"]]["system_state"]
        .value_counts()
        .rename_axis("system_state")
        .reset_index(name="days")
    )
    state_fig = px.bar(
        state_counts,
        x="system_state",
        y="days",
        title="Observed Days by System State",
        labels={"system_state": "System state", "days": "Observed reporting days"},
    )
    figures.append(("system_state_distribution.html", state_fig))

    paths = []
    for filename, figure in figures:
        path = output_dir / filename
        figure.write_html(path)
        paths.append(path)
    return paths


def write_eda_tables(df: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "data_understanding": data_understanding_table(),
        "summary_statistics": summary_statistics(df),
        "correlation_matrix": correlation_table(df).reset_index(),
    }
    written = {}
    for name, table in tables.items():
        path = output_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        written[name] = str(path)
    return written


def business_interpretations(df: pd.DataFrame) -> dict[str, str]:
    observed = df[df["is_observed"]].copy()
    peak = observed.loc[observed["total_system_load"].idxmax()]
    trough = observed.loc[observed["total_system_load"].idxmin()]
    mean_net = observed["net_daily_intake"].mean()
    strain_days = int(observed["system_state"].eq("Strained").sum())
    relief_days = int(observed["system_state"].eq("Relief").sum())
    return {
        "load_trend": (
            f"Total system load peaked at {peak['total_system_load']:,.0f} children on "
            f"{peak[DATE_COL].date()} and reached its lowest observed level of "
            f"{trough['total_system_load']:,.0f} on {trough[DATE_COL].date()}."
        ),
        "net_intake": (
            f"Average observed net intake was {mean_net:,.1f} children per reporting day, "
            "meaning discharges generally exceeded transfers over the full period."
        ),
        "stress_states": (
            f"The classification logic identifies {strain_days} strained observed reporting days "
            f"and {relief_days} relief observed reporting days."
        ),
    }
