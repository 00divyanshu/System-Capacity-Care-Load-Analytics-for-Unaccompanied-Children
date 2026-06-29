# System Capacity & Care Load Analytics for Unaccompanied Children

**A Healthcare Operations and Policy Analytics Report**

## Abstract

This report presents an end-to-end analytical framework for monitoring system capacity and care-load pressure in the Unaccompanied Alien Children care pipeline. The project transforms CBP and HHS daily operational records into validated time-series data, operational KPIs, anomaly flags, stress-state classifications, exploratory findings, and forecast outputs. The framework is designed for policy analysts, healthcare operations teams, humanitarian response planners, and portfolio reviewers who need a transparent view of intake pressure, HHS care burden, discharge throughput, backlog accumulation, and operational sustainability.

## 1. Introduction

The Unaccompanied Alien Children program operates as a dynamic care pipeline. Children may first enter CBP custody, then move into HHS care for sheltering, medical screening, case management, behavioral health support, and eventual discharge to vetted sponsors or other approved placements. This pipeline has both humanitarian and operational dimensions: the system must protect child welfare while maintaining sufficient bed capacity, clinical readiness, case-management throughput, and sponsor-processing capability.

Raw daily data is valuable, but it does not automatically answer operational questions. Decision-makers need to know whether care load is rising or falling, whether discharges are keeping pace with transfers, when backlog risk is accumulating, and whether current pressure is normal, watch-level, strained, or relief-oriented.

## 2. Problem Statement

The core problem is the absence of a centralized analytical framework that continuously translates daily UAC operational records into capacity intelligence. Without a repeatable framework, stakeholders may see individual counts but miss the relationship between intake, transfer, HHS census, discharge throughput, volatility, and sustained pressure periods.

This project addresses that gap by creating a reproducible analytics pipeline and Streamlit dashboard that convert raw operational records into actionable healthcare capacity indicators.

## 3. Stakeholders

- HHS/ORR leadership responsible for shelter capacity, care standards, and sponsor-placement throughput.
- CBP coordination teams monitoring custody load and transfer urgency.
- Shelter network operators managing beds, staffing, clinical screening, and case workflows.
- Healthcare and behavioral health teams planning screening and care support.
- Policy analysts and oversight bodies assessing system sustainability.
- Nonprofit and child-welfare partners supporting operational response and reunification pathways.

## 4. Dataset Overview

The dataset contains daily operational records from `2023-01-12` through `2025-12-21`. The raw CSV has `1170` rows and `6` columns. After dropping fully blank trailing rows, `720` usable observations remain. The full date range contains `1075` calendar days, of which `720` are observed reporting dates and `355` are missing reporting dates.

| Field | Business Meaning | Analytical Use |
|---|---|---|
| Date | Reporting date | Time-series index and aggregation key |
| Children apprehended and placed in CBP custody | Upstream inflow | Intake pressure signal |
| Children in CBP custody | Point-in-time CBP load | Short-term holding pressure |
| Children transferred out of CBP custody | Transfer flow | HHS intake pressure |
| Children in HHS Care | Point-in-time HHS census | Primary care-load and shelter-capacity measure |
| Children discharged from HHS Care | Exit flow | Throughput and relief capacity |

## 5. Data Cleaning and Validation

The cleaning process preserves operational meaning rather than deleting inconvenient records. Fully blank trailing rows are removed as file artifacts. Dates are parsed into datetime values, count fields are converted to numeric values, and HHS care counts with thousands separators are cleaned. The data is sorted chronologically and expanded to a complete daily index.

Because the dataset has missing calendar dates, the pipeline flags missing dates explicitly. Stock variables such as CBP custody, HHS care, and total system load are interpolated for continuous trend analysis. Flow variables such as transfers and discharges remain observed-only unless a downstream chart or model explicitly handles missingness. This prevents the dashboard from inventing daily activity that was not reported.

Validation results:

- Fully blank raw rows removed: `450`
- Duplicate full rows: `0`
- Duplicate dates: `0`
- Negative count records: `0`
- Transfers greater than same-day CBP custody: `86` records
- Discharges greater than same-day HHS care: `0` records
- Zero-transfer records affecting discharge-offset ratio: `3` records

## 6. KPI Framework

