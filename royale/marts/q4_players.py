"""Q4: one row per carded player and gaming month, without raw-data joins.

Keep player IDs so period totals, group drills and concentration can be computed
without adding monthly distinct counts or averaging monthly percentages.
"""
import duckdb
import numpy as np
import pandas as pd

from royale.money import concentration_share

NAME = "q4_players"
QUERY = """
SELECT player_id, period_month,
       coalesce(home_region, 'Unknown') AS home_region,
       coalesce(age_band, 'Unknown') AS age_band,
       coalesce(opening_tier, 'Unknown') AS opening_tier,
       CAST(tracked_coin_in_usd AS DOUBLE) AS tracked_coin_in_usd,
       CAST(tracked_payout_usd AS DOUBLE) AS tracked_payout_usd,
       CAST(tracked_net_usd AS DOUBLE) AS tracked_net_usd,
       CAST(theo_usd AS DOUBLE) AS theo_usd,
       CAST(luck_residual_usd AS DOUBLE) AS luck_residual_usd
FROM player_period
ORDER BY period_month, player_id
"""
MONEY = ["tracked_coin_in_usd", "tracked_payout_usd", "tracked_net_usd", "theo_usd", "luck_residual_usd"]


def build(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    frame = con.sql(QUERY).df()
    source_rows = con.sql("SELECT count(*) FROM player_period").fetchall()[0][0]
    assert len(frame) == source_rows, "Player projection changed row count"
    assert not frame.duplicated(["player_id", "period_month"]).any()
    assert np.allclose(frame.tracked_net_usd, frame.tracked_payout_usd - frame.tracked_coin_in_usd, atol=1e-8, rtol=0)
    assert np.allclose(frame.luck_residual_usd, frame.tracked_net_usd + frame.theo_usd, atol=1e-8, rtol=0)
    # Net and luck are exact identities; derive them on read to keep the mart small.
    return frame.drop(columns=["tracked_net_usd", "luck_residual_usd"])


def outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    """Reconstruct player-view identities from the three stored dollar amounts."""
    frame = frame.copy()
    frame["tracked_net_usd"] = frame.tracked_payout_usd - frame.tracked_coin_in_usd
    frame["luck_residual_usd"] = frame.tracked_net_usd + frame.theo_usd
    return frame


def monthly_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Monthly active-player outcomes and independently ranked concentration.

    Active means positive tracked coin-in. Loss is max(-player net, 0), so
    winners do not create negative Lorenz weights. Each top fraction is rounded
    up, using all active players (including winners) as the population.
    """
    frame = outcomes(frame)
    rows = []
    for month, group in frame.groupby("period_month", sort=True):
        active = group[group.tracked_coin_in_usd > 0]
        losses = (-active.tracked_net_usd).clip(lower=0)
        row = {"period_month": month, "active_players": len(active),
               "ahead_share": (active.tracked_net_usd > 0).mean() if len(active) else np.nan,
               "gross_player_loss_usd": losses.sum()}
        row.update({col: group[col].sum() for col in MONEY})
        for label, values in [("coin_in", active.tracked_coin_in_usd), ("loss", losses)]:
            for pct in [1, 10]:
                row[f"top_{pct}pct_{label}_share"] = concentration_share(values, pct / 100)
        rows.append(row)
    return pd.DataFrame(rows)
