"""Every committed mart loads, is small, and the example mart has one row per gaming day."""
import pandas as pd

from royale import config, io


def test_marts_exist_and_are_small():
    files = sorted(config.MARTS_DIR.glob("*.parquet"))
    assert files, "no marts built; run: uv run python -m royale.build"
    for path in files:
        assert path.stat().st_size <= config.MART_MAX_BYTES, f"{path.name} over 5 MB; aggregate further"
        assert len(pd.read_parquet(path)) > 0, f"{path.name} is empty"


def test_property_day_mart():
    df = io.mart("property_day")
    assert len(df) == 181
    assert df["gaming_date"].is_unique
    assert (df["coin_in_usd"] - df["payout_usd"] - df["house_win_usd"]).abs().max() < 1e-6
