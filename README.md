# System Capacity & Care Load Analytics for Unaccompanied Children

## Project Overview
This portfolio-grade analytics project converts UAC daily operational records into capacity intelligence for the CBP-to-HHS care pipeline. It measures system load, intake-discharge balance, backlog accumulation, volatility, relief periods, and forecastable care-load trends.

## Problem Statement
Daily operational records exist, but they do not automatically show when the care system is under pressure, whether discharges are keeping pace with transfers, or when backlog risk is accumulating. This project creates a reproducible analytical framework and interactive dashboard for those decisions.

## Objectives
- Clean and validate daily CBP/HHS operational data.
- Engineer healthcare capacity KPIs and anomaly flags.
- Identify high-load, strained, watch, normal, and relief periods.
- Compare forecasting models for system load, HHS care, net intake, and discharges.
- Deliver dashboard, a polished research paper, and reproducible project documentation.

## Dataset Information
Source file: `data/raw/HHS_Unaccompanied_Alien_Children_Program.csv`

Columns:
- `Date`
- `Children apprehended and placed in CBP custody*`
- `Children in CBP custody`
- `Children transferred out of CBP custody`
- `Children in HHS Care`
- `Children discharged from HHS Care`

Initial inspection found 720 usable records from January 12, 2023 to December 21, 2025, plus 450 blank trailing rows and 355 missing calendar dates.

## Technologies Used
Python, pandas, NumPy, Plotly, Matplotlib, Seaborn, scikit-learn, statsmodels, Prophet, XGBoost, Streamlit, pytest.

## KPIs
- Total System Load = CBP Custody + HHS Care
- Net Daily Intake = Transfers out of CBP custody - HHS discharges
- Care Load Growth Rate = day-over-day percent change in total system load
- Discharge Offset Ratio = HHS discharges / transfers out of CBP custody
- Care Load Volatility Index = rolling standard deviation of total system load
- Backlog Indicator = sustained positive net intake

## Dashboard Features
- Date range selector
- Daily, weekly, and monthly views
- Metric toggles
- Rolling average controls
- Executive status strip and KPI summary cards
- Tabbed views for overview, stress analysis, forecasts, and data quality
- System state timeline
- Net intake and backlog visualization
- Forecast model comparison
- Anomaly review table
- Filtered data download

## Key Insights
- HHS care load is the dominant component of total system load.
- The dataset has material missing reporting dates, so missing-date flags are retained.
- Transfers exceed same-day CBP custody on 86 observed dates; these are flagged for review rather than removed.
- Forecasts are useful as planning signals, but policy shocks and reporting gaps limit deterministic interpretation.

## Installation
```bash
python -m pip install -r requirements.txt
```

## Run the Pipeline
```bash
python run_pipeline.py
```

## Launch the Dashboard
```bash
streamlit run app/streamlit_app.py
```

## Project Structure
```text
data/
  raw/                 Source CSV
  processed/           Cleaned data, daily feature table, trend tables, quality profile
notebooks/             Exploratory notebooks
src/                   Modular processing, feature, EDA, forecast, and reporting code
app/                   Streamlit application
outputs/
  figures/             EDA HTML charts
  forecasts/           Forecast outputs and model comparisons
  tables/              Generated EDA and data-understanding tables
paper/                 Standalone research/report paper
tests/                 Automated validation checks
```

## Future Improvements
- Add facility capacity, geography, length of stay, acuity, and staffing data.
- Build scenario forecasts under policy or surge assumptions.
- Add confidence intervals and model monitoring.
- Deploy the dashboard to Streamlit Community Cloud or another hosted environment.
