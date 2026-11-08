"""R45 passes on committed marts and fails on an out-of-window mart."""
import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rubric", ROOT / "tools/rubric.py")
rubric = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rubric)


def test_committed_marts_pass():
    assert rubric.window_check(ROOT)["status"] == "pass"


def test_out_of_window_mart_fails(tmp_path):
    pd.DataFrame({"gaming_date": pd.to_datetime(["2025-06-30", "2025-07-01"])}).to_parquet(tmp_path / "x.parquet")
    result = rubric.window_check(ROOT, tmp_path)
    assert result["status"] == "fail" and "x.parquet.gaming_date" in result["details"][0]
