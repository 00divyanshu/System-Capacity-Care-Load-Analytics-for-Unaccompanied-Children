from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import DATE_COL, PROFILE_FILE, REPORTS_DIR
from .eda import business_interpretations, data_understanding_table


def _profile_text() -> dict:
    if PROFILE_FILE.exists():
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    return {}


def _top_windows(df: pd.DataFrame, state: str, limit: int = 5) -> pd.DataFrame:
    obs = df[df["is_observed"]].copy()
    mask = obs["system_state"].eq(state)
    groups = mask.ne(mask.shift()).cumsum()
    rows = []
    for _, group in obs[mask].groupby(groups):
        rows.append(
            {
                "start": group[DATE_COL].min().date(),
                "end": group[DATE_COL].max().date(),
                "observed_days": len(group),
                "avg_total_load": round(group["total_system_load"].mean(), 1),
                "sum_net_intake": round(group["net_daily_intake"].sum(), 1),
            }
        )
    return pd.DataFrame(rows).sort_values(["observed_days", "avg_total_load"], ascending=False).head(limit)


def write_research_paper(df: pd.DataFrame, comparison: pd.DataFrame | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    profile = _profile_text()
    interp = business_interpretations(df)
    observed = df[df["is_observed"]]
    peak = observed.loc[observed["total_system_load"].idxmax()]
    trough = observed.loc[observed["total_system_load"].idxmin()]
    best_models = "Forecast comparison was not available."
    if comparison is not None and not comparison.empty:
        ok = comparison[comparison["status"].eq("ok")].copy()
        if not ok.empty:
            winners = ok.sort_values("rmse").groupby("target").head(1)
            best_models = "; ".join(
                f"{row.target}: {row.model} (RMSE {row.rmse:,.1f})"
                for row in winners.itertuples(index=False)
            )

    content = f"""# System Capacity & Care Load Analytics for Unaccompanied Children

## Abstract
This study develops an operational analytics framework for monitoring capacity pressure in the Unaccompanied Alien Children care pipeline. The framework transforms daily CBP and HHS operational records into capacity KPIs, anomaly flags, stress-state classifications, exploratory insights, and forecast-ready time series.

## Introduction
The UAC care pathway involves intake into CBP custody, transfer to HHS care, medical and welfare support, and eventual discharge to vetted sponsors or other placements. Capacity risk emerges when incoming transfers exceed discharge throughput or when HHS care load remains high for sustained periods.

## Background
The system is a flow-and-stock operation. Transfers and discharges are flows; CBP custody and HHS care counts are stocks. A policy analytics dashboard must distinguish these concepts because missing flow records should not be treated as zero activity.

## Problem Statement
The raw data does not by itself provide a continuous view of care load, intake-discharge balance, backlog accumulation, or operational relief. Decision-makers need a repeatable framework for identifying periods of strain and translating trends into resource-planning intelligence.

## Objectives
- Measure total care system load across CBP custody and HHS care.
- Detect intake pressure, backlog windows, relief periods, and volatility spikes.
- Preserve data-quality concerns through flags instead of deleting operationally meaningful records.
- Produce forecast outputs with clear limitations for planning discussions.
- Deliver a recruiter-ready dashboard, documentation, and policy summary.

## Dataset
The dataset contains `{profile.get('nonblank_shape', ['unknown'])[0]}` usable nonblank records from `{profile.get('date_min')}` through `{profile.get('date_max')}`. The raw file includes `{profile.get('blank_rows')}` fully blank trailing rows. There are `{profile.get('missing_calendar_days')}` missing calendar dates, so complete daily indexing is created with explicit missing-date flags.

## Methodology
The pipeline loads the raw CSV, removes only fully blank rows, standardizes field names, parses dates and counts, validates business rules, creates a complete daily index, interpolates stock variables for continuous capacity views, and leaves flow variables as observed unless explicitly modeled. Feature engineering then computes load, net intake, rolling averages, volatility, cumulative flows, backlog flags, and stress states.

## EDA
{interp['load_trend']} {interp['net_intake']} Distribution analysis shows a large decline in HHS care load from late 2023 highs into 2025 lows, while daily flow metrics remain volatile and policy-sensitive.

## KPI Analysis
Total system load combines CBP custody and HHS care. Net intake compares transfers with discharges. Discharge offset ratio measures whether exits keep pace with transfers. Volatility captures instability in capacity load. Backlog accumulation identifies sustained positive net-intake windows.

## Capacity Stress Analysis
Stress states are assigned using high-load thresholds, sustained positive net intake, relief windows, and rolling volatility. The highest observed total load was `{peak['total_system_load']:,.0f}` on `{peak[DATE_COL].date()}`. The lowest observed total load was `{trough['total_system_load']:,.0f}` on `{trough[DATE_COL].date()}`.

## Forecasting
Forecasting is suitable as a planning aid, not as a deterministic operational prediction. Reporting gaps, policy changes, and non-random shocks limit accuracy. The implemented framework compares moving average, exponential smoothing, SARIMA, Prophet, Random Forest, and XGBoost when installed. Current best model summary: {best_models}.

## Findings
- HHS care load dominates total system load, so shelter and healthcare capacity planning should focus on HHS census trends.
- Net intake is negative on average, indicating sustained discharge relief across the full period, but localized backlog windows still occur.
- Missing reporting days are material and must be flagged to avoid overstating daily precision.
- Logical transfer/custody rule failures are retained as anomaly flags for review rather than removed.

## Recommendations
- Use total system load and HHS care load as executive capacity indicators.
- Monitor sustained positive net intake as an early warning of backlog accumulation.
- Review transfer greater than CBP custody anomalies with source documentation.
- Pair forecasts with scenario planning and policy context before operational decisions.

## Limitations
The dataset does not include facility capacity, length of stay, age/acuity mix, geography, medical complexity, staffing, or sponsor-processing detail. Forecasts should therefore be interpreted as time-series signals, not complete capacity projections.

## Conclusion
The project converts daily operational records into a decision-support system for humanitarian healthcare capacity monitoring. It is designed to be transparent, auditable, and portfolio-ready.
"""
    path = REPORTS_DIR / "research_paper.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_executive_summary(df: pd.DataFrame) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    interp = business_interpretations(df)
    state_counts = df[df["is_observed"]]["system_state"].value_counts()
    content = f"""# Executive Summary

## Key Findings
- {interp['load_trend']}
- {interp['net_intake']}
- Observed reporting days by state: {state_counts.to_dict()}.

## Capacity Risks
- HHS care load is the main driver of system load.
- Sustained positive net intake can create backlog pressure even when annual average net intake is negative.
- Missing reporting dates require caution in daily interpretations.

## Policy Implications
- Leadership should track load, throughput, and relief together rather than relying on a single custody count.
- High-load and high-volatility periods should trigger readiness review for shelter beds, clinical screening, case management, and sponsor-processing capacity.

## Recommendations
- Maintain a daily capacity dashboard with anomaly flags.
- Use stress-state thresholds as an early-warning screen, not a punitive performance score.
- Treat forecasts as planning ranges and pair them with policy/event context.
"""
    path = REPORTS_DIR / "executive_summary.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_presentation_structure() -> Path:
    content = """# PowerPoint Presentation Structure

## Slide 1: Project Title
Content: System Capacity & Care Load Analytics for Unaccompanied Children.
Visual: Clean title slide with care-system pipeline motif.
Speaker Notes: Introduce the project as a healthcare operations and policy analytics framework.

## Slide 2: Policy and Operational Context
Content: CBP intake, HHS transfer, care delivery, sponsor discharge.
Visual: Four-stage process diagram.
Speaker Notes: Emphasize that this is a dynamic care pipeline, not a static census problem.

## Slide 3: Business Problem
Content: Need to monitor care load, capacity strain, intake-discharge balance, backlog, and sustainability.
Visual: Problem framing with key decision questions.
Speaker Notes: Explain why raw daily data needs analytical translation.

## Slide 4: Dataset Overview
Content: Date range, columns, row counts, data-quality notes.
Visual: Data understanding table.
Speaker Notes: Note missing calendar dates and anomaly-flag approach.

## Slide 5: KPI Framework
Content: Total load, net intake, volatility, backlog rate, discharge offset ratio.
Visual: KPI card mockup.
Speaker Notes: Tie each KPI to a planning decision.

## Slide 6: System Load Trend
Content: Total system load and 14-day rolling average.
Visual: Line chart.
Speaker Notes: Explain peak and low-load periods.

## Slide 7: CBP vs HHS Load
Content: Compare short-term custody load to HHS care census.
Visual: Dual-line or small-multiple chart.
Speaker Notes: Show that HHS care dominates system capacity burden.

## Slide 8: Net Intake and Backlog
Content: Transfers minus discharges and sustained positive windows.
Visual: Bar chart with positive and negative periods.
Speaker Notes: Positive net intake signals backlog accumulation.

## Slide 9: Stress-State Classification
Content: Normal, Watch, Strained, Relief logic.
Visual: Timeline colored by state.
Speaker Notes: Stress states are decision aids, not labels of fault.

## Slide 10: Forecasting
Content: Model comparison and selected forecast outputs.
Visual: Forecast line with validation metrics table.
Speaker Notes: Forecasts are planning tools with operational caveats.

## Slide 11: Dashboard Demo
Content: Streamlit sections and filters.
Visual: Dashboard screenshot placeholder.
Speaker Notes: Explain interactive use cases for policy and operations teams.

## Slide 12: Recommendations
Content: Monitoring cadence, anomaly review, scenario planning, capacity readiness.
Visual: Action-oriented recommendation table.
Speaker Notes: Close with how the framework supports better operational preparedness.
"""
    path = Path("presentation") / "slide_structure.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_resume_linkedin_content() -> Path:
    content = """# Resume and LinkedIn Content

## Resume Bullets
- Built an end-to-end healthcare capacity analytics project for the UAC care pipeline using Python, pandas, scikit-learn, Plotly, and Streamlit.
- Engineered operational KPIs for total system load, net intake pressure, discharge offset, backlog accumulation, and care load volatility across 2023-2025 daily records.
- Designed anomaly-aware validation logic for missing reporting dates, inconsistent transfer/custody counts, zero-transfer ratios, and high-volatility periods.
- Developed a modular forecasting framework comparing baseline, classical time-series, and machine-learning models using MAE, RMSE, and MAPE.
- Delivered an interactive Streamlit dashboard and policy-facing reports translating technical trends into capacity-planning recommendations.

## ATS-Friendly Project Description
Developed a portfolio-grade healthcare operations analytics system to evaluate capacity strain, care load, intake-discharge balance, backlog accumulation, and forecasting for the Unaccompanied Alien Children program. Used Python, pandas, NumPy, Plotly, Seaborn, Matplotlib, scikit-learn, statsmodels, Prophet, XGBoost, and Streamlit. Produced modular data cleaning, validation, feature engineering, EDA, KPI analysis, stress classification, forecasting, executive reporting, and dashboard deployment artifacts.

## LinkedIn Post
I completed an end-to-end analytics project titled "System Capacity & Care Load Analytics for Unaccompanied Children."

The project transforms daily CBP and HHS operational data into a healthcare capacity intelligence framework covering total system load, net intake pressure, discharge offset, backlog accumulation, volatility, stress periods, relief periods, and forecasting.

What I built:
- A reproducible Python data pipeline
- Data validation and anomaly flags
- KPI and stress-state framework
- EDA and time-series analysis
- Forecast model comparison
- Interactive Streamlit dashboard
- Executive summary, research paper, and presentation structure

This project strengthened my ability to connect technical analytics with real-world healthcare operations, humanitarian response, and policy decision-making.
"""
    path = REPORTS_DIR / "resume_linkedin_content.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_all_artifacts(df: pd.DataFrame, comparison: pd.DataFrame | None = None) -> list[Path]:
    paths = [
        write_research_paper(df, comparison),
        write_executive_summary(df),
        write_presentation_structure(),
        write_resume_linkedin_content(),
    ]
    data_understanding_table().to_csv(REPORTS_DIR / "data_understanding_table.csv", index=False)
    return paths
