import numpy as np
import pandas as pd
import pytest

from royale.model import KINDS, TEST_START, TRAIN_END, fit, predict
from royale.marts.q7_forecast import build


@pytest.fixture
def daily():
    dates = pd.date_range('2025-01-01', '2025-06-30')
    # Exact known weekday + linear trend, so extrapolation is checkable.
    return pd.DataFrame({'gaming_date': dates,
                         'coin_in_usd': 1000 + dates.day_of_week * 100 + np.arange(len(dates)) * 2.0})


@pytest.mark.parametrize('kind', KINDS)
def test_holdout_never_influences_training(daily, kind):
    train = daily[daily.gaming_date <= TRAIN_END]
    test = daily[daily.gaming_date >= TEST_START]
    expected = fit(train, kind)
    poisoned = daily.copy()
    poisoned.loc[poisoned.gaming_date >= TEST_START, 'coin_in_usd'] = np.nan
    actual = fit(poisoned, kind)
    assert actual == expected
    assert actual.training_rows == 120
    assert actual.training_end == TRAIN_END
    np.testing.assert_array_equal(predict(actual, test), predict(expected, test))
    # Changing or removing holdout target columns also cannot affect prediction.
    np.testing.assert_array_equal(predict(actual, test[['gaming_date']]), predict(actual, test.assign(coin_in_usd=1e15)))


def test_known_forecasts(daily):
    train = daily[daily.gaming_date <= TRAIN_END]
    test = daily[daily.gaming_date >= TEST_START]
    np.testing.assert_allclose(predict(fit(daily, 'constant'), test), train.coin_in_usd.mean())
    means = train.groupby(train.gaming_date.dt.day_of_week).coin_in_usd.mean()
    np.testing.assert_allclose(predict(fit(daily, 'weekday'), test), means.loc[test.gaming_date.dt.day_of_week])
    np.testing.assert_allclose(predict(fit(daily, 'weekday_trend'), test), test.coin_in_usd, atol=1e-9)


def test_training_errors(daily):
    with pytest.raises(ValueError, match='Unknown'):
        fit(daily, 'unknown')
    with pytest.raises(ValueError, match='No rows'):
        fit(daily[daily.gaming_date >= TEST_START])
    with pytest.raises(ValueError, match='Duplicate'):
        fit(pd.concat([daily, daily.iloc[:1]]))
    with pytest.raises(ValueError, match='seven weekdays'):
        fit(daily.iloc[:2])
    daily.loc[0, 'coin_in_usd'] = -1
    with pytest.raises(ValueError, match='finite and nonnegative'):
        fit(daily)


def test_builder_holdout_and_scoring(daily):
    import duckdb
    con = duckdb.connect()
    con.register('property_day', daily)
    result = build(con)
    assert len(result) == 61
    assert pd.to_datetime(result.gaming_date).min() == TEST_START
    np.testing.assert_allclose(result.weekday_trend_prediction_usd, result.coin_in_usd, atol=1e-9)
    con.unregister('property_day')
    con.register('property_day', daily.iloc[1:])
    with pytest.raises(ValueError, match='exactly one'):
        build(con)


def test_nonnegative_forecast(daily):
    daily['coin_in_usd'] = 1000 - np.arange(len(daily)) * 5.0
    future = pd.DataFrame({'gaming_date': ['2026-01-01']})
    assert predict(fit(daily, 'weekday_trend'), future)[0] == 0
