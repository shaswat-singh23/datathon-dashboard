"""Data access helpers.

    from src import io
    io.tables()                         # {name: path} for every data file found
    io.sql("select * from sales limit 5")   # polars DataFrame
    df = io.load("sales")               # whole table by name, or pass a path (xlsx works too)
    io.save(df, "sales_clean")          # data/processed/sales_clean.parquet, queryable right away

Every csv/tsv/parquet/json file under data/ and app/data/ becomes a duckdb view
named after the file (lowercase, non-word chars -> _). On a name clash the
parent folder is prefixed, e.g. processed_sales.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd
import polars as pl

from src.paths import APP_DATA, DATA, PROCESSED

READERS = {
    ".csv": "read_csv_auto",
    ".tsv": "read_csv_auto",
    ".parquet": "read_parquet",
    ".json": "read_json_auto",
    ".jsonl": "read_json_auto",
    ".ndjson": "read_json_auto",
}


def _clean(s: str) -> str:
    name = re.sub(r"\W+", "_", s).strip("_").lower()
    return name if name and not name[0].isdigit() else f"t_{name}"


def tables() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for root in (DATA, APP_DATA):
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in READERS:
                continue
            name = _clean(p.stem)
            if name in found:
                name = f"{_clean(p.parent.name)}_{name}"
            found[name] = p
    return found


@lru_cache(maxsize=1)
def con() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect()
    for name, p in tables().items():
        reader = READERS[p.suffix.lower()]
        path = p.as_posix().replace("'", "''")
        c.execute(f"create or replace view \"{name}\" as select * from {reader}('{path}')")
    return c


def refresh() -> None:
    """Call after adding files so new tables show up."""
    con.cache_clear()


def sql(query: str) -> pl.DataFrame:
    return con().sql(query).pl()


def load(name_or_path: str | Path) -> pl.DataFrame:
    p = Path(name_or_path)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pl.from_pandas(pd.read_excel(p))
    if p.suffix:
        return sql(f"select * from {READERS[p.suffix.lower()]}('{p.as_posix()}')")
    return sql(f'select * from "{name_or_path}"')


def save(df: pl.DataFrame | pd.DataFrame, name: str) -> Path:
    out = PROCESSED / f"{_clean(name)}.parquet"
    if isinstance(df, pd.DataFrame):
        df.to_parquet(out, index=False)
    else:
        df.write_parquet(out)
    refresh()
    return out
