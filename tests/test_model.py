import numpy as np
import pandas as pd
import pytest

from royale.model import FITTED_KIND, KINDS, LABELS, TEST_START, TRAIN_END, fit, predict, score_forecasts
from royale.marts.q7_forecast import build


@pytest.fixture
def daily():
    dates = pd.date_range('2025-01-01', '2025-06-30')
    # Exact known weekday + linear trend, so extrapolation is checkable.
    return pd.DataFrame({'gaming_date': dates,
                         'coin_in_usd': 1000 + dates.day_of_week * 100 + np.arange(len(dates)) * 2.0})


@pytest.mark.parametrize('kind', KINDS)
@pytest.mark.parametrize('poison', [np.nan, np.inf, -1e15, 'unobserved'])
def test_holdout_never_influences_training(daily, kind, poison):
    train = daily[daily.gaming_date <= TRAIN_END]
    test = daily[daily.gaming_date >= TEST_START]
    expected = fit(train, kind)
    poisoned = daily.astype({'coin_in_usd': object})
    poisoned.loc[poisoned.gaming_date >= TEST_START, 'coin_in_usd'] = poison
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
    regression = fit(daily, FITTED_KIND)
    np.testing.assert_allclose(regression.coefficients, [1000, 1100, 1200, 1300, 1400, 1500, 1600, 60], atol=1e-9)
    np.testing.assert_allclose(predict(regression, test), test.coin_in_usd, atol=1e-9)


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


def test_scores_use_only_selected_days():
    forecasts = pd.DataFrame({
        'gaming_date': pd.date_range('2025-05-31', periods=3),
        'coin_in_usd': [100, 100, 100],
        'constant_prediction_usd': [102, 108, 114],
        'weekday_prediction_usd': [99, 97, 95],
        'weekday_trend_prediction_usd': [100, 102, 104],
    }, index=[10, 20, 30])
    np.testing.assert_allclose(score_forecasts(forecasts), [8, 3, 2])
    # May has one day; June has two. Score days, rather than averaging month means.
    np.testing.assert_allclose(score_forecasts(forecasts.iloc[1:]), [11, 4, 3])
    np.testing.assert_allclose(score_forecasts(forecasts.iloc[:1]), [2, 1, 0])


def test_page_rescores_period_and_drills_without_refitting(monkeypatch):
    from datetime import date
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    from royale import io

    def no_fit(*args, **kwargs):
        raise AssertionError('The page must read frozen predictions, never fit a model')

    monkeypatch.setattr('royale.model.fit', no_fit)
    data = io.mart('q7_forecast')
    app = AppTest.from_file(str(Path('pages/7_model.py').resolve()), default_timeout=30).run()
    assert not app.exception
    initial = app.dataframe[0].value.copy()
    assert initial.Model.tolist() == [LABELS[kind] for kind in KINDS]
    full_column = 'Full holdout MAE (USD/day)'
    selected_column = 'Selected period MAE (USD/day)'
    np.testing.assert_allclose(initial[full_column], initial[selected_column])
    for position, kind in enumerate(KINDS):
        expected = (data[f'{kind}_prediction_usd'] - data.coin_in_usd).abs().mean()
        assert initial.iloc[position][full_column] == pytest.approx(expected)

    def check_view(start, end, drill):
        view = data[pd.to_datetime(data.gaming_date).dt.date.between(start, end)]
        scores = app.dataframe[0].value
        np.testing.assert_array_equal(scores[full_column], initial[full_column])
        for position, kind in enumerate(KINDS):
            error = (view[f'{kind}_prediction_usd'] - view.coin_in_usd).abs()
            assert scores.iloc[position][selected_column] == pytest.approx(error.mean())
        breakdown = app.dataframe[1].value
        assert breakdown.Days.sum() == len(view)
        for kind in KINDS:
            weighted = np.average(breakdown[LABELS[kind]], weights=breakdown.Days)
            assert weighted == pytest.approx(scores.loc[scores.Model == LABELS[kind], selected_column].iloc[0])
        assert drill in breakdown
        for _, row in breakdown.iterrows():
            dates = pd.to_datetime(view.gaming_date)
            labels = dates.dt.strftime('%Y-%m') if drill == 'Month' else dates.dt.day_name()
            group = view[labels == row[drill]]
            assert row.Days == len(group)
            for kind in KINDS:
                expected = (group[f'{kind}_prediction_usd'] - group.coin_in_usd).abs().mean()
                assert row[LABELS[kind]] == pytest.approx(expected)
        return breakdown

    # Unequal month sizes expose a mistaken unweighted average of month MAEs.
    start, end = date(2025, 5, 24), date(2025, 6, 5)
    app.slider[0].set_value((start, end)).run()
    assert not app.exception
    months = check_view(start, end, 'Month')
    assert months.Month.tolist() == ['2025-05', '2025-06']
    assert months.Days.tolist() == [8, 5]

    app.radio[0].set_value('Weekday').run()
    assert not app.exception
    weekdays = check_view(start, end, 'Weekday')
    assert weekdays.Weekday.tolist() == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    app.multiselect[0].set_value([]).run()
    assert not app.exception
    check_view(start, end, 'Weekday')
    app.slider[0].set_value((end, end)).run()
    assert not app.exception
    single = check_view(end, end, 'Weekday')
    assert single.Weekday.tolist() == ['Thursday']
