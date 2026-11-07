"""Fair event comparisons within the currently selected period and zone."""
import pandas as pd

from royale import money


def traffic_summary(zone_days: pd.DataFrame) -> dict:
    """Pool crossings over matched covered zone-hours, never machine-hours.

    Each input row is one zone-day. Unusable count/coverage pairs contribute no
    rate exposure; scheduled coverage still includes every selected zone-day.
    No missed crossings are imputed. Scheduled hours retain DST day lengths.
    """
    hours = zone_days.zone_counter_coverage_hours
    entries = zone_days.zone_entries_observed
    usable = entries.notna() & hours.notna() & hours.gt(0)
    covered = hours[usable].sum()
    scheduled = zone_days.scheduled_seconds.sum() / 3600
    return dict(covered_sensor_hours=covered, scheduled_sensor_hours=scheduled,
                entries_per_covered_hour=money.per_available_hour(entries[usable], hours[usable]),
                counter_coverage=money.availability(covered, scheduled))


def event_comparison(daily: pd.DataFrame) -> pd.DataFrame:
    """Suppress lift unless every event day has a non-event weekday comparator.

    Actuals always describe all selected event days. Partial expected totals must
    never be compared with those full actuals. This is descriptive, not causal.
    """
    baseline = daily[daily.events_active.isna()].groupby('local_weekday').coin_in_usd.mean()
    events = daily[daily.events_active.notna()].copy()
    events['expected'] = events.local_weekday.map(baseline)
    result = events.groupby('events_active').agg(
        days=('gaming_date', 'size'), matched_days=('expected', 'count'),
        first_day=('gaming_date', 'min'), coin_in_per_day=('coin_in_usd', 'mean'),
        actual=('coin_in_usd', 'sum'), expected=('expected', 'sum'))
    complete = result.matched_days.eq(result.days)
    result.loc[~complete, 'expected'] = float('nan')
    result['lift'] = [
        money.hold(actual, expected) - 1 if matched and expected > 0 else float('nan')
        for actual, expected, matched in zip(result.actual, result.expected, complete)
    ]
    result['comparison'] = [
        'Missing weekday baseline' if not matched else
        'Zero weekday baseline' if expected <= 0 else 'Matched (descriptive)'
        for matched, expected in zip(complete, result.expected)
    ]
    return result.sort_values('first_day')
