"""Q2 demand mart: one row per zone x gaming date (7 zones x 181 days).

Sums of coin-in, occupied and available machine-hours over active (on-floor) machine rows
from prepared_daily_view, plus the zone's counter entries for that day, the events active,
and any walkway closure touching the zone. Pages aggregate these rows with ratios of sums.

Notes on the inputs:
- Off-floor rows (location_id null) are excluded; they are not zero performance.
- zone_entries_observed repeats the zone's daily counter total on every machine row in that
  zone, so it is taken once per zone-day (any_value), never summed across machines.
  Entries are sensor crossings, not unique people; coverage hours say how much was observed.
- A walkway closure is mapped to gaming dates by overlapping the closure interval (UTC)
  with calendar_day's gaming-day interval (06:00 to 06:00 local, stored in UTC).
"""
import duckdb
import pandas as pd

NAME = "q2_demand"


def build(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.sql(
        """
        WITH zone_day AS (
            SELECT zone_id, any_value(zone_name) AS zone_name, gaming_date,
                   count(*)                              AS active_machines,
                   sum(coin_in_usd)::DOUBLE              AS coin_in_usd,
                   sum(occupied_hours)                   AS occupied_hours,
                   sum(available_hours)                  AS available_hours,
                   sum(paid_spins)                       AS paid_spins,
                   any_value(zone_entries_observed)      AS zone_entries_observed,
                   any_value(zone_counter_coverage_hours) AS zone_counter_coverage_hours
            FROM prepared_daily_view
            WHERE location_id IS NOT NULL
            GROUP BY zone_id, gaming_date
        ),
        closure_day AS (
            SELECT c.gaming_date, w.walkway_id, w.zone_a, w.zone_b, w.closure_reason
            FROM floor_walkways w
            JOIN calendar_day c
              ON w.closed_from_utc < c.gaming_day_end_utc
             AND w.closed_to_utc   > c.gaming_day_start_utc
        ),
        floor_closures AS (
            SELECT gaming_date,
                   string_agg(walkway_id || ' ' || zone_a || '-' || zone_b || ' (' || closure_reason || ')', '; ')
                       AS closures_active
            FROM closure_day GROUP BY gaming_date
        ),
        zone_closures AS (
            SELECT gaming_date, zone_id, string_agg(walkway_id, '; ') AS zone_walkway_closed
            FROM (SELECT gaming_date, zone_a AS zone_id, walkway_id FROM closure_day
                  UNION ALL
                  SELECT gaming_date, zone_b AS zone_id, walkway_id FROM closure_day)
            GROUP BY gaming_date, zone_id
        )
        SELECT z.gaming_date, c.month, c.local_weekday, c.is_weekend, c.federal_holiday,
               c.scheduled_seconds, p.events_active, fc.closures_active,
               z.zone_id, z.zone_name, zc.zone_walkway_closed,
               z.active_machines,
               z.active_machines * c.scheduled_seconds / 3600.0 AS scheduled_machine_hours,
               z.available_hours, z.occupied_hours, z.coin_in_usd, z.paid_spins,
               z.zone_entries_observed, z.zone_counter_coverage_hours
        FROM zone_day z
        JOIN calendar_day c USING (gaming_date)
        JOIN property_day p USING (gaming_date)
        LEFT JOIN floor_closures fc USING (gaming_date)
        LEFT JOIN zone_closures zc ON zc.gaming_date = z.gaming_date AND zc.zone_id = z.zone_id
        ORDER BY z.gaming_date, z.zone_id
        """
    ).df()
