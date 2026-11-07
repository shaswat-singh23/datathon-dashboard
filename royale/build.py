"""Build every mart from DATA_DIR into marts/. Usage: uv run python -m royale.build [NAME ...]"""
from __future__ import annotations

import sys

from royale import config, io, marts


def main(only: list[str] | None = None) -> int:
    if not config.data_available():
        print(f"No data at DATA_DIR={config.DATA_DIR}. Set DATA_DIR in .env (see SETUP.md).")
        return 1
    config.MARTS_DIR.mkdir(exist_ok=True)
    con = io.connect()
    for mod in marts.modules():
        if only and mod.NAME not in only:
            continue
        df = mod.build(con)
        out = io.mart_path(mod.NAME)
        df.to_parquet(out, index=False)
        size = out.stat().st_size
        flag = "" if size <= config.MART_MAX_BYTES else "  TOO BIG: aggregate further"
        print(f"{mod.NAME}: {len(df):,} rows x {len(df.columns)} cols, {size / 1e6:.2f} MB{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or None))
