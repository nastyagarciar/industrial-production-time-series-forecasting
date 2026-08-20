"""Reusable utilities for monthly industrial-production forecasting.

This public portfolio module does not bundle the original coursework dataset.
It provides consistent parsing, holdout splitting, model fitting and metrics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX


def parse_monthly_ipi(data: pd.DataFrame) -> pd.Series:
    """Convert Date values such as '1975M01' into a monthly time series."""
    required = {"Date", "IPI Nacional"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    dates = pd.PeriodIndex(
        data["Date"].astype(str).str.replace("M", "-", regex=False),
        freq="M",
    ).to_timestamp()

    return pd.Series(
        data["IPI Nacional"].astype(float).to_numpy(),
        index=dates,
        name="IPI_Nacional",
    )


def seasonal_holdout(series: pd.Series, horizon: int = 12):
    """Reserve a common holdout horizon for every compared model."""
    if horizon <= 0 or horizon >= len(series):
        raise ValueError("Invalid forecast horizon.")
    return series.iloc[:-horizon], series.iloc[-horizon:]


def fit_ets(train: pd.Series):
    """Fit the selected damped-trend / multiplicative-seasonality ETS model."""
    return ExponentialSmoothing(
        train,
        trend="add",
        damped_trend=True,
        seasonal="mul",
        seasonal_periods=12,
        initialization_method="estimated",
    ).fit(optimized=True, use_brute=True)


def fit_sarima(train: pd.Series):
    """Fit the SARIMA specification selected in the corrected auto-ARIMA run."""
    return SARIMAX(
        train,
        order=(2, 1, 1),
        seasonal_order=(2, 0, 2, 12),
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False)


def regression_metrics(actual: pd.Series, predicted: pd.Series) -> dict[str, float]:
    """Return MAE, RMSE and MAPE for aligned forecasts."""
    actual = pd.Series(actual, dtype=float)
    predicted = pd.Series(predicted, index=actual.index, dtype=float)

    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "RMSE": float(mean_squared_error(actual, predicted) ** 0.5),
        "MAPE_pct": float(
            np.mean(np.abs((actual - predicted) / actual)) * 100
        ),
    }
