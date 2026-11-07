"""Q3 downtime mart: play lost to faults, repairs, moves and installs.

One table, two record types (column `record_type`):

- `machine_day`: one row per on-floor machine-day (off-floor rows with null location_id
  are excluded). Lost hours = calendar_day.scheduled_seconds - machine_day.available_seconds
  (calendar scheduled hours, so 2025-03-08 counts 23 h). Lost coin-in = lost hours x that
  machine's coin-in per available hour in the same calendar month (ratio of sums).
  Assumption: an hour lost to downtime would have drawn the same coin-in as the machine's
  average available hour that month. Lost theo (expected house win) uses the same method.
- `ticket`: one row per operations ticket with response times. Repair response =
  available_at - opened_at; split into wait (opened -> work started) and fix (work
  started -> available). Shift is from the local hour the ticket opened, matching
  shift_roster: day 06-14, swing 14-22, grave 22-06.

Location (zone, bank) comes from machine_day.location_id for machine-days and from
operations.location_id for tickets, so moved machines are attributed to where they were.
"""
import duckdb
import pandas as pd

NAME = "q3_downtime"

MACHINE_DAY_SQL = """
WITH md AS (
    SELECT m.machine_id, m.gaming_date, m.location_id,
           c.scheduled_seconds / 3600.0                       AS scheduled_h,
           m.available_seconds / 3600.0                       AS available_h,
           (c.scheduled_seconds - m.available_seconds) / 3600.0 AS lost_h,
           m.coin_in_cents / 100.0                            AS coin_in_usd,
           m.theo_cents::DOUBLE / 100.0                       AS theo_usd,
           date_trunc('month', m.gaming_date)::DATE           AS month
    FROM machine_day m
    JOIN calendar_day c USING (gaming_date)
    WHERE m.location_id IS NOT NULL
),
rate AS (  -- coin-in per available hour, same machine, same month (ratio of sums)
    SELECT machine_id, month,
           sum(coin_in_usd) / nullif(sum(available_h), 0) AS coin_in_per_avail_h,
           sum(theo_usd) / nullif(sum(available_h), 0)    AS theo_per_avail_h
    FROM md GROUP BY 1, 2
)
SELECT 'machine_day' AS record_type, md.gaming_date, md.month, md.machine_id,
       mc.manufacturer, f.zone_id, z.name AS zone_name, f.bank_id, md.location_id,
       md.scheduled_h, md.available_h, md.lost_h, md.coin_in_usd, md.theo_usd,
       r.coin_in_per_avail_h, r.theo_per_avail_h,
       md.lost_h * r.coin_in_per_avail_h AS lost_coin_in_usd,
       md.lost_h * r.theo_per_avail_h    AS lost_theo_usd
FROM md
JOIN rate r USING (machine_id, month)
JOIN machines mc USING (machine_id)
JOIN floor_locations f USING (location_id)
LEFT JOIN floor_locations z ON z.location_id = f.zone_id
"""

TICKET_SQL = """
SELECT 'ticket' AS record_type, c.gaming_date,
       date_trunc('month', c.gaming_date)::DATE AS month, o.machine_id,
       mc.manufacturer, f.zone_id, z.name AS zone_name, f.bank_id, o.location_id,
       o.operation_id, o.event_type, o.opened_at_local,
       hour(o.opened_at_local) AS opened_hour_local,
       CASE WHEN hour(o.opened_at_local) BETWEEN 6 AND 13 THEN 'day'
            WHEN hour(o.opened_at_local) BETWEEN 14 AND 21 THEN 'swing'
            ELSE 'grave' END AS shift,
       epoch(o.work_started_at_utc - o.opened_at_utc) / 3600.0 AS wait_h,
       epoch(o.available_at_utc - o.work_started_at_utc) / 3600.0 AS fix_h,
       epoch(o.available_at_utc - o.opened_at_utc) / 3600.0 AS response_h,
       o.direct_cost_cents / 100.0 AS direct_cost_usd
FROM operations o
JOIN calendar_day c
  ON o.opened_at_utc >= c.gaming_day_start_utc AND o.opened_at_utc < c.gaming_day_end_utc
JOIN machines mc USING (machine_id)
LEFT JOIN floor_locations f ON f.location_id = o.location_id
LEFT JOIN floor_locations z ON z.location_id = f.zone_id
"""


def build(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    n_on_floor = con.sql("SELECT count(*) FROM machine_day WHERE location_id IS NOT NULL").fetchall()[0][0]
    n_ops = con.sql("SELECT count(*) FROM operations").fetchall()[0][0]
    md = con.sql(MACHINE_DAY_SQL).df()
    tk = con.sql(TICKET_SQL).df()
    # Row counts must survive the joins (AGENTS.md rule 4).
    assert len(md) == n_on_floor, f"machine_day rows {len(md)} != on-floor rows {n_on_floor}"
    assert len(tk) == n_ops, f"ticket rows {len(tk)} != operations rows {n_ops}"
    df = pd.concat([md, tk], ignore_index=True)
    return df.sort_values(["record_type", "gaming_date", "machine_id"]).reset_index(drop=True)
