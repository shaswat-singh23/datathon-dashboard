"""Q1 machine rankings from the committed daily mart."""
import pandas as pd
import plotly.express as px
import streamlit as st
from royale import io
from royale.marts import q1_location as location
from royale.marts.q1_machines import summarize

st.set_page_config(page_title='Machines: The Gilded Ace', page_icon='♠', layout='wide')
st.title('Which bottom-10 machines deserve a second look?')
st.caption('Compare the manager’s raw house-win ranking with expected contribution per available hour.')
try:
    data = io.mart('q1_machines')
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()
data['gaming_date'] = pd.to_datetime(data.gaming_date)
start, end = st.slider('Analysis period', min_value=data.gaming_date.min().date(),
    max_value=data.gaming_date.max().date(),
    value=(data.gaming_date.min().date(), data.gaming_date.max().date()))
bank = st.selectbox('Bank drill', ['All banks'] + sorted(data.bank_id.dropna().unique().tolist()))
selected = data[data.gaming_date.dt.date.between(start, end)]
if bank != 'All banks':
    selected = selected[selected.bank_id == bank]
if selected.empty:
    st.warning('No on-floor machine-days in this selection.')
    st.stop()
ranked = summarize(selected)
raw = ranked.sort_values('raw_rank').head(10)
adjusted = ranked.head(10)
overlap = len(set(raw.index) & set(adjusted.index))
st.metric('Manager picks surviving adjustment', f'{overlap} / {len(raw)}')
st.caption('Ranks and peer benchmarks recalculate within the selected period and bank. '
           'A machine with zero available hours has no adjusted rate and sorts last.')
left, right = st.columns(2)
with left:
    st.subheader('Manager: lowest total house win')
    st.dataframe(raw[['house_win', 'adjusted_rank', 'triage', 'luck_z', 'rule']], width='stretch')
with right:
    st.subheader('Adjusted: lowest expected contribution/hour')
    st.dataframe(adjusted[['adjusted_per_hour', 'raw_rank', 'zone', 'game']], width='stretch')
st.subheader('All machines — click a column to sort')
st.dataframe(ranked, width='stretch')
st.info('Classifications are inspection priorities, not causal findings. “Luck” also covers machines '
        'rescued by exposure adjustment. A location flag compares against other machines in the same zone; '
        'game mix and demand can confound it. A weak flag supports further investigation, not automatic replacement.')

st.subheader('Location: the same game in different places')
try:
    locations = location.complete_months(io.mart('q1_location'), start, end)
except FileNotFoundError as exc:
    st.warning(str(exc))
    locations = pd.DataFrame()
if locations.empty:
    st.info('The location comparison needs a complete calendar month inside the analysis period. '
            'Widen the date filter to include one; uncertainty needs at least three matched months.')
else:
    months = sorted(pd.to_datetime(locations.month).dt.strftime('%Y-%m').unique())
    st.caption(f'Location window: {months[0]} through {months[-1]}, complete months only. '
               'The bank drill selects candidates and the highlighted bank; comparison peers span the floor. '
               'Rates use total coin-in / total available hours.')
    candidates = locations if bank == 'All banks' else locations[locations.bank_id == bank]
    if candidates.empty:
        st.info('This bank has no machine exposure in the complete months selected.')
    else:
        manager_ids = (candidates.groupby('machine_id').house_win_cents.sum()
                       .sort_index().sort_values(kind='stable').head(10).index)
        screen = location.assess(locations, manager_ids, bank=None if bank == 'All banks' else bank)
        st.metric('Manager picks with a location association',
                  f'{int(screen.location_signal.sum())} / {len(screen)}')
        st.caption('Screen: at least 80% matched exposure and three months; local same-title peers '
                   'have lower demand and traffic than other-zone peers (upper 95% month-bootstrap '
                   'bounds below zero); the machine reaches at least 90% of local peer demand. '
                   'A missing interval means insufficient matched months. This screen is descriptive; '
                   'the data establish no causal count of machines explained by location.')
        stricter = (screen.location_signal & (screen.own_vs_local >= .95)).sum()
        st.caption(f'Threshold sensitivity: requiring 95% of local peer demand gives {stricter} candidates. '
                   'Location associations can coexist with the luck or payout-inspection flags above.')
        st.dataframe(screen, width='stretch', column_config={
            'location_signal': st.column_config.CheckboxColumn('Location association'),
            'demand_gap': st.column_config.NumberColumn('Local vs other demand gap', format='percent'),
            'demand_low': st.column_config.NumberColumn('Demand gap 95% low', format='percent'),
            'demand_high': st.column_config.NumberColumn('Demand gap 95% high', format='percent'),
            'traffic_gap': st.column_config.NumberColumn('Local vs other traffic gap', format='percent'),
            'traffic_low': st.column_config.NumberColumn('Traffic gap 95% low', format='percent'),
            'traffic_high': st.column_config.NumberColumn('Traffic gap 95% high', format='percent'),
            'matched_hours_share': st.column_config.NumberColumn('Exposure matched', format='percent'),
            'own_vs_local': st.column_config.NumberColumn('Machine / local peer demand', format='percent'),
        })
    game = st.selectbox('Location game drill', sorted(locations.game.unique()))
    game_data = locations[locations.game == game]
    zone_rates = location.rates(game_data, ['month', 'zone_id', 'zone_name'])
    zone_rates['month_label'] = pd.to_datetime(zone_rates.month).dt.strftime('%Y-%m')
    st.plotly_chart(px.line(zone_rates, x='month_label', y='coin_in_per_available_hour',
                           color='zone_name', markers=True,
                           labels={'month_label': 'Month', 'coin_in_per_available_hour': 'Coin-in / available hour ($)',
                                   'zone_name': 'Zone'}), width='stretch')
    st.caption('Each line is the selected title in one zone; compare within a month to hold title '
               'and calendar month fixed. Empty combinations have no matched evidence.')
    bank_rates = location.rates(game_data, ['zone_name', 'bank_id'])
    if bank != 'All banks':
        bank_rates = bank_rates[bank_rates.bank_id == bank]
    st.dataframe(bank_rates[['zone_name', 'bank_id', 'coin_in_usd', 'available_hours',
                             'coin_in_per_available_hour']], width='stretch')
    st.markdown('**Traffic and the walkway closure**')
    zone_traffic = location.traffic_rates(locations, ['month', 'zone_id'])
    st.dataframe(zone_traffic, width='stretch')
    closure_rates = location.rates(game_data, ['zone_id', 'zone_name', 'closure_endpoint', 'phase'])
    closure_traffic = location.traffic_rates(locations, ['zone_id', 'phase'])
    closure_rates = closure_rates.merge(closure_traffic, on=['zone_id', 'phase'], how='left', validate='many_to_one')
    st.dataframe(closure_rates[['zone_name', 'closure_endpoint', 'phase', 'coin_in_per_available_hour',
                                'zone_entries_per_coverage_hour', 'coverage_hours']], width='stretch')
    st.caption('W-ENT-B40 (Main Entrance ↔ Back Forty) closed March 3–April 7, 2025. '
               'Before/during/after splits use gaming days overlapping the UTC closure interval, '
               'including partial boundary days. Other zones provide context. '
               'Traffic counts sensor crossings, not unique people. These phase rates do not control '
               'for seasonality, events, bet-size mix or displacement and do not identify a closure effect.')
