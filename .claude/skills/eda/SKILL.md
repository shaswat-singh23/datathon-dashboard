---
name: eda
description: Profile one or more datasets and write EDA.md. Use when new data arrives or the user asks to explore, profile, or understand a dataset.
argument-hint: "[path or folder under data/raw, default all of data/raw]"
---

Profile $ARGUMENTS. If empty, profile everything in data/raw/.

Work in a script at `scripts/eda.py` (run with `uv run python scripts/eda.py`) using duckdb or polars. `src.io.sql()` already exposes every file in data/ as a table named after the file.

For each table:
1. Shape, columns, dtypes. 5 sample rows.
2. Nulls per column (count and %). Constant or near-constant columns.
3. Cardinality per column. For anything that looks like an id or key, check uniqueness and report duplicates.
4. Numeric columns: min, p1, median, p99, max. Flag impossible values (negative quantities, future dates, sentinels like -1 or 999).
5. Date columns: range, granularity, gaps. Say whether this is a time series.
6. Categorical columns: top values, rare levels, inconsistent spelling or casing.

Across tables:
7. Likely join keys and the match rate for each (what % of keys in A exist in B, and the reverse).

If a target is known or obvious:
8. Its distribution and class balance, plus columns that look like leakage (derived from the target, recorded after the outcome, or suspiciously predictive).

Write EDA.md with one section per table and the commands used. Save plots to `figures/eda_*.png`. Keep EDA.md under 200 lines.

End EDA.md with:
- 5 questions this data can plausibly answer, ranked by how much the challenge's judges would care
- Data quality issues that will bite us, each with a proposed fix

Do not modify data/raw.
