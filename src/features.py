from __future__ import annotations

import numpy as np
import pandas as pd

from .config import BACKLOG_MIN_DAYS, DATE_COL, FLOW_COLUMNS, ROLLING_WINDOWS, VOLATILITY_WINDOW


def _consecutive_true_runs(mask: pd.Series) -> pd.Series:
    groups = mask.ne(mask.shift()).cumsum()
    return mask.groupby(groups).cumcount().add(1).where(mask, 0)


def add_capacity_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add operational KPIs, rolling metrics, anomaly flags, and stress states."""
    out = df.copy().sort_values(DATE_COL).reset_index(drop=True)

    out["total_system_load"] = out["cbp_custody"] + out["hhs_care"]
    out["net_daily_intake"] = out["transferred_out_cbp"] - out["discharged_hhs"]
    out.loc[out["flag_missing_date"], "net_daily_intake"] = np.nan
    out["care_load_growth_rate"] = out["total_system_load"].pct_change()
    out["discharge_offset_ratio"] = out["discharged_hhs"] / out["transferred_out_cbp"].replace(0, np.nan)

    for window in ROLLING_WINDOWS:
        out[f"total_system_load_{window}d_avg"] = out["total_system_load"].rolling(window, min_periods=1).mean()
        out[f"hhs_care_{window}d_avg"] = out["hhs_care"].rolling(window, min_periods=1).mean()
        out[f"net_daily_intake_{window}d_avg"] = out["net_daily_intake"].rolling(window, min_periods=1).mean()

    out["care_load_volatility_index"] = (
        out["total_system_load"].rolling(VOLATILITY_WINDOW, min_periods=3).std().fillna(0)
    )
    out["net_intake_volatility_index"] = (
        out["net_daily_intake"].rolling(VOLATILITY_WINDOW, min_periods=3).std().fillna(0)
    )

    for column in FLOW_COLUMNS:
        out[f"cumulative_{column}"] = out[column].fillna(0).cumsum()
    out["cumulative_net_intake"] = out["net_daily_intake"].fillna(0).cumsum()

    observed_net_positive = out["net_daily_intake"].gt(0) & out["is_observed"]
    observed_net_negative = out["net_daily_intake"].lt(0) & out["is_observed"]
    out["positive_net_intake_run_days"] = _consecutive_true_runs(observed_net_positive)
    out["negative_net_intake_run_days"] = _consecutive_true_runs(observed_net_negative)
    out["backlog_indicator"] = out["positive_net_intake_run_days"].ge(BACKLOG_MIN_DAYS)
    out["relief_period_flag"] = out["negative_net_intake_run_days"].ge(BACKLOG_MIN_DAYS)

    load_q75 = out["total_system_load"].quantile(0.75)
    load_q90 = out["total_system_load"].quantile(0.90)
    volatility_q75 = out["care_load_volatility_index"].quantile(0.75)
    net_intake_q75 = out["net_daily_intake"].quantile(0.75)
    net_intake_q25 = out["net_daily_intake"].quantile(0.25)

    out["high_load_flag"] = out["total_system_load"].ge(load_q75)
    out["severe_load_flag"] = out["total_system_load"].ge(load_q90)
    out["volatility_spike_flag"] = out["care_load_volatility_index"].ge(volatility_q75)
    out["net_intake_spike_flag"] = out["net_daily_intake"].gt(net_intake_q75)
    out["net_intake_relief_spike_flag"] = out["net_daily_intake"].lt(net_intake_q25)
    out["strain_period_flag"] = (
        out["severe_load_flag"]
        | (out["high_load_flag"] & out["backlog_indicator"])
        | (out["backlog_indicator"] & out["volatility_spike_flag"])
    )

    conditions = [
        out["relief_period_flag"] & out["net_daily_intake"].lt(0),
        out["strain_period_flag"],
        out["high_load_flag"] | out["backlog_indicator"] | out["volatility_spike_flag"],
    ]
    choices = ["Relief", "Strained", "Watch"]
    out["system_state"] = np.select(conditions, choices, default="Normal")
    out.loc[out["flag_missing_date"], "system_state"] = "Missing Report"

    return out
