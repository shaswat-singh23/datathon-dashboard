"""Same-title location comparisons; monthly totals split by walkway-closure phase.

Traffic is a zone/month/phase measure repeated on machine rows. Deduplicate that
key before aggregating it. Rates always use sums of money and available hours.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from royale import money
from royale.marts.q1_machines import SQL as MACHINE_SQL

NAME = "q1_location"
KEY = ["machine_id", "month", "zone_id", "bank_id", "config_id", "phase"]
TRAFFIC_KEY = ["month", "zone_id", "phase"]
SUMS = ["coin_in_cents", "house_win_cents", "available_seconds", "scheduled_seconds", "machine_days"]

SQL = f"""
WITH daily AS ({MACHINE_SQL}),
closure AS (
    SELECT min(closed_from_utc) AS start_utc, max(closed_to_utc) AS end_utc
    FROM floor_walkways WHERE closed_from_utc IS NOT NULL
),
dates AS (
    SELECT c.gaming_date, c.gaming_day_start_utc, c.gaming_day_end_utc,
           date_trunc('month', gaming_date)::DATE AS month,
           CASE WHEN gaming_day_end_utc <= start_utc THEN 'Before closure'
                WHEN gaming_day_start_utc >= end_utc THEN 'After reopening'
                ELSE 'During closure' END AS phase
    FROM calendar_day c CROSS JOIN closure
),
affected AS (
    SELECT zone_a AS zone_id FROM floor_walkways WHERE closed_from_utc IS NOT NULL
    UNION SELECT zone_b FROM floor_walkways WHERE closed_from_utc IS NOT NULL
),
traffic AS (
    SELECT d.month, t.zone_id, d.phase,
           sum(t.entries_count) AS zone_entries,
           sum(CASE WHEN t.entries_count IS NOT NULL THEN t.coverage_minutes ELSE 0 END) / 60.0
               AS coverage_hours
    FROM zone_traffic_hourly t
    JOIN dates d ON t.hour_start_utc >= d.gaming_day_start_utc
                AND t.hour_start_utc < d.gaming_day_end_utc
    GROUP BY d.month, t.zone_id, d.phase
),
machine_month AS (
    SELECT m.machine_id, d.month, m.zone_id, m.zone_name, m.bank_id,
           m.config_id, m.game, d.phase,
           sum(m.coin_in_cents) AS coin_in_cents,
           sum(m.house_win_cents) AS house_win_cents,
           sum(m.available_seconds) AS available_seconds,
           sum(m.scheduled_seconds) AS scheduled_seconds,
           count(*) AS machine_days
    FROM daily m JOIN dates d USING (gaming_date)
    GROUP BY m.machine_id, d.month, m.zone_id, m.zone_name, m.bank_id,
             m.config_id, m.game, d.phase
)
SELECT m.*, t.zone_entries, t.coverage_hours,
       a.zone_id IS NOT NULL AS closure_endpoint
