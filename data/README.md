# data/

Everything here except this file is gitignored.

- `raw/`: original files exactly as downloaded. Never modified. Get them from the team Drive folder: <link>
- `processed/`: parquet produced by code in `src/`. Safe to delete and rebuild.

The deployed app can't see this folder. Put small files the app needs in `app/data/`, which is committed. Check the challenge rules allow it first.
