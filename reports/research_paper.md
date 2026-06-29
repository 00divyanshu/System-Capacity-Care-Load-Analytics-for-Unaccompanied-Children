# System Capacity & Care Load Analytics for Unaccompanied Children

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
The dataset contains `720` usable nonblank records from `2023-01-12` through `2025-12-21`. The raw file includes `450` fully blank trailing rows. There are `355` missing calendar dates, so complete daily indexing is created with explicit missing-date flags.

## Methodology
The pipeline loads the raw CSV, removes only fully blank rows, standardizes field names, parses dates and counts, validates business rules, creates a complete daily index, interpolates stock variables for continuous capacity views, and leaves flow variables as observed unless explicitly modeled. Feature engineering then computes load, net intake, rolling averages, volatility, cumulative flows, backlog flags, and stress states.

## EDA
Total system load peaked at 11,762 children on 2023-12-20 and reached its lowest observed level of 2,002 on 2025-08-24. Average observed net intake was -44.7 children per reporting day, meaning discharges generally exceeded transfers over the full period. Distribution analysis shows a large decline in HHS care load from late 2023 highs into 2025 lows, while daily flow metrics remain volatile and policy-sensitive.

## KPI Analysis
Total system load combines CBP custody and HHS care. Net intake compares transfers with discharges. Discharge offset ratio measures whether exits keep pace with transfers. Volatility captures instability in capacity load. Backlog accumulation identifies sustained positive net-intake windows.

## Capacity Stress Analysis
Stress states are assigned using high-load thresholds, sustained positive net intake, relief windows, and rolling volatility. The highest observed total load was `11,762` on `2023-12-20`. The lowest observed total load was `2,002` on `2025-08-24`.

## Forecasting
Forecasting is suitable as a planning aid, not as a deterministic operational prediction. Reporting gaps, policy changes, and non-random shocks limit accuracy. The implemented framework compares moving average, exponential smoothing, SARIMA, Prophet, Random Forest, and XGBoost when installed. Current best model summary: Discharge Volume: Random Forest (RMSE 3.9); Net Daily Intake: Random Forest (RMSE 6.6); HHS Care Load: SARIMA (RMSE 129.2); Total System Load: SARIMA (RMSE 164.0).

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
