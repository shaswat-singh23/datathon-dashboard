"""Daily payout diagnostics and period-specific machine inspection intervals."""
from __future__ import annotations

import numpy as np
import pandas as pd

from royale import money

NAME = "q1_leak"
# Two-sided normal tail probability * 310 machines is below 5% (Bonferroni).
Z_THRESHOLD = 3.8
SQL = """
SELECT m.machine_id, m.gaming_date, p.location_id, f.bank_id,
       m.config_id, g.theme AS game, g.volatility_class,
       m.paid_spins, m.available_seconds, m.coin_in_cents,
       m.payout_cents, m.house_win_cents, m.sum_bet_squared,
       g.configured_rtp, g.payout_multiplier_variance
FROM machine_day m
JOIN calendar_day c USING (gaming_date)
JOIN placements p ON p.machine_id = m.machine_id
 AND c.gaming_day_start_utc >= p.effective_from_utc
 AND (p.effective_to_utc IS NULL OR c.gaming_day_start_utc < p.effective_to_utc)
JOIN floor_locations f ON f.location_id = p.location_id
JOIN game_math g ON g.config_id = m.config_id
WHERE m.active AND m.location_id IS NOT NULL
"""


def _statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Add ratio-of-sums RTP and normal intervals in cents, without clipping."""
    result = df.copy()
    result["observed_rtp"] = [
        money.hold(payout, coin) for payout, coin in
        zip(result.payout_cents, result.coin_in_cents)
    ]
    expected_hold = [
        money.hold(theo, coin) for theo, coin in
        zip(result.theo_cents, result.coin_in_cents)
    ]
    result["configured_rtp"] = [
        1 - value if value is not None else np.nan for value in expected_hold
    ]
    # The variance column already sums squared bets times game variance.
    result["payout_z"] = [
        -value if value is not None else np.nan
        for value in (
            money.luck_z(win, theo, variance, 1.0)
            for win, theo, variance in zip(
                result.house_win_cents, result.theo_cents, result.variance_cents2
            )
        )
    ]
    valid = (result.coin_in_cents > 0) & (result.variance_cents2 > 0) & (result.paid_spins > 0)
    result["rtp_se"] = np.sqrt(result.variance_cents2.where(valid)) / result.coin_in_cents.where(valid)
    result.loc[~valid, "payout_z"] = np.nan
    result["ci_lower"] = result.observed_rtp - Z_THRESHOLD * result.rtp_se
    result["ci_upper"] = result.observed_rtp + Z_THRESHOLD * result.rtp_se
    result["inspection_candidate"] = (
        (result.configured_rtp < result.ci_lower) | (result.configured_rtp > result.ci_upper)
    ) & valid
    result["unadjusted_95_flag"] = (result.payout_z.abs() > 1.96) & valid
    return result


def build(con) -> pd.DataFrame:
    """One row per active, on-floor machine-day; preserve rows and meter sums."""
    before = con.sql("""SELECT count(*), sum(coin_in_cents), sum(payout_cents)
        FROM machine_day WHERE active AND location_id IS NOT NULL""").fetchall()[0]
    df = con.sql(SQL).df()
    assert len(df) == before[0], f"join changed row count: {before[0]} -> {len(df)}"
    assert not df.duplicated(["machine_id", "gaming_date"]).any(), "duplicate machine-day"
    assert int(df.coin_in_cents.sum()) == before[1], "join changed wagers"
    assert int(df.payout_cents.sum()) == before[2], "join changed payouts"
    mismatches = con.sql("""SELECT count(*) FROM machine_day m
        JOIN calendar_day c USING (gaming_date)
        JOIN placements p ON p.machine_id = m.machine_id
         AND c.gaming_day_start_utc >= p.effective_from_utc
         AND (p.effective_to_utc IS NULL OR c.gaming_day_start_utc < p.effective_to_utc)
        WHERE m.active AND m.location_id IS NOT NULL AND m.location_id <> p.location_id
    """).fetchall()[0][0]
    assert mismatches == 0, "placement disagrees with machine-day location"
    df["configured_rtp"] = df.configured_rtp.astype(float)
    df["payout_multiplier_variance"] = df.payout_multiplier_variance.astype(float)
    assert df.configured_rtp.between(0, 1).all(), "invalid configured RTP"
    assert (df.payout_multiplier_variance > 0).all(), "invalid game variance"
    assert (df.sum_bet_squared >= 0).all(), "invalid squared bets"
    assert (df.coin_in_cents - df.payout_cents == df.house_win_cents).all(), "meters disagree"
    df["theo_cents"] = [money.theo(coin, rtp) for coin, rtp in zip(df.coin_in_cents, df.configured_rtp)]
    df["variance_cents2"] = df.sum_bet_squared * df.payout_multiplier_variance
    # Daily intervals are stored for inspection; the page recomputes from sums.
    return _statistics(df).sort_values(["gaming_date", "machine_id"]).reset_index(drop=True)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate each machine's statistics for the selected dates and bank."""
    result = df.groupby("machine_id", sort=True).agg(
        active_days=("gaming_date", "size"),
        paid_spins=("paid_spins", "sum"),
        available_seconds=("available_seconds", "sum"),
        coin_in_cents=("coin_in_cents", "sum"),
        payout_cents=("payout_cents", "sum"),
        house_win_cents=("house_win_cents", "sum"),
        theo_cents=("theo_cents", "sum"),
        variance_cents2=("variance_cents2", "sum"),
        game=("game", lambda values: ", ".join(sorted(values.unique()))),
        volatility_class=("volatility_class", lambda values: values.iloc[0] if values.nunique() == 1 else "mixed"),
    )
    result = _statistics(result)
    result["available_hours"] = result.available_seconds / 3600
    result["excess_payout_per_hour"] = [
        money.per_available_hour(money.cents_to_usd(-money.luck_residual(win, theo)), hours)
        for win, theo, hours in zip(result.house_win_cents, result.theo_cents, result.available_hours)
    ]
    result["direction"] = np.where(result.payout_z > 0, "above configured RTP", "below configured RTP")
    result.loc[result.payout_z.isna(), "direction"] = "insufficient play/variance"
    return result.sort_values("payout_z", key=lambda values: values.abs(), ascending=False)


def volatility_check(summary: pd.DataFrame) -> pd.DataFrame:
    """Compare screened-machine flag rates, keeping mixed configurations separate."""
    return summary.groupby("volatility_class", sort=True).agg(
        machines=("inspection_candidate", "size"),
        testable_machines=("payout_z", "count"),
        candidates=("inspection_candidate", "sum"),
        unadjusted_95_flags=("unadjusted_95_flag", "sum"),
        median_rtp_se=("rtp_se", "median"),
    ).assign(
        flag_rate=lambda rows: rows.candidates / rows.testable_machines.replace(0, np.nan),
        unadjusted_95_rate=lambda rows: rows.unadjusted_95_flags / rows.testable_machines.replace(0, np.nan),
    )