with st.expander('Source'):
    st.markdown('''**Location mart:** `marts/q1_location.parquet`; build with
`uv run python -m royale.build q1_location`. Query and comparison functions:
`royale/marts/q1_location.py`. Grain: machine × month × zone × bank × configuration × closure phase.
Off-floor rows are excluded; locations come from dated placements at gaming-day start.
Traffic hours join UTC gaming-day boundaries; missing counter counts are excluded with their
coverage, rather than treated as zero. Traffic is deduplicated by month/zone/phase before sums.

**Location baseline:** manager's bottom ten by total house win over active on-floor days in the
complete-month window (and selected bank). Peer comparisons match game configuration/title and
month, exclude the subject in every zone, and weight rates by the subject's available hours.
Other-zone traffic rates are weighted by same-title peer hours. Missing peer combinations are
excluded and the matched exposure share is shown. Bank comparisons show the selected title's rates.
Bootstrap: 2,000 paired resamples of calendar months, seed 31, percentile 95% intervals;
at least three matched months. These intervals describe variation across observed months,
assume exchangeable months, and omit placement selection and persistent machine differences.
They are exploratory, with no correction for searching machines/periods. The 90% local-peer
threshold is a screening tolerance, not an equivalence test. No causal location attribution is claimed.
See `findings/31-location.md` for the checked commands, full-window result and limitations.
''')
    st.markdown('''**Mart:** `marts/q1_machines.parquet`; build with
`uv run python -m royale.build q1_machines`. Query: `SQL` in
`royale/marts/q1_machines.py`; period aggregation: `summarize` in that module.

| Measure | Calculation |
|---|---|
| Manager baseline | Active on-floor rows; SUM(house_win_cents), ascending, machine ID breaks ties |
| Active days / availability | COUNT(machine-days); SUM(available_seconds) / SUM(calendar_day.scheduled_seconds) |
| Location / game | placements at gaming-day start; game_math on daily config_id; all visited zones/games listed |
| Theo / luck | SUM(coin-in × (1 − configured RTP)); house win − theo |
| Luck z | residual cents / sqrt(SUM(sum_bet_squared × payout_multiplier_variance)), via royale.money |
| Hold / configured hold | SUM(house win) / SUM(coin-in); SUM(theo) / SUM(coin-in) |
| Observed contribution/hour | (house win − supplied costs) / available hours |
| Adjusted contribution/hour | (theo − supplied costs) / available hours; ascending ranking |
| Supplied costs | Prepared daily lease + service + power + repair costs, counted once |
| Overlap | Intersection of raw bottom ten and adjusted bottom ten |
| Zone peer rate | Other machines' expected contribution/hour in each zone, weighted by subject's available hours |

**Triage rules, in order:** leak-candidate if z < −3.8; location if zone peers are below
floor rate and machine meets its zone peer rate; luck if z < −1.96 or adjusted rank > 10;
weak otherwise. Threshold 3.8 is approximately a one-sided 5% familywise screen across
310 machines; it is not proof of a leak. Repeated period/drill searches invalidate that calibration.

**Limits:** z assumes independent spins and correct game variance. Short periods are noisy.
Adjusted contribution removes realized payout luck but retains supplied realized costs
(including revenue-share leases tied to positive daily house win). It is a descriptive screening
rate, not a replacement counterfactual or full profit: shared labor and nongaming revenue/costs
are excluded. Availability adjustment does not recover demand displaced during outages.
Zone peers do not identify a causal location effect; no game-mix or traffic control is claimed.
See `findings/22-machines.md` for the full-period result and verification.
''')
