from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from royale import io
from royale.model import KINDS
from royale.planning import choose_days, evaluate_planning


@pytest.fixture
def forecasts():
    dates = pd.date_range('2025-05-05', periods=21)
    return pd.DataFrame({
        'gaming_date': dates,
        'coin_in_usd': np.tile([10, 20, 30, 40, 50, 60, 70], 3),
        'constant_prediction_usd': 40.,
        'weekday_prediction_usd': np.tile([10, 20, 30, 40, 50, 60, 70], 3),
        'weekday_trend_prediction_usd': np.tile([70, 60, 50, 40, 30, 20, 10], 3),
    })


def test_equal_slots_and_independently_known_demand_coverage(forecasts):
    summary, schedule = evaluate_planning(forecasts, 2)
    rows = summary.set_index('kind')
    assert rows.review_days.eq(6).all()
    assert rows.weeks.eq(3).all()
    assert rows.observed_days.eq(21).all()
    assert rows.uniform_expected_coin_in_usd.eq(240).all()
    assert rows.loc['weekday', 'demand_share'] == pytest.approx(130 / 280)
    assert rows.loc['constant', 'demand_share'] == pytest.approx(30 / 280)
    assert rows.loc['weekday_trend', 'demand_share'] == pytest.approx(30 / 280)
    assert rows.loc['weekday', 'gain_pp'] == pytest.approx(100 * (130 / 280 - 2 / 7))
    for _, policy in schedule.groupby('kind'):
        assert policy.groupby('week').priority_day.sum().eq(2).all()
    pd.testing.assert_frame_equal(summary, evaluate_planning(forecasts, 2)[0])


@pytest.mark.parametrize('kind', KINDS)
def test_day_choices_do_not_consume_actuals_and_ignore_row_order(forecasts, kind):
    expected = choose_days(forecasts, kind)
    for poison in [np.nan, np.inf, -1e15, 'unobserved']:
        changed = forecasts.assign(coin_in_usd=poison).sample(frac=1, random_state=86)
        pd.testing.assert_frame_equal(choose_days(changed, kind), expected)
    pd.testing.assert_frame_equal(choose_days(forecasts.drop(columns='coin_in_usd'), kind), expected)


def test_boundary_weeks_missing_dates_and_no_eligible_weeks(forecasts):
    view = forecasts.iloc[1:-1]
    summary, _ = evaluate_planning(view)
    assert summary.weeks.eq(1).all()
    assert summary.review_days.eq(2).all()
    assert summary.gain_low_pp.isna().all()
    assert summary.gain_high_pp.isna().all()
    missing = forecasts.drop(index=9)
    assert choose_days(missing, 'weekday').week.nunique() == 2
    summary, schedule = evaluate_planning(forecasts.iloc[:6])
    assert summary.empty and schedule.empty
    zero, _ = evaluate_planning(forecasts.assign(coin_in_usd=0))
    assert zero.demand_share.isna().all() and zero.gain_pp.isna().all()


def test_week_bootstrap_is_ratio_of_summed_week_totals(forecasts):
    forecasts.loc[14:, 'coin_in_usd'] *= 20
    forecasts.loc[19:, 'coin_in_usd'] = 1
    summary, schedule = evaluate_planning(forecasts)
    policy = schedule[schedule.kind == 'weekday']
    expected = policy.loc[policy.priority_day, 'coin_in_usd'].sum() / policy.coin_in_usd.sum()
    row = summary.set_index('kind').loc['weekday']
    assert row.demand_share == pytest.approx(expected)
    weekly = policy.assign(covered=policy.coin_in_usd.where(policy.priority_day, 0)).groupby('week')[['covered', 'coin_in_usd']].sum()
    assert row.demand_share != pytest.approx((weekly.covered / weekly.coin_in_usd).mean())
    assert row.gain_low_pp <= row.gain_pp <= row.gain_high_pp


@pytest.mark.parametrize('slots', [0, 8, 1.5, True])
def test_invalid_resource_budgets(forecasts, slots):
    with pytest.raises(ValueError, match='slots'):
        choose_days(forecasts, 'weekday', slots)


def test_page_policy_rescores_and_drills_without_raw_data(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Planning must use committed forecasts without raw reads or refitting')
    monkeypatch.setattr(io, 'table', forbidden)
    monkeypatch.setattr(io, 'sql', forbidden)
    monkeypatch.setattr('royale.model.fit', forbidden)
    app = AppTest.from_file(str(Path('app.py').resolve()), default_timeout=30).run()
    app.switch_page('pages/7_model.py').run()
    assert not app.exception and not app.error
    table = next(d.value for d in app.dataframe if 'gain_pp' in d.value)
    assert table.weeks.eq(8).all()
    assert table.review_days.eq(16).all()
    slots = next(widget for widget in app.selectbox if widget.label == 'Review days per complete week')
    slots.set_value(3).run()
    table = next(d.value for d in app.dataframe if 'gain_pp' in d.value)
    assert table.review_days.eq(24).all()
    drill = next(widget for widget in app.selectbox if widget.label == 'Planning forecast drill')
    drill.set_value('constant').run()
    actual = next(d.value for d in app.dataframe if 'priority_day' in d.value)
    assert set(pd.to_datetime(actual.loc[actual.priority_day, 'gaming_date']).dt.day_of_week) == {0, 1, 2}
    app.slider[0].set_value((date(2025, 5, 6), date(2025, 5, 25))).run()
    assert not app.exception
    table = next(d.value for d in app.dataframe if 'gain_pp' in d.value)
    assert table.weeks.eq(2).all() and table.review_days.eq(6).all()
    app.slider[0].set_value((date(2025, 5, 6), date(2025, 5, 6))).run()
    assert not app.exception
    assert any('complete Monday' in message.value for message in app.info)
