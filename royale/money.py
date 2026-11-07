"""Money-math helpers. Every page uses these so the math is the same everywhere.

Conventions (GUIDE.md and DATASET.md):
- Ratios are ratios of SUMS, never means of daily ratios.
- `_cents` are integer cents; `_usd` are dollars. Convert once, at the edge.
- Hold = house win / coin-in. Theo = coin-in x (1 - RTP). Luck residual (machine view)
  = house win - theo. Player view flips the sign: tracked net + theo.
- Exposure: compare per available hour or per unit of coin-in, not raw totals.
  Scheduled hours come from calendar_day.scheduled_seconds (2025-03-08 has 23 h).

Every function accepts pandas Series, lists or numpy arrays (DECIMAL columns from DuckDB
are fine; they are cast to float). Ratios return None when the denominator sums to zero.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _f(x) -> pd.Series:
    """Coerce to a float Series (handles Decimal, int, list, scalar). NaN stays NaN."""
    if isinstance(x, pd.Series):
        return x.astype(float)
    return pd.Series(np.atleast_1d(np.asarray(x, dtype=float)))


def _sum(x) -> float:
    return float(_f(x).sum())


def _ratio(num: float, den: float) -> float | None:
    return None if den == 0 else num / den


def cents_to_usd(cents):
    """Integer cents -> dollars (float). Works on scalars and Series."""
    if isinstance(cents, pd.Series):
        return cents.astype(float) / 100.0
    if isinstance(cents, np.ndarray):
        return cents.astype(float) / 100.0
    return float(cents) / 100.0


def hold(house_win, coin_in) -> float | None:
    """Ratio of sums: sum(house_win) / sum(coin_in). None when coin_in sums to zero."""
    return _ratio(_sum(house_win), _sum(coin_in))


def theo(coin_in, rtp) -> float:
    """Expected house win: sum(coin_in * (1 - rtp)). rtp is per row or a scalar."""
    c = _f(coin_in)
    r = rtp if np.isscalar(rtp) else _f(rtp).to_numpy()
    return float((c.to_numpy() * (1.0 - np.asarray(r, dtype=float))).sum())


def luck_residual(house_win, theo_) -> float:
    """Machine view: sum(house_win) - sum(theo). Positive means luckier than expected for the house."""
    return _sum(house_win) - _sum(theo_)


def luck_z(house_win, theo_, sum_bet_squared, payout_multiplier_variance) -> float | None:
    """Standardised luck: how many standard deviations house win sits from theo.

        z = (sum(house_win) - sum(theo)) / sqrt(sum(sum_bet_squared * payout_multiplier_variance))

    Why: each spin's house win is bet x (1 - multiplier), so its variance is
    bet^2 x Var(multiplier). Spins are independent, so variances add across spins, rows
    and days; machine_day.sum_bet_squared already sums bet^2 over a day's spins.

    Units: sum_bet_squared is in cents^2 and payout_multiplier_variance (game_math) is
    unitless, so the denominator is in cents. house_win and theo_ MUST be in cents too
    (machine_day.house_win_cents, theo_cents). Passing dollars understates |z| by 100x.
    Pass payout_multiplier_variance per row (join game_math on config_id) or as a scalar.

    Assumes independent spins and the configured multiplier distribution (no leak); a
    large |z| is a lead to inspect, not a finding. None when the variance sums to zero.
    """
    bsq = _f(sum_bet_squared).to_numpy()
    pv = payout_multiplier_variance
    pv = pv if np.isscalar(pv) else _f(pv).to_numpy()
    var = float((bsq * np.asarray(pv, dtype=float)).sum())
    if var <= 0:
        return None
    return luck_residual(house_win, theo_) / math.sqrt(var)


def availability(available_seconds, scheduled_seconds) -> float | None:
    """Ratio of sums: sum(available) / sum(scheduled). None when scheduled sums to zero."""
    return _ratio(_sum(available_seconds), _sum(scheduled_seconds))


def per_available_hour(amount, available_hours) -> float | None:
    """sum(amount) / sum(available_hours). The exposure-adjusted rate. None when hours sum to zero."""
    return _ratio(_sum(amount), _sum(available_hours))


def comp_reinvestment(comp_cost, theo_) -> float | None:
    """Redeemed comp economic cost / theo, ratio of sums. None when theo sums to zero."""
    return _ratio(_sum(comp_cost), _sum(theo_))


def concentration_share(values, top_fraction: float) -> float | None:
    """Share of sum(values) held by the top `top_fraction` of rows (e.g. 0.01 for the top 1%).

    The top group is ceil(n * top_fraction) rows (at least 1), ranked by value descending.
    None when there are no rows or values sum to zero.
    """
    if not 0 < top_fraction <= 1:
        raise ValueError("top_fraction must be in (0, 1]")
    v = _f(values).dropna().sort_values(ascending=False)
    total = float(v.sum())
    if v.empty or total == 0:
        return None
    k = max(1, math.ceil(len(v) * top_fraction))
    return float(v.iloc[:k].sum()) / total
