"""Paths and the table registry. Everything reads data through DATA_DIR."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

DATA_DIR = Path(os.environ.get("DATA_DIR", REPO_ROOT / "data")).expanduser()
MARTS_DIR = REPO_ROOT / "marts"
MART_MAX_BYTES = 5 * 1024 * 1024  # marts are committed; keep each under 5 MB

# Gaming window and the recommendation horizon (from GUIDE.md).
WINDOW_START = "2025-01-01"
WINDOW_END = "2025-06-30"
HORIZON_START = "2025-07-01"
HORIZON_DAYS = 30
BUDGET_USD = 100_000

# table name -> path relative to DATA_DIR (parquet). Same names as the data dictionary.
TABLES: dict[str, str] = {
    # 1_prepared_views
    "prepared_daily_view": "1_prepared_views/prepared_daily_view.parquet",
    "property_day": "1_prepared_views/property_day.parquet",
    "player_period": "1_prepared_views/player_period.parquet",
    # 2_machine_decision
    "machines": "2_machine_decision/machines.parquet",
    "game_math": "2_machine_decision/game_math.parquet",
    "placements": "2_machine_decision/placements.parquet",
    "floor_locations": "2_machine_decision/floor_locations.parquet",
    "floor_walkways": "2_machine_decision/floor_walkways.parquet",
    "machine_day": "2_machine_decision/machine_day.parquet",
    "operations": "2_machine_decision/operations.parquet",
    "cost_rules": "2_machine_decision/cost_rules.parquet",
    "action_catalog": "2_machine_decision/action_catalog.parquet",
    "calendar_day": "2_machine_decision/calendar_day.parquet",
    # 3_guests
    "players": "3_guests/players.parquet",
    "sessions": "3_guests/sessions.parquet",
    "trips": "3_guests/trips.parquet",
    "loyalty_ledger": "3_guests/loyalty_ledger.parquet",
    "fnb_transactions": "3_guests/fnb_transactions.parquet",
    # 4_context
    "zone_traffic_hourly": "4_context/zone_traffic_hourly.parquet",
    "events": "4_context/events.parquet",
    "weather_daily": "4_context/real_sources/weather_daily.parquet",
    "city_visitation_monthly": "4_context/real_sources/city_visitation_monthly.parquet",
    "visitor_profile_summary": "4_context/real_sources/visitor_profile_summary.parquet",
    "visitor_profile_segments": "4_context/real_sources/visitor_profile_segments.parquet",
    "benchmark_public": "4_context/real_sources/benchmark_public.parquet",
    "benchmark_property_monthly": "4_context/real_sources/benchmark_property_monthly.parquet",
    "benchmark_state_monthly": "4_context/real_sources/benchmark_state_monthly.parquet",
    # 5_optional
    "machine_hour": "5_optional/machine_hour.parquet",
    "shift_roster": "5_optional/shift_roster.parquet",
    "security_incidents": "5_optional/security_incidents.parquet",
    "visitor_profile_monthly": "5_optional/visitor_profile_monthly.parquet",
}


def table_path(name: str) -> Path:
    """Absolute path of a raw table. Raises KeyError for unknown names."""
    return DATA_DIR / TABLES[name]


def data_available() -> bool:
    """True when DATA_DIR holds the prepared views (needed for marts, not for the app)."""
    return table_path("property_day").is_file()
