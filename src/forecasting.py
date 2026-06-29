from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from .config import DATE_COL, FORECAST_HORIZON_DAYS, TARGET_COLUMNS, TEST_DAYS


@dataclass
class ForecastResult:
    target_name: str
    model_name: str
    mae: float | None
    rmse: float | None
    mape: float | None
    status: str
    reason: str
    forecast: pd.DataFrame


def _safe_mape(y_true: pd.Series, y_pred: np.ndarray) -> float | None:
    y = pd.Series(y_true).astype(float)
    nonzero = y.abs() > 1e-9
    if nonzero.sum() < max(5, len(y) * 0.5):
        return None
    return float((np.abs((y[nonzero] - y_pred[nonzero]) / y[nonzero])).mean() * 100)


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> tuple[float, float, float | None]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = _safe_mape(y_true.reset_index(drop=True), np.asarray(y_pred))
    return mae, rmse, mape


def _prepare_series(df: pd.DataFrame, column: str) -> pd.Series:
    series = df.set_index(DATE_COL)[column].astype(float).sort_index()
    return series.interpolate(method="time", limit_direction="both")


def _future_dates(series: pd.Series, horizon: int) -> pd.DatetimeIndex:
    start = series.index.max() + pd.Timedelta(days=1)
    return pd.date_range(start, periods=horizon, freq="D")


def _moving_average(series: pd.Series, horizon: int, window: int = 14) -> np.ndarray:
    value = series.tail(window).mean()
    return np.repeat(value, horizon)


def _random_forest_predictions(series: pd.Series, horizon: int) -> np.ndarray:
    frame = pd.DataFrame({"y": series})
    for lag in [1, 7, 14, 28]:
        frame[f"lag_{lag}"] = frame["y"].shift(lag)
    frame["dayofweek"] = frame.index.dayofweek
    frame["month"] = frame.index.month
    frame["time_idx"] = np.arange(len(frame))
    frame = frame.dropna()
    features = [c for c in frame.columns if c != "y"]
    model = RandomForestRegressor(n_estimators=250, random_state=42, min_samples_leaf=3)
    model.fit(frame[features], frame["y"])

    history = series.copy()
    preds = []
    for date in _future_dates(series, horizon):
        row = {
            "lag_1": history.iloc[-1],
            "lag_7": history.iloc[-7] if len(history) >= 7 else history.iloc[-1],
            "lag_14": history.iloc[-14] if len(history) >= 14 else history.iloc[-1],
            "lag_28": history.iloc[-28] if len(history) >= 28 else history.iloc[-1],
            "dayofweek": date.dayofweek,
            "month": date.month,
            "time_idx": len(history),
        }
        pred = float(model.predict(pd.DataFrame([row]))[0])
        preds.append(pred)
        history.loc[date] = pred
    return np.asarray(preds)


def _statsmodels_ets(series: pd.Series, horizon: int) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    model = ExponentialSmoothing(series, trend="add", seasonal=None, initialization_method="estimated")
    fit = model.fit(optimized=True)
    return np.asarray(fit.forecast(horizon))


def _statsmodels_arima(series: pd.Series, horizon: int) -> np.ndarray:
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    model = SARIMAX(
        series,
        order=(1, 1, 1),
        seasonal_order=(0, 1, 1, 7),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fit = model.fit(disp=False)
    return np.asarray(fit.forecast(horizon))


def _prophet_forecast(series: pd.Series, horizon: int) -> np.ndarray:
    from prophet import Prophet

    prophet_df = series.reset_index()
    prophet_df.columns = ["ds", "y"]
    model = Prophet(weekly_seasonality=True, yearly_seasonality=True, daily_seasonality=False)
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=horizon, freq="D")
    forecast = model.predict(future).tail(horizon)
    return forecast["yhat"].to_numpy()


def _xgboost_predictions(series: pd.Series, horizon: int) -> np.ndarray:
    from xgboost import XGBRegressor

    frame = pd.DataFrame({"y": series})
    for lag in [1, 7, 14, 28]:
        frame[f"lag_{lag}"] = frame["y"].shift(lag)
    frame["dayofweek"] = frame.index.dayofweek
    frame["month"] = frame.index.month
    frame["time_idx"] = np.arange(len(frame))
    frame = frame.dropna()
    features = [c for c in frame.columns if c != "y"]
    model = XGBRegressor(
        n_estimators=250,
        learning_rate=0.05,
        max_depth=3,
        subsample=0.9,
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(frame[features], frame["y"])

    history = series.copy()
    preds = []
    for date in _future_dates(series, horizon):
        row = {
            "lag_1": history.iloc[-1],
            "lag_7": history.iloc[-7] if len(history) >= 7 else history.iloc[-1],
            "lag_14": history.iloc[-14] if len(history) >= 14 else history.iloc[-1],
            "lag_28": history.iloc[-28] if len(history) >= 28 else history.iloc[-1],
            "dayofweek": date.dayofweek,
            "month": date.month,
            "time_idx": len(history),
        }
        pred = float(model.predict(pd.DataFrame([row]))[0])
        preds.append(pred)
        history.loc[date] = pred
    return np.asarray(preds)


def _evaluate_model(
    target_name: str,
    model_name: str,
    train: pd.Series,
    test: pd.Series,
    horizon: int,
    predictor: Callable[[pd.Series, int], np.ndarray],
) -> ForecastResult:
    try:
        test_pred = predictor(train, len(test))
        mae, rmse, mape = _metrics(test, test_pred)
        all_pred = predictor(pd.concat([train, test]), horizon)
        forecast_df = pd.DataFrame(
            {
                "date": _future_dates(pd.concat([train, test]), horizon),
                "target": target_name,
                "model": model_name,
                "forecast": all_pred,
            }
        )
        return ForecastResult(target_name, model_name, mae, rmse, mape, "ok", "", forecast_df)
    except Exception as exc:
        return ForecastResult(
            target_name,
            model_name,
            None,
            None,
            None,
            "skipped",
            str(exc),
            pd.DataFrame(columns=["date", "target", "model", "forecast"]),
        )


def run_forecasts(
    df: pd.DataFrame,
    horizon: int = FORECAST_HORIZON_DAYS,
    test_days: int = TEST_DAYS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    results: list[ForecastResult] = []
    model_registry: list[tuple[str, Callable[[pd.Series, int], np.ndarray]]] = [
        ("Moving Average", _moving_average),
        ("Random Forest", _random_forest_predictions),
        ("Exponential Smoothing", _statsmodels_ets),
        ("SARIMA", _statsmodels_arima),
        ("Prophet", _prophet_forecast),
        ("XGBoost", _xgboost_predictions),
    ]

    for target_name, column in TARGET_COLUMNS.items():
        series = _prepare_series(df, column)
        if len(series) <= test_days + 60:
            raise ValueError(f"Not enough data to forecast {target_name}")
        train = series.iloc[:-test_days]
        test = series.iloc[-test_days:]
        for model_name, predictor in model_registry:
            results.append(_evaluate_model(target_name, model_name, train, test, horizon, predictor))

    comparison = pd.DataFrame(
        [
            {
                "target": r.target_name,
                "model": r.model_name,
                "mae": r.mae,
                "rmse": r.rmse,
                "mape": r.mape,
                "status": r.status,
                "reason": r.reason,
            }
            for r in results
        ]
    )
    forecasts = pd.concat([r.forecast for r in results if not r.forecast.empty], ignore_index=True)
    return comparison, forecasts