FROM machine_month m
LEFT JOIN traffic t USING (month, zone_id, phase)
LEFT JOIN affected a USING (zone_id)
ORDER BY m.machine_id, m.month, m.zone_id, m.bank_id, m.config_id, m.phase
"""


def build(con):
    # This dataset has one closure interval. Fail rather than silently combining
    # separate closures into an invented continuous intervention.
    intervals = con.sql("""SELECT count(*) FROM (
        SELECT DISTINCT closed_from_utc, closed_to_utc FROM floor_walkways
        WHERE closed_from_utc IS NOT NULL)""").fetchall()[0][0]
    assert intervals == 1, "location mart expects one walkway closure interval"
    source = con.sql("""SELECT count(*), sum(coin_in_cents), sum(house_win_cents),
        sum(available_seconds), sum(c.scheduled_seconds)
        FROM machine_day m JOIN calendar_day c USING (gaming_date)
        WHERE m.active AND m.location_id IS NOT NULL""").fetchall()[0]
    daily = con.sql(MACHINE_SQL).df()
    assert len(daily) == source[0] and not daily.duplicated(["machine_id", "gaming_date"]).any()
    assert not con.sql("""SELECT sensor_id, hour_start_utc FROM zone_traffic_hourly
        GROUP BY ALL HAVING count(*) > 1""").fetchall(), "duplicate traffic sensor-hour"
    df = con.sql(SQL).df()
    assert not df.duplicated(KEY).any(), "monthly joins changed the grain"
    actual = tuple(int(df[k].sum()) for k in
                   ["machine_days", "coin_in_cents", "house_win_cents", "available_seconds", "scheduled_seconds"])
    assert actual == source, f"monthly joins changed totals: {source} -> {actual}"
    traffic = df.drop_duplicates(TRAFFIC_KEY)
    raw_traffic = con.sql("""SELECT sum(entries_count),
        sum(CASE WHEN entries_count IS NOT NULL THEN coverage_minutes ELSE 0 END)/60.0
        FROM zone_traffic_hourly t JOIN calendar_day c
        ON hour_start_utc >= gaming_day_start_utc AND hour_start_utc < gaming_day_end_utc""").fetchall()[0]
    assert np.allclose([traffic.zone_entries.sum(), traffic.coverage_hours.sum()], raw_traffic)
    df["coin_in_per_available_hour"] = [
        money.per_available_hour(money.cents_to_usd(c), s / 3600)
        for c, s in zip(df.coin_in_cents, df.available_seconds)
    ]
    df["zone_entries_per_coverage_hour"] = df.zone_entries / df.coverage_hours.replace(0, np.nan)
    return df


def rates(df, keys):
    """Money/exposure totals at the requested grain (never average row rates)."""
    result = df.groupby(keys, observed=True, dropna=False)[SUMS].sum().reset_index()
    result["coin_in_usd"] = money.cents_to_usd(result.coin_in_cents)
    result["available_hours"] = result.available_seconds / 3600
    result["coin_in_per_available_hour"] = [
        money.per_available_hour(c, h) for c, h in zip(result.coin_in_usd, result.available_hours)
    ]
    return result


def traffic_rates(df, keys):
    """Traffic totals deduplicated across machines, banks and game titles."""
    result = (df.drop_duplicates(TRAFFIC_KEY).groupby(keys, observed=True, dropna=False)
              [["zone_entries", "coverage_hours"]].sum(min_count=1).reset_index())
    result["zone_entries_per_coverage_hour"] = result.zone_entries / result.coverage_hours.replace(0, np.nan)
    return result


def complete_months(df, start, end):
    """Select only full calendar months contained in the page's date window."""
    month = pd.to_datetime(df.month)
    return df[(month >= pd.Timestamp(start)) &
              (month + pd.offsets.MonthEnd(0) <= pd.Timestamp(end))].copy()


