"""Run tonight: uv run python scripts/verify_env.py   Every line should say PASS."""

import importlib
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

results: list[tuple[str, bool, str]] = []


def check(name, fn):
    try:
        results.append((name, True, str(fn() or "")))
    except Exception as e:  # noqa: BLE001
        results.append((name, False, f"{type(e).__name__}: {e}"))


for mod in ["pandas", "polars", "duckdb", "pyarrow", "numpy", "sklearn", "lightgbm",
            "statsmodels", "plotly", "matplotlib", "streamlit", "openpyxl"]:
    check(f"import {mod}", lambda m=mod: getattr(importlib.import_module(m), "__version__", "ok"))


def duck():
    import duckdb
    return duckdb.sql("select 42 as x").fetchall()[0][0]


def sk():
    import numpy as np
    from sklearn.ensemble import HistGradientBoostingRegressor
    X = np.random.rand(200, 4)
    HistGradientBoostingRegressor(max_iter=10).fit(X, X[:, 0])
    return "fit ok"


def lgb():
    import lightgbm
    import numpy as np
    X = np.random.rand(200, 4)
    lightgbm.LGBMRegressor(n_estimators=10, verbose=-1).fit(X, X[:, 0])
    return "fit ok"


def src_io():
    from src import io
    return f"{len(io.tables())} tables visible"


def git_identity():
    name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, check=False).stdout.strip()
    email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, check=False).stdout.strip()
    if not (name and email):
        raise RuntimeError('set it: git config --global user.name "You" && git config --global user.email you@x.com')
    return name


check("duckdb query", duck)
check("sklearn fit", sk)
check("lightgbm fit", lgb)
check("src.io", src_io)
check("git identity", git_identity)

print(f"Python {platform.python_version()} on {platform.system()} {platform.machine()}\n")
for name, ok, msg in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name:22} {msg}")

failed = [n for n, ok, _ in results if not ok]
if failed:
    if any("lightgbm" in n for n in failed) and platform.system() == "Darwin":
        print("\nlightgbm on macOS needs OpenMP: brew install libomp, then rerun.")
    print(f"\n{len(failed)} check(s) failed.")
    sys.exit(1)
print("\nAll good.")
