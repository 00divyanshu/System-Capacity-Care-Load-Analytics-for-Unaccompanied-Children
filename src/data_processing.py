from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    CLEAN_FILE,
    DAILY_FILE,
    DATE_COL,
    FLOW_COLUMNS,
    MONTHLY_FILE,
    NUMERIC_COLUMNS,
    PROFILE_FILE,
    RAW_FILE,
    RAW_TO_CANONICAL_COLUMNS,
    STOCK_COLUMNS,
    WEEKLY_FILE,
)


@dataclass(frozen=True)
class DataQualityProfile:
    raw_shape: tuple[int, int]
    nonblank_shape: tuple[int, int]
    blank_rows: int
    duplicate_rows: int
    duplicate_dates: int
    date_min: str
    date_max: str
    observed_dates: int
    calendar_days: int
    missing_calendar_days: int
    negative_counts: dict[str, int]
    transfers_gt_cbp_custody: int
    discharges_gt_hhs_care: int
    zero_transfers: int

    def to_dict(self) -> dict:
        return {
            "raw_shape": list(self.raw_shape),
            "nonblank_shape": list(self.nonblank_shape),
            "blank_rows": self.blank_rows,
            "duplicate_rows": self.duplicate_rows,
            "duplicate_dates": self.duplicate_dates,
            "date_min": self.date_min,
            "date_max": self.date_max,
            "observed_dates": self.observed_dates,
            "calendar_days": self.calendar_days,
            "missing_calendar_days": self.missing_calendar_days,
            "negative_counts": self.negative_counts,
            "transfers_gt_cbp_custody": self.transfers_gt_cbp_custody,
            "discharges_gt_hhs_care": self.discharges_gt_hhs_care,
            "zero_transfers": self.zero_transfers,
        }


def load_raw_data(path: Path = RAW_FILE) -> pd.DataFrame:
    """Load the source CSV as strings so cleaning decisions stay explicit."""
    return pd.read_csv(path, dtype=str)