def assess(df, manager_ids, draws=2000, bank=None):
    """Screen bottom-ten picks using same-config, same-month, leave-one-out peers.

    A descriptive location signal needs >=80% matched exposure, >=3 months,
    negative upper 95% month-bootstrap bounds for local-vs-other demand AND
    traffic gaps, and subject demand >=90% of local peers. This is a heuristic
    association, not a causal attribution or a replacement recommendation.
    """
    monthly_keys = ["machine_id", "month", "zone_id", "bank_id", "config_id", "game"]
    monthly = rates(df, monthly_keys)
    traffic = traffic_rates(df, ["month", "zone_id"])
    monthly = monthly.merge(traffic[["month", "zone_id", "zone_entries_per_coverage_hour"]],
                            on=["month", "zone_id"], how="left", validate="many_to_one")
    zone_totals = monthly.groupby(["month", "config_id", "zone_id"], observed=True)
    zone_totals = zone_totals[["coin_in_cents", "available_seconds"]].sum()
    rng = np.random.default_rng(31)
    results = []
    for machine in manager_ids:
        subject = monthly[monthly.machine_id == machine]
        if bank is not None:
            subject = subject[subject.bank_id == bank]
        contributions = []
        for _, s in subject.iterrows():
            peers = zone_totals.loc[(s.month, s.config_id)].copy()
            # Exclude the subject from every peer zone, including moves and banks.
            own = monthly[(monthly.machine_id == machine) & (monthly.month == s.month)
                          & (monthly.config_id == s.config_id)]
            own = own.groupby("zone_id")[["coin_in_cents", "available_seconds"]].sum()
            peers = peers.subtract(own.reindex(peers.index, fill_value=0))
            local = peers.loc[s.zone_id]
            other = peers.drop(index=s.zone_id)
            if (s.available_seconds <= 0 or local.available_seconds <= 0 or local.coin_in_cents <= 0
                    or other.available_seconds.sum() <= 0 or other.coin_in_cents.sum() <= 0):
                continue
            local_rate = money.per_available_hour(money.cents_to_usd(local.coin_in_cents),
                                                  local.available_seconds / 3600)
            other_rate = money.per_available_hour(money.cents_to_usd(other.coin_in_cents.sum()),
                                                  other.available_seconds.sum() / 3600)
            other_traffic = traffic[(traffic.month == s.month) & traffic.zone_id.isin(other.index)]
            other_traffic = other_traffic.set_index("zone_id").reindex(other.index)
            if (other_traffic.zone_entries_per_coverage_hour.isna().any()
                    or pd.isna(s.zone_entries_per_coverage_hour)):
                continue
            peer_traffic = np.average(other_traffic.zone_entries_per_coverage_hour,
                                      weights=other.available_seconds)
            hours = s.available_hours
            contributions.append(dict(month=s.month, hours=hours, own=s.coin_in_usd,
                local=local_rate * hours, other=other_rate * hours,
                local_traffic=s.zone_entries_per_coverage_hour * hours,
                other_traffic=peer_traffic * hours))
        row = dict(machine_id=machine, matched_months=0, matched_hours_share=0.,
                   own_per_hour=np.nan, local_peer_per_hour=np.nan, other_zone_peer_per_hour=np.nan,
                   own_vs_local=np.nan, demand_gap=np.nan, demand_low=np.nan, demand_high=np.nan,
                   traffic_gap=np.nan, traffic_low=np.nan, traffic_high=np.nan, location_signal=False)
        if contributions:
            d = pd.DataFrame(contributions).groupby("month").sum()
            total = d.sum()
            row.update(matched_months=len(d), matched_hours_share=total.hours / subject.available_hours.sum(),
                       own_per_hour=money.per_available_hour(total.own, total.hours),
                       local_peer_per_hour=money.per_available_hour(total.local, total.hours),
                       other_zone_peer_per_hour=money.per_available_hour(total.other, total.hours),
                       own_vs_local=money.hold(total.own, total.local),
                       demand_gap=money.hold(total.local, total.other) - 1,
                       traffic_gap=money.hold(total.local_traffic, total.other_traffic) - 1)
            if len(d) >= 3:
                samples = rng.integers(0, len(d), size=(draws, len(d)))
                for prefix, numerator, denominator in [("demand", "local", "other"),
                                                        ("traffic", "local_traffic", "other_traffic")]:
                    num = d[numerator].to_numpy()[samples].sum(axis=1)
                    den = d[denominator].to_numpy()[samples].sum(axis=1)
                    low, high = np.quantile(num / den - 1, [.025, .975])
                    row.update({f"{prefix}_low": low, f"{prefix}_high": high})
                row["location_signal"] = bool(row["matched_hours_share"] >= .8
                    and row["demand_high"] < 0 and row["traffic_high"] < 0 and row["own_vs_local"] >= .9)
        results.append(row)
    return pd.DataFrame(results).set_index("machine_id")
