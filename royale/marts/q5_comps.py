"""Monthly comp aggregates; property totals stay separate from tracked guest groups.

No raw-table join: UNION ALL preserves both populations without fan-out.
source_rows records input counts so build verification can reconcile aggregation.
"""
import duckdb
import pandas as pd

NAME = "q5_comps"


def build(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.sql("""
        SELECT 'tracked' AS population, period_month AS month,
               opening_tier, home_region, count(*) AS source_rows,
               sum(comp_cost_usd)::DOUBLE AS comp_cost_usd,
               sum(comp_face_value_usd)::DOUBLE AS comp_face_value_usd,
               sum(theo_usd)::DOUBLE AS theo_usd,
               sum(points_earned)::DOUBLE AS points_earned,
               sum(points_redeemed)::DOUBLE AS points_redeemed
        FROM player_period
        GROUP BY period_month, opening_tier, home_region
        UNION ALL
        SELECT 'property', strftime(gaming_date, '%Y-%m'),
               NULL, NULL, count(*),
               sum(comp_cost_usd)::DOUBLE, sum(comp_face_value_usd)::DOUBLE,
               sum(theo_usd)::DOUBLE, NULL, NULL
        FROM property_day
        GROUP BY strftime(gaming_date, '%Y-%m')
        ORDER BY month, population, opening_tier, home_region
    """).df()