def clean_observed_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Drop file-artifact blank rows, standardize columns, parse dates/counts."""
    expected = set(RAW_TO_CANONICAL_COLUMNS)
    missing = expected.difference(raw_df.columns)
    if missing:
        raise ValueError(f"Missing expected source columns: {sorted(missing)}")

    df = raw_df.dropna(how="all").rename(columns=RAW_TO_CANONICAL_COLUMNS).copy()
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(
            df[column].astype(str).str.replace(",", "", regex=False).str.strip(),
            errors="coerce",
        )

    if df[DATE_COL].isna().any():
        bad_rows = df[df[DATE_COL].isna()].index.tolist()
        raise ValueError(f"Date parsing failed for rows: {bad_rows[:10]}")
    if df[NUMERIC_COLUMNS].isna().any().any():
        bad_cols = df[NUMERIC_COLUMNS].columns[df[NUMERIC_COLUMNS].isna().any()].tolist()
        raise ValueError(f"Numeric parsing failed for columns: {bad_cols}")

    return df.sort_values(DATE_COL).reset_index(drop=True)


def add_validation_flags(df: pd.DataFrame) -> pd.DataFrame:
    flagged = df.copy()
    flagged["flag_negative_count"] = flagged[NUMERIC_COLUMNS].lt(0).any(axis=1)
    flagged["flag_transfers_gt_cbp_custody"] = (
        flagged["transferred_out_cbp"] > flagged["cbp_custody"]
    )
    flagged["flag_discharges_gt_hhs_care"] = (
        flagged["discharged_hhs"] > flagged["hhs_care"]
    )
    flagged["flag_zero_transfer_ratio"] = flagged["transferred_out_cbp"].eq(0)
    return flagged


def build_daily_panel(observed_df: pd.DataFrame) -> pd.DataFrame:
    """Create complete daily panel while clearly separating observed and imputed values."""
    observed = add_validation_flags(observed_df)
    full_dates = pd.date_range(
        observed[DATE_COL].min(),
        observed[DATE_COL].max(),
        freq="D",
    )
    daily = (
        observed.set_index(DATE_COL)
        .reindex(full_dates)
        .rename_axis(DATE_COL)
        .reset_index()
    )
    daily["is_observed"] = daily["cbp_custody"].notna()
    daily["flag_missing_date"] = ~daily["is_observed"]

    for column in STOCK_COLUMNS:
        daily[f"{column}_observed"] = daily[column]
        daily[column] = daily[column].interpolate(method="linear", limit_direction="both")

    for column in FLOW_COLUMNS:
        daily[f"{column}_observed"] = daily[column]

    flag_columns = [
        "flag_negative_count",
        "flag_transfers_gt_cbp_custody",
        "flag_discharges_gt_hhs_care",
        "flag_zero_transfer_ratio",
    ]
    for column in flag_columns:
        daily[column] = daily[column].fillna(False).astype(bool)

    daily["flag_stock_interpolated"] = daily["flag_missing_date"]
    return daily


def create_quality_profile(raw_df: pd.DataFrame, observed_df: pd.DataFrame, daily_df: pd.DataFrame) -> DataQualityProfile:
    return DataQualityProfile(
        raw_shape=raw_df.shape,
        nonblank_shape=raw_df.dropna(how="all").shape,
        blank_rows=int(raw_df.isna().all(axis=1).sum()),
        duplicate_rows=int(raw_df.dropna(how="all").duplicated().sum()),
        duplicate_dates=int(observed_df[DATE_COL].duplicated().sum()),
        date_min=str(observed_df[DATE_COL].min().date()),
        date_max=str(observed_df[DATE_COL].max().date()),
        observed_dates=int(observed_df[DATE_COL].nunique()),
        calendar_days=int(daily_df.shape[0]),
        missing_calendar_days=int(daily_df["flag_missing_date"].sum()),
        negative_counts={column: int((observed_df[column] < 0).sum()) for column in NUMERIC_COLUMNS},
        transfers_gt_cbp_custody=int(
            (observed_df["transferred_out_cbp"] > observed_df["cbp_custody"]).sum()
        ),
        discharges_gt_hhs_care=int(
            (observed_df["discharged_hhs"] > observed_df["hhs_care"]).sum()
        ),
        zero_transfers=int(observed_df["transferred_out_cbp"].eq(0).sum()),
    )


def save_outputs(
    raw_df: pd.DataFrame,
    observed_df: pd.DataFrame,
    daily_df: pd.DataFrame,
    profile: DataQualityProfile,
) -> None:
    CLEAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    observed_df.to_csv(CLEAN_FILE, index=False)
    daily_df.to_csv(DAILY_FILE, index=False)

    weekly = (
        daily_df.set_index(DATE_COL)
        .resample("W-SUN")
        .agg(
            total_system_load=("total_system_load", "mean"),
            hhs_care=("hhs_care", "mean"),
            cbp_custody=("cbp_custody", "mean"),
            net_daily_intake=("net_daily_intake", "sum"),
            transferred_out_cbp=("transferred_out_cbp", "sum"),
            discharged_hhs=("discharged_hhs", "sum"),
            observed_days=("is_observed", "sum"),
        )
        .reset_index()
    )
    weekly.to_csv(WEEKLY_FILE, index=False)

    monthly = (
        daily_df.set_index(DATE_COL)
        .resample("MS")
        .agg(
            total_system_load=("total_system_load", "mean"),
            hhs_care=("hhs_care", "mean"),
            cbp_custody=("cbp_custody", "mean"),
            net_daily_intake=("net_daily_intake", "sum"),
            transferred_out_cbp=("transferred_out_cbp", "sum"),
            discharged_hhs=("discharged_hhs", "sum"),
            observed_days=("is_observed", "sum"),
        )
        .reset_index()
    )
    monthly.to_csv(MONTHLY_FILE, index=False)

    PROFILE_FILE.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")


def run_processing(path: Path = RAW_FILE) -> tuple[pd.DataFrame, pd.DataFrame, DataQualityProfile]:
    from .features import add_capacity_features

    raw_df = load_raw_data(path)
    observed_df = clean_observed_data(raw_df)
    daily_df = build_daily_panel(observed_df)
    daily_df = add_capacity_features(daily_df)
    profile = create_quality_profile(raw_df, observed_df, daily_df)
    save_outputs(raw_df, observed_df, daily_df, profile)
    return observed_df, daily_df, profile


if __name__ == "__main__":
    observed, daily, quality = run_processing()
    print(json.dumps(quality.to_dict(), indent=2))
