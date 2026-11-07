"""Retrospective public context, one row per gaming date.

Weather is matched by date label, not reallocated to 06:00 gaming-day bounds.
Tourism is monthly context repeated per day, never an as-of forecast input.
"""
import duckdb
import pandas as pd

NAME = "q2_context"


def build(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    # Reject duplicate keys before joining: silent fan-out would inflate coin-in.
    for table, key in (("property_day", "gaming_date"),
                       ("weather_daily", "source_date"),
                       ("city_visitation_monthly", "month")):
        if con.sql(f"SELECT count(*) != count(DISTINCT {key}) FROM {table}").fetchall()[0][0]:
            raise ValueError(f"{table}: missing or duplicate {key}")
    result = con.sql("""
        SELECT p.gaming_date, strftime(p.gaming_date, '%Y-%m') AS month,
               p.local_weekday, p.coin_in_usd::DOUBLE AS coin_in_usd,
               w.source_date AS weather_calendar_date, w.station_id,
               CASE WHEN nullif(trim(w.tmax_qflag), '') IS NULL THEN w.tmax_c::DOUBLE END AS tmax_c,
               CASE WHEN nullif(trim(w.prcp_qflag), '') IS NULL THEN w.prcp_mm::DOUBLE END AS prcp_mm,
               w.prcp_mflag, w.tmax_qflag, w.prcp_qflag,
               v.visitor_volume::DOUBLE / v.days_in_month AS visitors_per_calendar_day,
               v.source_revision AS tourism_revision,
               w.source_url AS weather_source_url, v.source_url AS tourism_source_url
        FROM property_day p
        LEFT JOIN weather_daily w ON w.source_date = p.gaming_date
        LEFT JOIN city_visitation_monthly v ON v.month = strftime(p.gaming_date, '%Y-%m')
        ORDER BY p.gaming_date
    """).df()
    assert len(result) == con.sql("SELECT count(*) FROM property_day").fetchall()[0][0]
    return result
