from __future__ import annotations

import pandas as pd

from src.artifacts import write_all_artifacts
from src.config import DAILY_FILE, FORECAST_FILE, MODEL_COMPARISON_FILE, REPORTS_DIR
from src.data_processing import run_processing
from src.eda import generate_eda_figures, write_eda_tables
from src.forecasting import run_forecasts


def main() -> None:
    observed_df, daily_df, profile = run_processing()
    generate_eda_figures(daily_df)
    write_eda_tables(daily_df, REPORTS_DIR)

    comparison, forecasts = run_forecasts(daily_df)
    MODEL_COMPARISON_FILE.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(MODEL_COMPARISON_FILE, index=False)
    forecasts.to_csv(FORECAST_FILE, index=False)

    write_all_artifacts(daily_df, comparison)
    print("Pipeline complete")
    print(f"Observed rows: {len(observed_df)}")
    print(f"Daily rows: {len(daily_df)}")
    print(f"Missing calendar days: {profile.missing_calendar_days}")
    print(f"Processed data: {DAILY_FILE}")
    print(f"Forecast comparison: {MODEL_COMPARISON_FILE}")


if __name__ == "__main__":
    main()
