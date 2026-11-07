"""Daily sufficient statistics for period-specific machine comparison and triage."""
import pandas as pd
from royale import money

NAME = 'q1_machines'
SQL = """
SELECT m.machine_id, m.gaming_date, p.location_id, f.zone_id,
       z.name AS zone_name, f.bank_id, g.theme AS game, m.config_id,
       c.scheduled_seconds, m.available_seconds, m.coin_in_cents,
       m.house_win_cents, m.sum_bet_squared, g.configured_rtp,
       g.payout_multiplier_variance,
       d.lease_cost_usd + d.service_cost_usd + d.power_cost_usd
         + d.repair_cost_usd AS supplied_cost_usd
FROM machine_day m
JOIN calendar_day c USING (gaming_date)
JOIN placements p ON p.machine_id = m.machine_id
 AND c.gaming_day_start_utc >= p.effective_from_utc
 AND (p.effective_to_utc IS NULL OR c.gaming_day_start_utc < p.effective_to_utc)
JOIN game_math g ON g.config_id = m.config_id
JOIN floor_locations f ON f.location_id = p.location_id
JOIN floor_locations z ON z.location_id = f.zone_id
JOIN prepared_daily_view d ON d.machine_id = m.machine_id AND d.gaming_date = m.gaming_date
WHERE m.active AND m.location_id IS NOT NULL
"""


def build(con):
    expected = con.sql('SELECT count(*) FROM machine_day WHERE active AND location_id IS NOT NULL').fetchall()[0][0]
    df = con.sql(SQL).df()
    assert len(df) == expected, f'join changed row count: {expected} -> {len(df)}'
    assert not df.duplicated(['machine_id', 'gaming_date']).any()
    mismatches = con.sql("""SELECT count(*) FROM machine_day m JOIN calendar_day c USING(gaming_date)
      JOIN placements p ON p.machine_id=m.machine_id
      AND c.gaming_day_start_utc >= p.effective_from_utc
      AND (p.effective_to_utc IS NULL OR c.gaming_day_start_utc < p.effective_to_utc)
      WHERE m.location_id IS NOT NULL AND m.location_id <> p.location_id""").fetchall()[0][0]
    assert mismatches == 0, 'placement disagrees with machine-day location'
    df['configured_rtp'] = df.configured_rtp.astype(float)
    df['payout_multiplier_variance'] = df.payout_multiplier_variance.astype(float)
    df['theo_cents'] = [money.theo(c, r) for c, r in zip(df.coin_in_cents, df.configured_rtp)]
    df['variance_cents2'] = df.sum_bet_squared * df.payout_multiplier_variance
    return df.sort_values(['gaming_date', 'machine_id']).reset_index(drop=True)


def summarize(df):
    """Recompute all rates and ranks within the selected period and drill."""
    rows = []
    for machine, d in df.groupby('machine_id', sort=True):
        hours = d.available_seconds.sum() / 3600
        win = money.cents_to_usd(d.house_win_cents.sum())
        theo = money.cents_to_usd(d.theo_cents.sum())
        costs = d.supplied_cost_usd.sum()
        rows.append(dict(machine_id=machine, active_days=len(d), available_hours=hours,
            availability=money.availability(d.available_seconds, d.scheduled_seconds),
            coin_in=money.cents_to_usd(d.coin_in_cents.sum()), house_win=win, theo=theo,
            luck_residual=money.luck_residual(win, theo),
            luck_z=money.luck_z(d.house_win_cents, d.theo_cents, d.sum_bet_squared, d.payout_multiplier_variance),
            observed_hold=money.hold(d.house_win_cents, d.coin_in_cents),
            configured_hold=money.hold(d.theo_cents, d.coin_in_cents),
            contribution_per_hour=money.per_available_hour(win-costs, hours),
            adjusted_per_hour=money.per_available_hour(theo-costs, hours),
            zone=', '.join(sorted(d.zone_name.unique())), game=', '.join(sorted(d.game.unique())),
            supplied_cost=costs))
    result = pd.DataFrame(rows).set_index('machine_id')
    result['raw_rank'] = result.house_win.rank(method='first').astype(int)
    result['adjusted_rank'] = result.adjusted_per_hour.rank(method='first', na_option='bottom').astype(int)
    # Zone benchmarks exclude the subject machine, weighted by its hours in each zone.
    floor_rate = money.per_available_hour(money.cents_to_usd(df.theo_cents.sum())-df.supplied_cost_usd.sum(), df.available_seconds.sum()/3600)
    for machine, d in df.groupby('machine_id'):
        benchmark, weight = 0., 0.
        for zone, segment in d.groupby('zone_id'):
            peers = df[(df.zone_id == zone) & (df.machine_id != machine)]
            rate = money.per_available_hour(money.cents_to_usd(peers.theo_cents.sum())-peers.supplied_cost_usd.sum(), peers.available_seconds.sum()/3600)
            if rate is not None:
                h = segment.available_seconds.sum()/3600
                benchmark += rate*h
                weight += h
        rate = benchmark/weight if weight else float('nan')
        result.loc[machine, 'zone_peer_per_hour'] = rate
        r = result.loc[machine]
        if pd.notna(r.luck_z) and r.luck_z < -3.8:
            label, rule = 'leak-candidate', 'z < -3.8; inspect payout/configuration, no wrongdoing inferred'
        elif rate < floor_rate and r.adjusted_per_hour >= rate:
            label, rule = 'location', 'below-floor zone peers; machine meets zone peer rate'
        elif (pd.notna(r.luck_z) and r.luck_z < -1.96) or r.adjusted_rank > 10:
            label, rule = 'luck', 'z < -1.96 or leaves bottom 10 after luck/exposure adjustment'
        else:
            label, rule = 'weak', 'remains bottom 10; no preceding luck/location signal'
        result.loc[machine, 'triage'] = label
        result.loc[machine, 'rule'] = rule
    return result.sort_values('adjusted_rank')
