import math
from decimal import Decimal

import pandas as pd
import pytest

from royale import config, io, money

needs_data = pytest.mark.skipif(not config.data_available(), reason="DATA_DIR has no data")
S = pd.Series


# cents_to_usd
def test_cents_to_usd_scalar_and_series():
    assert money.cents_to_usd(12345) == 123.45
    assert money.cents_to_usd(S([100, 250])).tolist() == [1.0, 2.5]


# hold
def test_hold_ratio_of_sums():
    assert money.hold(S([10.0, 30.0]), S([100.0, 300.0])) == pytest.approx(0.1)


def test_hold_two_days_differs_from_mean_of_daily_holds():
    house_win = S([10.0, 1.0])     # day 1 hold 10%, day 2 hold 50%
    coin_in = S([100.0, 2.0])
    ratio_of_sums = money.hold(house_win, coin_in)
    mean_of_ratios = (house_win / coin_in).mean()
    assert ratio_of_sums == pytest.approx(11 / 102)
    assert mean_of_ratios == pytest.approx(0.30)
    assert abs(ratio_of_sums - mean_of_ratios) > 0.1


def test_hold_zero_coin_in_is_none():
    assert money.hold(S([5.0]), S([0.0])) is None
    assert money.hold(S([], dtype=float), S([], dtype=float)) is None


def test_hold_accepts_decimal():
    assert money.hold(S([Decimal("1.50")]), S([Decimal("15.00")])) == pytest.approx(0.1)


# theo
def test_theo_per_row_rtp():
    assert money.theo(S([1000.0, 2000.0]), S([0.90, 0.95])) == pytest.approx(100 + 100)


def test_theo_scalar_rtp_and_zero():
    assert money.theo(S([1000.0]), 0.92) == pytest.approx(80.0)
    assert money.theo(S([0.0]), 0.92) == 0.0


# luck_residual
def test_luck_residual_sign():
    assert money.luck_residual(S([50.0, 70.0]), S([60.0, 80.0])) == pytest.approx(-20.0)


# luck_z
def test_luck_z_formula():
    # residual 20, variance 100*2 + 300*1 = 500
    z = money.luck_z(S([60.0, 60.0]), S([50.0, 50.0]), S([100.0, 300.0]), S([2.0, 1.0]))
    assert z == pytest.approx(20 / math.sqrt(500))


def test_luck_z_scalar_variance_and_zero_variance():
    assert money.luck_z(S([10.0]), S([0.0]), S([25.0]), 4.0) == pytest.approx(1.0)
    assert money.luck_z(S([10.0]), S([0.0]), S([0.0]), 4.0) is None


# availability
def test_availability_ratio_of_sums_and_zero():
    assert money.availability(S([3600, 0]), S([3600, 3600])) == pytest.approx(0.5)
    assert money.availability(S([0]), S([0])) is None


# per_available_hour
def test_per_available_hour_and_zero():
    assert money.per_available_hour(S([100.0, 50.0]), S([10.0, 5.0])) == pytest.approx(10.0)
    assert money.per_available_hour(S([100.0]), S([0.0])) is None


# comp_reinvestment
def test_comp_reinvestment_and_zero():
    assert money.comp_reinvestment(S([20.0, 10.0]), S([100.0, 50.0])) == pytest.approx(0.2)
    assert money.comp_reinvestment(S([20.0]), S([0.0])) is None


# concentration_share
def test_concentration_share_top_fraction():
    values = S([1.0] * 99 + [101.0])          # top 1% (1 row) holds 101/200
    assert money.concentration_share(values, 0.01) == pytest.approx(101 / 200)
    assert money.concentration_share(values, 1.0) == pytest.approx(1.0)


def test_concentration_share_rounds_up_and_zero():
    assert money.concentration_share(S([4.0, 3.0, 2.0, 1.0]), 0.3) == pytest.approx(7 / 10)
    assert money.concentration_share(S([0.0, 0.0]), 0.5) is None
    assert money.concentration_share(S([], dtype=float), 0.5) is None
    with pytest.raises(ValueError):
        money.concentration_share(S([1.0]), 0)


# real data
@needs_data
def test_property_day_observed_hold_reproduced_jan_2025():
    df = io.sql("""
        SELECT gaming_date, house_win_usd, coin_in_usd, observed_hold
        FROM property_day
        WHERE gaming_date BETWEEN DATE '2025-01-01' AND DATE '2025-01-31'
        ORDER BY gaming_date
    """)
    assert len(df) == 31
    for _, r in df.iterrows():
        got = money.hold(S([r.house_win_usd]), S([r.coin_in_usd]))
        assert got == pytest.approx(r.observed_hold, abs=1e-9)
