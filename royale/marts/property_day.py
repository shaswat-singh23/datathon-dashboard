"""Floor-level daily mart: property_day plus the calendar's scheduled seconds.

Example mart. Pages that need a whole-floor trend read io.mart("property_day").
"""
import duckdb
import pandas as pd

NAME = "property_day"


def build(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.sql(
        """
        SELECT p.*, c.scheduled_seconds, c.month, c.is_weekend, c.federal_holiday,
               p.available_machine_hours / (p.active_machines * c.scheduled_seconds / 3600.0)
                   AS availability_ratio
        FROM property_day p
        JOIN calendar_day c USING (gaming_date)
        ORDER BY gaming_date
        """
    ).df()
