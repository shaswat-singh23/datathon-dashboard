from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from royale import io
from royale.demand import event_comparison, traffic_summary


def test_missing_weekdays_and_zero_baseline_are_not_lifts():
    data = pd.DataFrame({
        'gaming_date': pd.date_range('2025-01-01', periods=6),
        'local_weekday': ['Mon', 'Mon', 'Tue', 'Wed', 'Wed', 'Thu'],
        'events_active': [None, 'Partial', 'Partial', None, 'Zero', 'Unmatched'],
        'coin_in_usd': [100, 110, 900, 0, 50, 40],
    })
    result = event_comparison(data)
    assert result.loc['Partial', 'actual'] == 1010
    assert result.loc['Partial', 'matched_days'] == 1
    assert result.loc['Partial', 'days'] == 2
    assert result.loc['Zero', 'matched_days'] == 1
    assert result.lift.isna().all()
    assert np.isnan(result.loc['Partial', 'expected'])
    assert result.loc['Zero', 'comparison'] == 'Zero weekday baseline'
    assert result.loc['Unmatched', 'comparison'] == 'Missing weekday baseline'


def test_matched_event_uses_ratio_of_sums_not_mean_of_day_lifts():
    data = pd.DataFrame({
        'gaming_date': pd.date_range('2025-01-01', periods=5),
        'local_weekday': ['Mon', 'Tue', 'Mon', 'Mon', 'Tue'],
        'events_active': [None, None, 'Event', 'Event', 'Event'],
        'coin_in_usd': [100, 1000, 200, 300, 900],
    })
    row = event_comparison(data).loc['Event']
    assert row.days == row.matched_days == 3
    assert row.expected == 1200
    assert row.lift == pytest.approx(1400 / 1200 - 1)
    assert row.lift != pytest.approx((2 + 3 + .9) / 3 - 1)
    assert event_comparison(data[data.events_active.isna()]).empty


@pytest.mark.parametrize('last_day,matched,days', [(7, 0, 1), (10, 3, 4), (31, 4, 4)])
def test_rendered_event_filter_has_complete_comparator(last_day, matched, days):
    app = AppTest.from_file(str(Path('app.py').resolve()), default_timeout=30).run()
    app.switch_page('pages/2_demand.py').run()
    app.slider[0].set_value((date(2025, 1, 1), date(2025, 1, last_day))).run()
    assert not app.exception and not app.error
    event_table = next(frame.value for frame in app.dataframe if 'matched_days' in frame.value)
    ces = event_table.loc[event_table.index.str.contains('CES')].iloc[0]
    assert ces.matched_days == matched
    assert ces.days == days
    assert np.isfinite(ces.lift) if matched == days else pd.isna(ces.lift)
    if matched == days:
        data = io.mart('q2_demand')
        data = data[pd.to_datetime(data.gaming_date).dt.month == 1]
        daily = data.groupby(['gaming_date', 'local_weekday'], as_index=False).agg(
            coin_in_usd=('coin_in_usd', 'sum'), events_active=('events_active', 'first'))
        baseline = daily[daily.events_active.isna()].groupby('local_weekday').coin_in_usd.mean()
        events = daily[daily.events_active.fillna('').str.contains('CES')]
        assert ces.lift == pytest.approx(events.coin_in_usd.sum() / events.local_weekday.map(baseline).sum() - 1)

    # Zone filtering also changes the event and baseline populations together.
    zone = next(widget for widget in app.selectbox if widget.label == 'Zone drill')
    zone.set_value('Z-B40').run()
    assert not app.exception and not app.error
    event_table = next(frame.value for frame in app.dataframe if 'matched_days' in frame.value)
    assert not np.isinf(event_table.lift).any()


def test_counter_rate_matches_count_exposure_pairs_and_retains_dst():
    data = pd.DataFrame({
        'zone_entries_observed': [240, 120, np.nan, 999],
        'zone_counter_coverage_hours': [24, 3, 5, 0],
        'scheduled_seconds': [24 * 3600, 23 * 3600, 24 * 3600, 24 * 3600],
    })
    summary = traffic_summary(data)
    assert summary['entries_per_covered_hour'] == pytest.approx(360 / 27)
    assert summary['entries_per_covered_hour'] != pytest.approx((10 + 40) / 2)
    assert summary['covered_sensor_hours'] == 27
    assert summary['scheduled_sensor_hours'] == 95
    assert summary['counter_coverage'] == pytest.approx(27 / 95)
    zero = traffic_summary(data.assign(zone_counter_coverage_hours=0))
    assert zero['entries_per_covered_hour'] is None
    assert zero['counter_coverage'] == 0
    assert traffic_summary(data.iloc[:0])['counter_coverage'] is None


@pytest.mark.parametrize('start,end,zone', [
    (date(2025, 1, 1), date(2025, 6, 30), 'All zones'),
    (date(2025, 3, 8), date(2025, 3, 8), 'All zones'),
    (date(2025, 1, 1), date(2025, 1, 31), 'Z-B40'),
])
def test_rendered_counter_metrics_match_selected_mart_exposure(start, end, zone):
    app = AppTest.from_file(str(Path('app.py').resolve()), default_timeout=30).run()
    app.switch_page('pages/2_demand.py').run()
    app.slider[0].set_value((start, end)).run()
    next(s for s in app.selectbox if s.label == 'Zone drill').set_value(zone).run()
    assert not app.exception and not app.error
    data = io.mart('q2_demand')
    selected = data[pd.to_datetime(data.gaming_date).dt.date.between(start, end)]
    if zone != 'All zones':
        selected = selected[selected.zone_id == zone]
    hours = selected.zone_counter_coverage_hours.sum()
    expected_rate = selected.zone_entries_observed.sum() / hours
    expected_coverage = hours / (selected.scheduled_seconds.sum() / 3600)
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics['Entries / covered sensor-hour'] == f'{expected_rate:,.1f}'
    assert metrics['Counter coverage'] == f'{expected_coverage:.1%}'
    monthly = next(frame.value for frame in app.dataframe if 'counter_coverage' in frame.value)
    for month, rows in selected.groupby('month'):
        assert monthly.loc[month, 'entries_per_covered_hour'] == pytest.approx(
            rows.zone_entries_observed.sum() / rows.zone_counter_coverage_hours.sum())


def test_machine_tables_publish_units_without_changing_rank_values():
    import json
    from royale.marts.q1_machines import summarize

    app = AppTest.from_file(str(Path('app.py').resolve()), default_timeout=30).run()
    app.switch_page('pages/1_machines.py').run()
    assert not app.exception and not app.error
    ranked = app.dataframe[2]
    pd.testing.assert_frame_equal(ranked.value, summarize(io.mart('q1_machines')))
    columns = json.loads(ranked.proto.columns)
    assert columns['house_win']['label'] == 'Total house win ($)'
    assert columns['house_win']['type_config']['format'] == '$%.0f'
    assert '$/h' in columns['adjusted_per_hour']['label']
    assert columns['adjusted_per_hour']['type_config']['format'] == '$%.2f'
    assert columns['availability']['type_config']['format'] == 'percent'
    assert columns['observed_hold']['type_config']['format'] == 'percent'
    assert columns['luck_z']['label'] == 'House-win luck z'
