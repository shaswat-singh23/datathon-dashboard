"""Calendar-only forecasts, fit exclusively on Jan 1–Apr 30, 2025.

The constant, weekday mean and weekday-plus-linear-trend specifications are
fixed before holdout scoring. Predict uses dates only, never observed outcomes
or holdout-day lag features. No tourism, survey or future operations inputs.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

TRAIN_START = pd.Timestamp('2025-01-01')
TRAIN_END = pd.Timestamp('2025-04-30')
TEST_START = pd.Timestamp('2025-05-01')
TEST_END = pd.Timestamp('2025-06-30')
KINDS = ('constant', 'weekday', 'weekday_trend')
LABELS = {'constant': 'Constant training mean (baseline)', 'weekday': 'Weekday mean',
          'weekday_trend': 'Weekday + linear trend'}


def _dates(frame: pd.DataFrame) -> pd.DatetimeIndex:
    dates = pd.DatetimeIndex(pd.to_datetime(frame['gaming_date']))
    if dates.hasnans or dates.tz is not None:
        raise ValueError('gaming_date must contain valid timezone-naive gaming dates')
    return dates.normalize()


def _features(dates: pd.DatetimeIndex) -> np.ndarray:
    # Seven weekday intercepts plus elapsed days, with a fixed training origin.
    weekdays = np.eye(7)[dates.day_of_week]
    trend = np.asarray((dates - TRAIN_START).days, dtype=float) / 30
    return np.column_stack([weekdays, trend])


@dataclass(frozen=True)
class Forecast:
    kind: str
    coefficients: tuple[float, ...]
    training_rows: int
    training_end: pd.Timestamp

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        """Predict from gaming_date alone; other columns are deliberately ignored."""
        dates = _dates(frame)
        weights = np.asarray(self.coefficients)
        if self.kind == 'constant':
            values = np.full(len(dates), weights[0])
        elif self.kind == 'weekday':
            values = weights[dates.day_of_week]
        else:
            values = _features(dates) @ weights
        return np.maximum(values, 0)


def fit(frame: pd.DataFrame, kind: str = 'weekday') -> Forecast:
    """Fit on the fixed training window, even if passed later rows.

    Filtering precedes target conversion or validation. Holdout targets cannot
    influence coefficients, weekday means, clipping, or other fitting choices.
    Training requires finite nonnegative outcomes and all seven weekdays.
    """
    if kind not in KINDS:
        raise ValueError(f'Unknown forecast kind: {kind}')
    dates = _dates(frame)
    mask = (dates >= TRAIN_START) & (dates <= TRAIN_END)
    train_dates = dates[mask]
    target = frame.loc[mask, 'coin_in_usd'].to_numpy(dtype=float)
    if not len(target):
        raise ValueError('No rows in the training window')
    if train_dates.has_duplicates:
        raise ValueError('Duplicate training gaming dates')
    if not np.isfinite(target).all() or (target < 0).any():
        raise ValueError('Training coin-in must be finite and nonnegative')
    if set(train_dates.day_of_week) != set(range(7)):
        raise ValueError('Training must cover all seven weekdays')
    if kind == 'constant':
        weights = np.array([target.mean()])
    elif kind == 'weekday':
        weights = np.array([target[train_dates.day_of_week == day].mean() for day in range(7)])
    else:
        design = _features(train_dates)
        if np.linalg.matrix_rank(design) != design.shape[1]:
            raise ValueError('Insufficient training dates to fit weekday and trend')
        weights = np.linalg.lstsq(design, target, rcond=None)[0]
    return Forecast(kind, tuple(float(x) for x in weights), len(target), train_dates.max())


def predict(model: Forecast, frame: pd.DataFrame) -> np.ndarray:
    """Functional counterpart to Forecast.predict."""
    return model.predict(frame)
