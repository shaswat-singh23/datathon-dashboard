"""Money-math helpers. Every page uses these so the math is the same everywhere.

Conventions (GUIDE.md and DATASET.md):
- Ratios are ratios of SUMS, never means of daily ratios.
- `_cents` are integer cents; `_usd` are dollars. Convert once, at the edge.
- Hold = house win / coin-in. Theo = coin-in x (1 - RTP). Luck residual (machine view)
  = house win - theo. Player view flips the sign: tracked net + theo.
- Exposure: compare per available hour or per unit of coin-in, not raw totals.
  Scheduled hours come from calendar_day.scheduled_seconds (2025-03-08 has 23 h).

Issue #14 implements these and tests them in tests/test_money.py. Until then they raise.
"""
from __future__ import annotations

import pandas as pd

_TODO = "Implemented by issue #14 (money-math helpers)."


def cents_to_usd(cents) -> float:
    """Integer cents -> dollars (float). Works on scalars and Series."""
    raise NotImplementedError(_TODO)


def hold(house_win: pd.Series, coin_in: pd.Series) -> float:
    """Ratio of sums: sum(house_win) / sum(coin_in). None when coin_in sums to zero."""
    raise NotImplementedError(_TODO)


def theo(coin_in: pd.Series, rtp: pd.Series) -> float:
    """Expected house win: sum(coin_in * (1 - rtp)) when rtp is per row."""
    raise NotImplementedError(_TODO)


def luck_residual(house_win: pd.Series, theo_: pd.Series) -> float:
    """Machine view: sum(house_win) - sum(theo). Positive means luckier than expected for the house."""
    raise NotImplementedError(_TODO)


def luck_z(house_win: pd.Series, theo_: pd.Series, sum_bet_squared: pd.Series,
           payout_multiplier_variance: pd.Series) -> float:
    """Standardised luck: residual / sqrt(sum(bet^2 * variance)). How many SDs from theo.

    sum_bet_squared is in cents^2 (machine_day); keep units consistent with house_win."""
    raise NotImplementedError(_TODO)


def availability(available_seconds: pd.Series, scheduled_seconds: pd.Series) -> float:
    """Ratio of sums: sum(available) / sum(scheduled). None when scheduled sums to zero."""
    raise NotImplementedError(_TODO)


def per_available_hour(amount: pd.Series, available_hours: pd.Series) -> float:
    """sum(amount) / sum(available_hours). The exposure-adjusted rate."""
    raise NotImplementedError(_TODO)


def comp_reinvestment(comp_cost: pd.Series, theo_: pd.Series) -> float:
    """Redeemed comp economic cost / theo, ratio of sums. None when theo sums to zero."""
    raise NotImplementedError(_TODO)


def concentration_share(values: pd.Series, top_fraction: float) -> float:
    """Share of sum(values) held by the top `top_fraction` of rows (e.g. 0.01 for the top 1%)."""
    raise NotImplementedError(_TODO)
