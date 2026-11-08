"""Decision visuals reconcile with the tables and analytical outputs they present."""
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from royale import budget, io, visuals
from royale.marts.q1_machines import summarize
from royale.marts.q6_actions import assess, proposed_plan
from royale.model import KINDS, LABELS, score_forecasts


def open_page(page):
    app = AppTest.from_file(str(Path('app.py').resolve()), default_timeout=60).run()
    app.switch_page(f'pages/{page}').run()
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]
    return app


# ---- Machines -------------------------------------------------------------------------------

@pytest.mark.parametrize('months', [None, (6,)])
def test_slope_points_equal_summarize_ranks(months):
    data = io.mart('q1_machines')
    if months:
        data = data[pd.to_datetime(data.gaming_date).dt.month.isin(months)]
    ranked = summarize(data)
    table = visuals.slope_table(ranked)
    expected = ranked.sort_values('raw_rank').head(10)
    assert table.index.tolist() == expected.index.tolist()
    fig = visuals.slope_chart(table)
    machines = [t for t in fig.data if t.meta != 'boundary']
    assert [t.name for t in machines] == table.index.tolist()
    for trace in machines:
        assert list(trace.y) == [expected.loc[trace.name, 'raw_rank'], expected.loc[trace.name, 'adjusted_rank']]


def test_full_period_emphasis_is_m1158_and_m1118():
    table = visuals.slope_table(summarize(io.mart('q1_machines')))
    assert set(table.index[table.leaves_bottom_ten]) == {'M-1158', 'M-1118'}


def test_machines_page_table_holds_slope_ranks():
    app = open_page('1_machines.py')
    manager = app.dataframe[0].value
    fig_table = visuals.slope_table(summarize(io.mart('q1_machines')))
    pd.testing.assert_series_equal(manager.raw_rank, fig_table.raw_rank, check_names=False)
    pd.testing.assert_series_equal(manager.adjusted_rank, fig_table.adjusted_rank, check_names=False)
    assert any('not an estimated replacement uplift' in c.value for c in app.caption)


# ---- Demand ---------------------------------------------------------------------------------

def test_closure_rates_are_ratios_of_sums_with_units():
    demand = io.mart('q2_demand')
    window = visuals.closure_window(demand)
    assert window == (pd.Timestamp('2025-03-03'), pd.Timestamp('2025-04-06'))
    table, reason = visuals.closure_comparison(demand, window)
    assert reason is None
    assert table.phase.tolist() == [p for p in visuals.PHASES for _ in range(2)]
    dates = pd.to_datetime(demand.gaming_date)
    during = demand[dates.between(*window) & demand.zone_id.eq('Z-B40')]
    row = table[(table.phase == 'During closure') & (table.area == 'Back Forty')].iloc[0]
    assert row.days == 35
    assert row.coin_in_per_available_hour == pytest.approx(during.coin_in_usd.sum() / during.available_hours.sum())
    assert table.coin_in_usd.sum() == pytest.approx(demand.coin_in_usd.sum())
    bars = visuals.closure_chart(table)
    for trace in bars.data:
        part = table[table.area == trace.name]
        np.testing.assert_allclose(list(trace.y), part.coin_in_per_available_hour.astype(float))
    assert '$/h' in bars.layout.yaxis.title.text


@pytest.mark.parametrize('start,end,phrase', [
    ('2025-05-01', '2025-06-30', 'no days inside the closure'),
    ('2025-03-10', '2025-03-20', 'entirely inside the closure'),
])
def test_unsupported_windows_explain_instead_of_substituting(start, end, phrase):
    demand = io.mart('q2_demand')
    dates = pd.to_datetime(demand.gaming_date)
    view = demand[dates.between(start, end)]
    table, reason = visuals.closure_comparison(view, visuals.closure_window(demand))
    assert phrase in reason
    assert table.coin_in_usd.sum() == pytest.approx(view.coin_in_usd.sum())


def test_demand_page_shows_honest_message_for_post_closure_window():
    app = open_page('2_demand.py')
    app.slider[0].set_value((date(2025, 5, 1), date(2025, 6, 30))).run()
    assert not app.exception
    assert any('no days inside the closure' in w.value for w in app.warning)


# ---- Actions --------------------------------------------------------------------------------

@pytest.fixture(scope='module')
def actions():
    data = io.mart('q6_actions')
    catalog = data[data.record_type == 'catalog'].copy()
    options, evidence = assess(data)
    return data, catalog, options, evidence


def test_cost_bars_equal_budget_outputs(actions):
    data, catalog, options, evidence = actions
    manager = evidence['machines'].sort_values('raw_rank').head(10).index.tolist()
    costs = visuals.cost_comparison(options, catalog, manager)
    by_id = options.set_index('action_type_id')
    for row in costs.itertuples():
        if row.action_type_id in by_id.index:
            line = budget.ActionLine(row.action_type_id, int(by_id.loc[row.action_type_id, 'quantity']))
        else:
            line = budget.ActionLine(row.action_type_id, 10, manager)
        assert row.cost_usd == pytest.approx(budget.line_cost_usd(catalog, line))
    fig = visuals.cost_chart(costs)
    plotted = {y: x for trace in fig.data for y, x in zip(trace.y, trace.x)}
    assert plotted == dict(zip(costs.option, costs.cost_usd))
    assert plotted['Inspect'] == pytest.approx(budget.plan_cost_usd(catalog, proposed_plan(data)))


