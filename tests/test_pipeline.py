from __future__ import annotations

import pandas as pd

from src.data_processing import build_daily_panel, clean_observed_data, load_raw_data
from src.features import add_capacity_features


def test_cleaning_contract():
    raw = load_raw_data()
    observed = clean_observed_data(raw)

    assert raw.shape == (1170, 6)
    assert observed.shape == (720, 6)
    assert observed["date"].min() == pd.Timestamp("2023-01-12")
    assert observed["date"].max() == pd.Timestamp("2025-12-21")
    assert observed["date"].duplicated().sum() == 0
    assert observed.isna().sum().sum() == 0


def test_daily_panel_and_validation_flags():
    observed = clean_observed_data(load_raw_data())
    daily = add_capacity_features(build_daily_panel(observed))

    assert len(daily) == 1075
    assert int(daily["flag_missing_date"].sum()) == 355
    assert int(daily["flag_transfers_gt_cbp_custody"].sum()) == 86
    assert int(daily["flag_discharges_gt_hhs_care"].sum()) == 0
    assert int(daily["flag_zero_transfer_ratio"].sum()) == 3


def test_feature_formulas_on_first_observed_row():
    observed = clean_observed_data(load_raw_data())
    daily = add_capacity_features(build_daily_panel(observed))
    row = daily[daily["date"].eq(pd.Timestamp("2023-01-12"))].iloc[0]

    assert row["total_system_load"] == row["cbp_custody"] + row["hhs_care"]
    assert row["net_daily_intake"] == row["transferred_out_cbp"] - row["discharged_hhs"]
    assert round(row["discharge_offset_ratio"], 6) == round(row["discharged_hhs"] / row["transferred_out_cbp"], 6)
    assert row["system_state"] in {"Normal", "Watch", "Strained", "Relief", "Missing Report"}
