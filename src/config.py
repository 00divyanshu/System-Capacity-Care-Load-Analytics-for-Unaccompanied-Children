from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
FORECASTS_DIR = OUTPUTS_DIR / "forecasts"
REPORTS_DIR = PROJECT_ROOT / "reports"

RAW_FILE = RAW_DATA_DIR / "HHS_Unaccompanied_Alien_Children_Program.csv"
CLEAN_FILE = PROCESSED_DATA_DIR / "uac_clean_observed.csv"
DAILY_FILE = PROCESSED_DATA_DIR / "uac_daily_capacity_features.csv"
MONTHLY_FILE = PROCESSED_DATA_DIR / "uac_monthly_trends.csv"
WEEKLY_FILE = PROCESSED_DATA_DIR / "uac_weekly_trends.csv"
PROFILE_FILE = PROCESSED_DATA_DIR / "data_quality_profile.json"
MODEL_COMPARISON_FILE = FORECASTS_DIR / "model_comparison.csv"
FORECAST_FILE = FORECASTS_DIR / "forecast_outputs.csv"

RAW_TO_CANONICAL_COLUMNS = {
    "Date": "date",
    "Children apprehended and placed in CBP custody*": "apprehended_placed_cbp",
    "Children in CBP custody": "cbp_custody",
    "Children transferred out of CBP custody": "transferred_out_cbp",
    "Children in HHS Care": "hhs_care",
    "Children discharged from HHS Care": "discharged_hhs",
}

DATE_COL = "date"
FLOW_COLUMNS = [
    "apprehended_placed_cbp",
    "transferred_out_cbp",
    "discharged_hhs",
]
STOCK_COLUMNS = [
    "cbp_custody",
    "hhs_care",
]
NUMERIC_COLUMNS = FLOW_COLUMNS + STOCK_COLUMNS
TARGET_COLUMNS = {
    "Total System Load": "total_system_load",
    "HHS Care Load": "hhs_care",
    "Net Daily Intake": "net_daily_intake",
    "Discharge Volume": "discharged_hhs",
}

ROLLING_WINDOWS = [7, 14]
VOLATILITY_WINDOW = 14
BACKLOG_MIN_DAYS = 3
FORECAST_HORIZON_DAYS = 30
TEST_DAYS = 90

