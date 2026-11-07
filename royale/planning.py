"""Retrospective demand alignment of fixed-budget operational review days.

    Selection consumes frozen forecasts only. Observed wagers are used only to
    evaluate demand coverage. Uniform allocation has an exact k/7 expected share
    for the same k review-day slots, without assuming labor or revenue effects.
"""
import numpy as np
import pandas as pd

from royale import money
from royale.model import KINDS, LABELS


def choose_days(forecasts: pd.DataFrame, kind: str, slots: int = 2) -> pd.DataFrame:
    """Choose k days per complete Mon–Sun week; ties use earliest date.

    Incomplete boundary weeks and weeks with missing dates are excluded from
    every policy. Do not use observed demand, or tune slots against holdout.
    """
    if kind not in KINDS:
        raise ValueError('Unknown forecast kind')
    if isinstance(slots, bool) or not isinstance(slots, (int, np.integer)) or not 1 <= slots <= 7:
        raise ValueError('slots must be an integer from 1 to 7')
    column = f'{kind}_prediction_usd'
    days = forecasts[['gaming_date', column]].copy()
    days['gaming_date'] = pd.to_datetime(days.gaming_date)
    if days.gaming_date.isna().any() or days.gaming_date.duplicated().any():
        raise ValueError('Dates must be valid and unique')
    if not np.isfinite(days[column]).all() or (days[column] < 0).any():
        raise ValueError('Forecasts must be finite and nonnegative')
    days['week'] = days.gaming_date.dt.to_period('W-SUN').dt.start_time
    days = days[days.groupby('week').gaming_date.transform('size').eq(7)].copy()
    days = days.sort_values(['week', column, 'gaming_date'], ascending=[True, False, True])
    days['priority_day'] = days.groupby('week').cumcount() < slots
    return days.sort_values('gaming_date').reset_index(drop=True)


def evaluate_planning(forecasts: pd.DataFrame, slots: int = 2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare policies on identical complete weeks and equal review-day budgets.

    Includes a paired week-bootstrap interval for coverage gain versus uniform
    allocation: 2,000 resamples, seed 86, at least three complete weeks. This is
    exploratory uncertainty across observed weeks, not a July benefit interval.
    """
    rows, schedules = [], []
    for kind in KINDS:
        chosen = choose_days(forecasts, kind, slots)
        if chosen.empty:
            continue
        chosen = chosen.merge(forecasts[['gaming_date', 'coin_in_usd']].assign(
            gaming_date=lambda d: pd.to_datetime(d.gaming_date)), on='gaming_date', validate='one_to_one')
        chosen['model'] = LABELS[kind]
        chosen['kind'] = kind
        schedules.append(chosen)
        chosen['covered_coin_in'] = chosen.coin_in_usd.where(chosen.priority_day, 0)
        weekly = chosen.groupby('week').agg(total=('coin_in_usd', 'sum'), covered=('covered_coin_in', 'sum'))
        total, covered = weekly.total.sum(), weekly.covered.sum()
        share = money.hold(covered, total)
        low = high = float('nan')
        if len(weekly) >= 3 and total > 0:
            rng = np.random.default_rng(86)
            samples = rng.integers(0, len(weekly), size=(2000, len(weekly)))
            denominators = weekly.total.to_numpy()[samples].sum(axis=1)
            numerators = weekly.covered.to_numpy()[samples].sum(axis=1)
            valid = denominators > 0
            gains = numerators[valid] / denominators[valid] - slots / 7
            if len(gains):
                low, high = np.quantile(gains, [.025, .975])
        rows.append(dict(kind=kind, model=LABELS[kind], weeks=len(weekly),
                         review_days=int(chosen.priority_day.sum()), observed_days=len(chosen),
                         covered_coin_in_usd=covered, uniform_expected_coin_in_usd=total * slots / 7,
                         demand_share=share, uniform_share=slots / 7,
                         gain_pp=None if share is None else 100 * (share - slots / 7),
                         gain_low_pp=100 * low, gain_high_pp=100 * high))
    return pd.DataFrame(rows), pd.concat(schedules, ignore_index=True) if schedules else pd.DataFrame()
