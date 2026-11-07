"""Q1 machine rankings from the committed daily mart."""
import pandas as pd
import streamlit as st
from royale import io
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

st.subheader('Leak: inspect, not proof')
st.caption('Payout ratios are compared with configured RTP using each game’s payout variance and actual '
           'squared bets. The period and bank selections above also apply here.')
try:
    from royale.marts.q1_leak import Z_THRESHOLD, summarize as summarize_leak, volatility_check

    leak_daily = io.mart('q1_leak')
except FileNotFoundError as exc:
    st.warning(str(exc))
else:
    leak_daily['gaming_date'] = pd.to_datetime(leak_daily.gaming_date)
    leak_selected = leak_daily[leak_daily.gaming_date.dt.date.between(start, end)]
    if bank != 'All banks':
        leak_selected = leak_selected[leak_selected.bank_id == bank]
    if leak_selected.empty:
        st.info('No payout-screen data in this selection.')
    else:
        leak = summarize_leak(leak_selected)
        leak['manager_raw_rank'] = ranked.raw_rank.reindex(leak.index)
        candidates = leak[leak.inspection_candidate]
        st.metric('Payout inspection candidates', f'{len(candidates)} / {leak.payout_z.notna().sum()} tested')
        st.caption(f'Flag: configured RTP falls outside observed RTP ± {Z_THRESHOLD:g} standard errors. '
                   'Positive payout z means higher payouts than configured; negative means lower payouts. '
                   'Normal intervals are approximate and are not clipped to 0–100%.')
        if candidates.empty:
            st.info('No machine crosses the payout-inspection threshold in this selection.')
        else:
            st.dataframe(candidates[[
                'manager_raw_rank', 'game', 'volatility_class', 'paid_spins', 'available_hours',
                'observed_rtp', 'configured_rtp', 'ci_lower', 'ci_upper', 'payout_z',
                'direction', 'excess_payout_per_hour',
            ]], width='stretch', column_config={
                name: st.column_config.NumberColumn(name.replace('_', ' ').title(), format='percent')
                for name in ['observed_rtp', 'configured_rtp', 'ci_lower', 'ci_upper']
            })
        st.markdown('**Volatility check** — compare the variance-adjusted screen with the simple '
                    'per-machine 95% screen (|z| > 1.96). Rates use testable machines only.')
        st.dataframe(volatility_check(leak), width='stretch', column_config={
            name: st.column_config.NumberColumn(name.replace('_', ' ').title(), format='percent')
            for name in ['flag_rate', 'unadjusted_95_rate', 'median_rtp_se']
        })
        st.info('Inspect payout meters, game configuration and service records; these are leads, not proof '
                'of a leak or wrongdoing. The ±3.8 rule gives an approximate two-sided familywise error '
                'bound below 5% across 310 machines under independent normal assumptions. Repeated period '
                'or bank searches invalidate that guarantee. Short samples and heavy tails weaken the '
                'normal approximation. Volatility-class rates are descriptive; they do not establish '
                'equal false-positive rates or a cause. Zero-play/zero-variance rows are not tested.')
        with st.expander('Leak source and method'):
            st.markdown('''**Mart:** `marts/q1_leak.parquet`, one active on-floor machine-day per row,
built with `uv run python -m royale.build q1_leak`. `SQL`, `summarize` and
`volatility_check` in `royale/marts/q1_leak.py` define the query and period calculations.
Locations come from placements at gaming-day start; off-floor rows are excluded.

- Observed RTP = SUM(payout_cents) / SUM(coin_in_cents).
- Configured RTP = 1 − SUM(theo_cents) / SUM(coin_in_cents), wager-weighted across configurations.
- V = SUM(sum_bet_squared × payout_multiplier_variance), in cents squared.
  Squared bets already sum over paid spins; multiplying by spins again would overstate variance.
- RTP standard error = sqrt(V) / SUM(coin_in_cents); interval = observed RTP ± 3.8 × standard error.
- Payout z = −house-win luck z from `royale.money`; a positive value means excess payouts.
- Excess payout/hour = (SUM(theo_cents) − SUM(house_win_cents)) / 100 / available hours.
- Manager rank is the raw total-house-win baseline above, recomputed for the same selection.

Daily mart intervals are diagnostic. Period intervals are recomputed from summed meters and
variances, never averaged. Mixed volatility configurations are reported as `mixed`.
The interval assumes the supplied game variance is correct and spins are independent;
it does not measure the chance of wrongdoing. See `findings/32-leak-screen.md`.
''')

with st.expander('Source'):
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
