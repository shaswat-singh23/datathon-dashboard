# Team conventions

Read by Claude Code, Cursor, Codex, and Copilot. Using ChatGPT or another chat tool? Paste this file in at the start.

## Team (fill in before the event)
- Claude driver: Shaswat. Pipeline, app, parallel Claude sessions.
- Data owner: ___. Question framing, domain context, audits joins and numbers.
- Analyst: ___. Modeling and validation.
- Storyteller: ___. README, slides, video. Starts by hour 4.

## Stack
- Python 3.12, managed by uv. Add deps with `uv add <pkg>`. Never `pip install`.
- Run everything with `uv run ...` from the repo root.
- Tables: polars or pandas. Big joins and aggregations: duckdb SQL. `src.io.sql("select ...")` queries every file in data/ by name.
- Models: scikit-learn first (HistGradientBoosting). lightgbm only if it adds something.
- Charts: plotly in the app, matplotlib for quick figures.
- App: Streamlit, `app/app.py`.

## Layout
```
data/raw/        original files. NEVER modify. gitignored.
data/processed/  derived parquet, rebuilt by code in src/. gitignored.
src/             shared importable code. Paths live in src/paths.py.
src/models/      model scripts, runnable with `uv run python -m src.models.<name>`.
scripts/         one-off runnable scripts.
notebooks/       personal scratch. gitignored. Move anything that matters into src/.
figures/         saved charts for slides and README.
app/             Streamlit dashboard. app/data/ is committed (small files only) so the deployed app has data.
FINDINGS.md      every insight, number, and decision. Single source of truth.
```

## Rules
1. Never edit or overwrite anything in data/raw.
2. Every join: print row counts before and after and check key uniqueness. State the expected cardinality (1:1, 1:many) and confirm it.
3. Every model reports its CV score next to a naive baseline (mean, majority class, or last value). No baseline, no claim.
4. Split by time if the data has time, by group if rows share an entity (store, user, patient). Random splits on those leak.
5. Fit preprocessing inside CV with a Pipeline. Never fit scalers or encoders on the full dataset.
6. A number goes in FINDINGS.md, with the script that produced it, before it goes in slides or the README.
7. Shared code is `.py`, not notebooks.
8. main always runs. `uv run streamlit run app/app.py` works before every merge.
9. Small commits with clear messages. Pull before you push.
10. If a result looks too good, assume leakage until proven otherwise.

## Git
- One branch per person: `<name>/<topic>`. Merge to main every 2 to 3 hours.
- Never commit data/raw, secrets, `.env`, or files over 50 MB.

## FINDINGS.md entry format
```
### <title> (<name>, <time>)
- Claim:
- Evidence: <number> from <script or query>
- So what: <why a judge should care>
```
