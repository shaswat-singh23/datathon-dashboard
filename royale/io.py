"""Read raw tables (from DATA_DIR) and marts (from marts/).

    from royale import io
    pd_day = io.table("property_day")                     # pandas DataFrame
    top = io.sql("SELECT * FROM machine_day LIMIT 5")     # every table name is a view
    m = io.mart("property_day")                           # committed derived table

Pages read only marts, so the deployed app works without DATA_DIR.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd

from royale import config


@lru_cache(maxsize=1)
def connect() -> duckdb.DuckDBPyConnection:
    """One in-memory DuckDB connection with a view per raw table that exists on disk."""
    con = duckdb.connect()
    for name, rel in config.TABLES.items():
        path = config.DATA_DIR / rel
        if path.is_file():
            con.sql(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet('{path.as_posix()}')")
    return con


def sql(query: str) -> pd.DataFrame:
    """Run SQL against the raw tables. Table names from the data dictionary work as-is."""
    return connect().sql(query).df()


def table(name: str) -> pd.DataFrame:
    """Load one raw table. Use sql() for anything large; prefer parquet column pruning."""
    path = config.table_path(name)
    if not path.is_file():
        raise FileNotFoundError(f"{name} not found at {path}. Set DATA_DIR in .env (see SETUP.md).")
    return pd.read_parquet(path)


def mart_path(name: str) -> Path:
    return config.MARTS_DIR / f"{name}.parquet"


def mart(name: str) -> pd.DataFrame:
    """Load a committed mart by name (file stem under marts/)."""
    path = mart_path(name)
    if not path.is_file():
        raise FileNotFoundError(f"marts/{name}.parquet is missing. Run: uv run python -m royale.build")
    return pd.read_parquet(path)
