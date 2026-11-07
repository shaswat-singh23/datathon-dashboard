# Organizer data integrity and semantics verified
- Issue: #33 | Author: sahith1021 | Time: 2026-11-07 13:30 CST
- Claim: The configured data copy passes the organizer's integrity and semantic checks for dataset `0.9.0-draft`.
- Evidence: Both unmodified organizer scripts exited 0: 62 file checksums/sizes, 31 table row-count/CSV–Parquet comparisons, and all 11 semantic checks passed. Prepared-view counts are below.
- So what: The dashboard's source copy matches the supplied manifest and satisfies the supplied accounting, date, key, rollup, and lag invariants.
- Checked by: Kyle (Claude Code, Fable 5.1), 2026-11-07 16:25

## Provenance and reproduction

- `DATA_DIR`: `/home/sahith/dashboard-royale/data` (loaded through `royale.config`).
- Organizer checkout: `5f9274bdc3efa6614e6c081becaeadda34c57a32`.
- `data/manifest.json`: version `0.9.0-draft`, world `gilded-ace-v1`, build seed `20250102`.
- Reference baseline: the organizer manifest's expected hashes, sizes and row counts, plus the semantic script's expected invariants. This is a verification result, not a model-performance claim.
- `uv` was unavailable; the existing project `.venv/bin/python` ran both scripts with DuckDB. No organizer files were modified.

Run from the dashboard repository root:

```sh
.venv/bin/python /home/sahith/dashboard-royale/scripts/verify_data.py
.venv/bin/python /home/sahith/dashboard-royale/scripts/verify_semantics.py
```

Both scripts resolve their data path relative to their own organizer checkout; that path was confirmed to equal the configured `DATA_DIR`.

### Integrity output (exit 0)

```text
PASS: 62 checksums and sizes; 31 row counts and format comparisons
```

### Semantic output (exit 0)

```text
PASS: unique machine-day keys
PASS: date window
PASS: off-floor rows
PASS: active floor range
PASS: machine integer accounting
PASS: prepared accounting
PASS: player accounting
PASS: property accounting
PASS: daily rollups
PASS: prior-seven-day feature
PASS: daylight saving
```

## Prepared-view row counts

| Prepared view | Observed rows | Manifest rows |
| --- | ---: | ---: |
| `prepared_daily_view` | 56,110 | 56,110 |
| `property_day` | 181 | 181 |
| `player_period` | 148,893 | 148,893 |

Reproduce the observed counts and manifest comparison:

```python
import json
import duckdb
from royale.config import DATA_DIR

manifest = json.loads((DATA_DIR / "manifest.json").read_text())
con = duckdb.connect()
for entry in manifest["files"]:
    if entry["path"].startswith("1_prepared_views/") and entry["path"].endswith(".parquet"):
        observed = con.read_parquet(str(DATA_DIR / entry["path"])).count("*").fetchall()[0][0]
        assert observed == entry["rows"]
        print(entry["path"], observed, entry["rows"])
```

## Limits

These checks establish consistency with this draft release, not real-world accuracy, causal explanations, or correctness of downstream dashboard analysis. Independent human review remains pending. `AGENTS.md` is unchanged; the verification result is reported on issue #33 instead.