| KPI | Formula | Interpretation | Recommended Visualization |
|---|---|---|---|
| Total System Load | CBP Custody + HHS Care | Total number of children under immediate federal care load | Line chart with rolling average |
| Net Daily Intake | Transfers out of CBP - HHS Discharges | Positive values indicate backlog pressure; negative values indicate relief | Diverging bar chart |
| Care Load Growth Rate | Day-over-day percent change in Total System Load | Speed of system load expansion or contraction | Line chart |
| Discharge Offset Ratio | HHS Discharges / Transfers out of CBP | Ratio above 1 means discharges exceed transfers | KPI card and trend line |
| Care Load Volatility Index | Rolling standard deviation of Total System Load | Instability in operational load | Area or line chart |
| Backlog Indicator | Sustained positive net intake | Multi-day pressure accumulation | Timeline/state indicator |

## 7. Exploratory Data Analysis

Total system load peaked at 11,762 children on 2023-12-20 and reached its lowest observed level of 2,002 on 2025-08-24. The observed average total system load is `6,232.8` children, with average HHS care load of `6,061.3` and average CBP custody load of `171.5`. HHS care dominates total system load, which means capacity planning should focus heavily on shelter census, clinical readiness, and case-management throughput.

Average observed net intake was -44.7 children per reporting day, meaning discharges generally exceeded transfers over the full period. This means the full-period average shows discharge relief, but localized backlog windows still matter. A system can have negative average net intake overall while still facing short periods where transfers exceed discharges and create operational pressure.

The highest observed total system load was `11,762` children on `2023-12-20`. The lowest observed total system load was `2,002` children on `2025-08-24`. This large spread shows that the system operates across substantially different capacity regimes and requires monitoring that can distinguish ordinary fluctuations from meaningful strain.

## 8. Capacity Stress Analysis

The dashboard classifies system state as Normal, Watch, Strained, Relief, or Missing Report. The classification combines total-load thresholds, sustained positive or negative net intake, and rolling volatility. The intent is not to assign fault, but to support early warning and operational prioritization.

Observed reporting days by state: Normal: 317; Watch: 183; Strained: 40; Relief: 180.

Quality and stress review identified `375` observed days with at least one operational alert or spike flag. The most important validation anomaly is the transfer-to-custody rule: transfers exceed same-day CBP custody on `86` observed records. These rows are retained and flagged because they may reflect reporting timing, definitional differences, or batch updates rather than simple data errors.

## 9. Forecasting

Forecasting is useful for planning, but not for deterministic prediction. The model comparison includes moving average, exponential smoothing, SARIMA, Prophet, Random Forest, and XGBoost when available. Models are evaluated with time-based train/test splits using MAE, RMSE, and MAPE where denominator behavior is safe.

Best validation results by target: Discharge Volume: Random Forest (MAE 3.3, RMSE 3.9); Net Daily Intake: Random Forest (MAE 5.5, RMSE 6.6); HHS Care Load: Random Forest (MAE 157.4, RMSE 186.9); Total System Load: Random Forest (MAE 161.4, RMSE 190.8).

Forecast interpretation should remain cautious because policy changes, reporting gaps, border conditions, sponsor-processing shifts, and operational decisions can change the trajectory quickly. Forecast outputs should therefore support scenario planning, not replace expert judgment.

## 10. Key Findings

1. HHS care load is the dominant component of total system load, making shelter and care census the main capacity-planning focus.
2. Net intake is negative on average, suggesting discharge throughput exceeded transfers over the full observed period.
3. Localized positive net-intake windows still create backlog risk and should be monitored as early-warning signals.
4. Missing reporting dates are material and should remain visible in all operational analysis.
5. Logical anomalies should be flagged for review rather than removed, especially when they may reflect reporting definitions or timing.
6. Forecasting is suitable for portfolio-grade planning analysis, but limitations must be clearly stated.

## 11. Recommendations

- Maintain a daily executive dashboard with total load, HHS care load, net intake pressure, discharge offset ratio, and volatility.
- Use sustained positive net intake as a trigger for backlog review and sponsor-processing support.
- Review transfer/custody anomalies with source documentation before treating them as errors.
- Pair forecasts with policy-event context, staffing data, shelter capacity, and sponsor-processing metrics.
- Expand the dataset with facility capacity, geography, length of stay, age/acuity mix, staffing, and medical-complexity fields.

## 12. Limitations

The dataset does not include official bed capacity, facility-level geography, age group, medical acuity, length of stay, case-management workload, staffing levels, sponsor-processing status, or policy-event indicators. Missing calendar dates also limit precision for daily flow analysis. As a result, the project should be interpreted as a capacity intelligence framework, not a complete causal model of the UAC care system.

## 13. Conclusion

This project converts raw UAC operational records into a transparent healthcare operations analytics system. It supports data validation, KPI monitoring, stress classification, EDA, forecasting, and dashboard-based decision support. The final product is designed to be useful for policy analytics, humanitarian response planning, healthcare operations storytelling, and a professional data analytics portfolio.