def test_scenarios_reconcile_and_zero_recovery_keeps_spend_and_downtime(actions):
    _, _, options, _ = actions
    scenarios = visuals.recovery_scenarios(options)
    assert set(scenarios.action_type_id) == {'A-PREVENTIVE', 'A-TECH-SHIFT'}
    assert 'A-INSPECT' not in set(scenarios.action_type_id)
    assert sorted(scenarios.assumed_recovery.unique()) == [0, .25, .5, 1]
    for action, part in scenarios.groupby('action_type_id'):
        option = options.set_index('action_type_id').loc[action]
        by_level = part.set_index('assumed_recovery')
        assert by_level.loc[.5, 'incremental_theo_usd'] == pytest.approx(option.base_theo_usd)
        assert by_level.loc[.25, 'incremental_theo_usd'] == pytest.approx(option.half_theo_usd)
        assert by_level.loc[1, 'incremental_theo_usd'] == pytest.approx(option.high_theo_usd)
        assert by_level.loc[0, 'incremental_theo_usd'] == pytest.approx(option.low_theo_usd)
        zero = by_level.loc[0]
        assert zero.spend_usd == option.cost_usd > 0
        assert zero.incremental_theo_usd == pytest.approx(-option.implementation_theo_usd)
        assert zero.theo_less_spend_usd == pytest.approx(-option.cost_usd - option.implementation_theo_usd)
    assert scenarios.loc[scenarios.action_type_id == 'A-PREVENTIVE', 'implementation_theo_usd'].gt(0).all()


def test_cards_cover_four_decisions_without_inspection_revenue(actions):
    data, catalog, options, evidence = actions
    cards = {c['action_type_id']: c for c in visuals.action_cards(options, catalog, evidence, proposed_plan(data))}
    assert list(cards) == list(visuals.CARD_ACTIONS)
    assert cards['A-INSPECT']['decision'] == 'Fund'
    assert 'No revenue' in cards['A-INSPECT']['benefit']
    assert cards['A-HOLD']['spend_usd'] == 0
    assert cards['A-HOLD']['decision'] == f"Preserve ${100_000 - cards['A-INSPECT']['spend_usd']:,.0f}"
    for card in cards.values():
        assert card['spend_usd'] == options.set_index('action_type_id').loc[card['action_type_id'], 'cost_usd']


def test_actions_page_renders_scenarios_for_short_window():
    app = open_page('6_actions.py')
    scenarios = next(f.value for f in app.dataframe if 'assumed_recovery' in f.value)
    assert set(scenarios.option) == {'Maintenance', 'Technician coverage'}
    app.slider[0].set_value((date(2025, 6, 1), date(2025, 6, 30))).run()
    assert not app.exception and not app.error
    short = next(f.value for f in app.dataframe if 'assumed_recovery' in f.value)
    zero = short[short.assumed_recovery == 0]
    assert (zero.spend_usd > 0).all()


# ---- Model ----------------------------------------------------------------------------------

def test_mae_chart_equals_score_forecasts_in_any_order():
    data = io.mart('q7_forecast')
    scores = score_forecasts(data)
    table = visuals.mae_table(scores, LABELS)
    fig = visuals.mae_chart(table)
    np.testing.assert_allclose(fig.data[0].x, scores.to_numpy())
    assert list(fig.data[0].y) == [LABELS[k] for k in KINDS]
    assert table.set_index('kind').mae_usd.idxmin() == 'weekday'
    shuffled = score_forecasts(data.sample(frac=1, random_state=3))
    pd.testing.assert_series_equal(scores, shuffled)


def test_display_order_and_filters_never_refit(monkeypatch):
    def no_fit(*args, **kwargs):
        raise AssertionError('Presentation must use frozen predictions, never fit')

    monkeypatch.setattr('royale.model.fit', no_fit)
    monkeypatch.setattr('royale.model.Forecast.predict', no_fit)
    data = io.mart('q7_forecast')
    data['gaming_date'] = pd.to_datetime(data.gaming_date)
    may = data[data.gaming_date.dt.month == 5]
    forward = visuals.forecast_chart(may, list(KINDS), LABELS)
    backward = visuals.forecast_chart(may, list(reversed(KINDS)), LABELS)
    by_name = {t.name: list(t.y) for t in backward.data}
    for trace in forward.data:
        assert list(trace.y) == by_name[trace.name]
    for kind in KINDS:
        assert by_name[LABELS[kind]] == may[f'{kind}_prediction_usd'].tolist()

    app = open_page('7_model.py')
    lead = app.get('plotly_chart')[0]
    app.slider[0].set_value((date(2025, 6, 1), date(2025, 6, 14))).run()
    next(m for m in app.multiselect if m.label == 'Forecasts to compare').set_value(['weekday_trend', 'constant']).run()
    assert not app.exception and not app.error
    # The lead MAE chart reports the frozen full holdout, unchanged by filters or display order.
    assert app.get('plotly_chart')[0].proto.spec == lead.proto.spec
    assert 'weekday-mean baseline' in app.markdown[0].value or any(
        'weekday-mean baseline' in m.value for m in app.markdown)
