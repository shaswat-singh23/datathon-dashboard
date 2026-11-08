"""Forecast evaluation from a committed mart; calendar-only inputs."""
import calendar

import pandas as pd
import streamlit as st

from royale.evidence import render_evidence
from royale.filters import independent_scope_note
from royale.theme import apply_theme

from royale import io, visuals
from royale.model import FITTED_KIND, KINDS, LABELS, score_forecasts
from royale.overview import weekday_profile
from royale.planning import evaluate_planning

st.set_page_config(page_title='Coin-in forecast: The Gilded Ace', page_icon='♠', layout='wide')
apply_theme("Forecast & validation", compact=True)
st.title('Can the calendar improve a daily demand forecast?')
st.caption('Daily whole-floor coin-in in a fictional casino. Coin-in includes replayed winnings; it is not revenue or visitor spending.')
try:
    data = io.mart('q7_forecast')
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()
data['gaming_date'] = pd.to_datetime(data.gaming_date)

full_scores = score_forecasts(data)
winner = full_scores.idxmin()
if winner == 'weekday':
    st.subheader('Result: the simple weekday average forecast best')
    st.markdown(f'On the held-out May–June days, the **weekday-mean baseline** had the lowest error: '
                f'**${full_scores["weekday"]:,.0f}/day** mean absolute error, versus '
                f'${full_scores[FITTED_KIND]:,.0f}/day for the fitted weekday + trend regression and '
                f'${full_scores["constant"]:,.0f}/day for the constant training mean. '
                'The fitted model did not beat the simpler seasonal baseline.')
else:
    st.subheader(f'Result: {LABELS[winner]} forecast best')
    st.markdown(f'On the held-out May–June days, **{LABELS[winner]}** had the lowest error '
                f'(${full_scores[winner]:,.0f}/day MAE); the weekday-mean baseline scored '
                f'${full_scores["weekday"]:,.0f}/day.')
st.plotly_chart(visuals.mae_chart(visuals.mae_table(full_scores, LABELS)), width='stretch')
lead_planning, _ = evaluate_planning(data, 2)
if not lead_planning.empty and 'weekday' in set(lead_planning.kind):
    lead_row = lead_planning.set_index('kind').loc['weekday']
    st.markdown(f'**Decision implication:** use the weekday profile to pick busy days for limited operational '
                f'reviews. Over the full holdout, two weekday-chosen review days per week covered '
                f'{lead_row.demand_share:.1%} of coin-in versus {lead_row.uniform_share:.1%} for a uniform allocation '
                f'({lead_row.gain_pp:+.1f} pp; week-bootstrap 95% range {lead_row.gain_low_pp:+.1f} to '
                f'{lead_row.gain_high_pp:+.1f} pp). See the review-day planning comparison below. '
                'This is retrospective demand alignment, not a staffing or revenue effect.')
st.caption('Scores come from forecasts frozen after fitting on January–April; nothing on this page refits a model. '
           'Coin-in is a demand proxy; this forecast does not estimate staffing needs or promotion lift directly. '
           'One holdout cannot establish future superiority.')

st.caption(independent_scope_note('May–June evaluation scope: the frozen forecasts are scored only on the May 1–June 30 holdout'))
start, end = st.slider('Evaluation period', min_value=data.gaming_date.min().date(), max_value=data.gaming_date.max().date(),
                       value=(data.gaming_date.min().date(), data.gaming_date.max().date()))
view = data[data.gaming_date.dt.date.between(start, end)]
selected_scores = score_forecasts(view)
scores = pd.DataFrame({'Model': [LABELS[k] for k in KINDS],
                       'Full holdout MAE (USD/day)': full_scores.to_numpy(),
                       'Selected period MAE (USD/day)': selected_scores.to_numpy()})
baseline = full_scores['constant']
scores['Full holdout improvement vs constant'] = (baseline - full_scores.to_numpy()) / baseline if baseline else float('nan')
st.subheader('Forecast accuracy: full holdout and selected period')
st.caption('MAE is the average absolute dollar error per day; smaller is better. Positive change means improvement. '
           f'Full holdout: {len(data)} days, May 1–June 30. Selected period: {start:%b %d}–{end:%b %d}, {len(view)} days. '
           'The period filter changes the selected scores, chart and drill. Full-holdout scores stay fixed; no model is refitted.')
st.dataframe(scores, hide_index=True, column_config={
    'Full holdout MAE (USD/day)': st.column_config.NumberColumn(format='dollar'),
    'Selected period MAE (USD/day)': st.column_config.NumberColumn(format='dollar'),
    'Full holdout improvement vs constant': st.column_config.NumberColumn(format='percent')})
st.metric('Lowest observed full-holdout MAE', f'${full_scores[winner]:,.0f}/day', LABELS[winner])
gap = full_scores[FITTED_KIND] - full_scores['weekday']
if gap >= 0:
    st.info(f'The fitted weekday + trend regression does not beat the weekday-mean baseline: '
            f'its full-holdout MAE is ${gap:,.2f}/day higher ({gap / full_scores["weekday"]:.2%}).')
else:
    st.info(f'The fitted weekday + trend regression beats the weekday-mean baseline by '
            f'${-gap:,.2f}/day on this holdout.')
selected = st.multiselect('Forecasts to compare', list(KINDS), default=list(KINDS), format_func=LABELS.get)
st.plotly_chart(visuals.forecast_chart(view, [k for k in KINDS if k in selected], LABELS), width='stretch')
st.caption('Black: actual daily coin-in. Lines: frozen predictions for the selected forecasts, stored in the mart.')

st.subheader('Validation: earlier months train, later months test')
st.markdown('**Training:** January 1–April 30, 2025 (120 days). **Held-out test:** May 1–June 30, 2025 (61 days). '
            'Each forecast is fitted once on the training period, then frozen for the entire test horizon. '
            'Inputs are the gaming date’s weekday and, for the trend model, elapsed calendar days. '
            'No test-day results, lagged holdout outcomes, later-published tourism, surveys, or future repairs are used.')
st.markdown('**Constant baseline:** the mean daily coin-in during training. **Weekday baseline:** the training mean for each weekday. '
            '**Fitted regression (weekday + linear trend):** seven weekday intercepts and one shared linear time slope, fitted by least squares. '
            'Negative predictions are clipped to zero. These specifications are fixed; no hyperparameters are selected using the test period.')

st.subheader('Where are the forecast errors?')
drill = st.radio('Error breakdown', ['Month', 'Weekday'], horizontal=True)
groups = view.gaming_date.dt.strftime('%Y-%m') if drill == 'Month' else view.gaming_date.dt.day_of_week
breakdown = pd.DataFrame([
    {drill: period if drill == 'Month' else calendar.day_name[period], 'Days': len(rows),
     **{LABELS[kind]: error for kind, error in score_forecasts(rows).items()}}
    for period, rows in view.groupby(groups, sort=True)
])
st.caption('MAE (USD/day) within the selected period. Each day has equal weight; '
           'the overall MAE weights each group by its day count. These groups are diagnostics, not tuning splits.')
st.dataframe(breakdown, hide_index=True, column_config={
    LABELS[kind]: st.column_config.NumberColumn(format='dollar') for kind in KINDS
})
with st.expander('Daily actuals and frozen predictions'):
    st.dataframe(view, hide_index=True)
st.caption('Uncertainty: errors may be correlated over time, and events or demand shifts can break calendar patterns. '
           'MAE describes this holdout’s observed error; it is not a prediction interval or a guaranteed error bound.')
st.subheader('Training calendar profile')
profile = weekday_profile(data)
st.dataframe(profile, column_config={
    'weekday_prediction_usd': st.column_config.NumberColumn('Training weekday mean coin-in / day', format='dollar'),
    'constant_prediction_usd': st.column_config.NumberColumn('Constant training mean / day', format='dollar'),
    'vs_constant': st.column_config.NumberColumn('Demand above/below constant', format='percent'),
})
st.caption('Fixed January–April estimates recovered from the frozen forecast columns, Monday to Sunday. '
           'The evaluation-period filter does not change this training profile. '
           'Wagers do not translate directly into staff hours, so these are demand comparisons rather than headcounts.')
st.subheader('Decision test: when to schedule limited operational reviews?')
st.write('Planning scenario: reserve a fixed number of equal-length floor-service review slots each week. '
         'Use each frozen forecast to prioritize the days expected to be busiest. The same number of slots '
         'allocated uniformly across the week is the neutral baseline. This tests alignment with demand; '
         'coin-in alone cannot establish staffing requirements, labor savings or increased revenue.')
slots = st.selectbox('Review days per complete week', [1, 2, 3], index=1)
planning, schedules = evaluate_planning(view, slots)
if planning.empty:
    st.info('Include a complete Monday–Sunday week to evaluate planning. Partial weeks are excluded from every policy.')
else:
    st.caption('Days are chosen using frozen predictions only, before looking at actual demand. '
               'Within each complete Monday–Sunday week, select the highest predicted days; ties use the earlier date. '
               'The constant forecast therefore selects Monday onward. A uniform allocation uses the same slot '
               'count and has an exact expected demand share of k/7. Actual coin-in is used only for evaluation. '
               'Boundary weeks and weeks missing a date are excluded for all policies. '
               'One, two and three slots are sensitivity scenarios, not choices optimized on this holdout.')
    st.dataframe(planning[['model', 'weeks', 'review_days', 'demand_share', 'uniform_share',
                          'gain_pp', 'gain_low_pp', 'gain_high_pp']], hide_index=True, width='stretch',
                 column_config={
                     'model': 'Frozen forecast policy', 'weeks': 'Weeks', 'review_days': 'Slots',
                     'demand_share': st.column_config.NumberColumn('Review-day demand share', format='percent'),
                     'uniform_share': st.column_config.NumberColumn('Uniform expected share', format='percent'),
                     'gain_pp': st.column_config.NumberColumn('Gain vs uniform (pp)', format='%.2f', help='Percentage points'),
                     'gain_low_pp': st.column_config.NumberColumn('Gain 95% low (pp)', format='%.2f'),
                     'gain_high_pp': st.column_config.NumberColumn('Gain 95% high (pp)', format='%.2f'),
                 })
    st.plotly_chart(visuals.planning_chart(planning), width='stretch')
    chosen = schedules[(schedules.kind == 'weekday') & schedules.priority_day]
    names = sorted(chosen.gaming_date.dt.day_of_week.unique())
    st.info('Operational candidate: the training-only weekday rule selects '
            + ', '.join(calendar.day_name[int(day)] for day in names)
            + f' for {slots} weekly review-day slots. Validate this schedule prospectively before changing staffing. '
              'The retrospective comparison does not prove a service or financial benefit.')
    st.caption('Coverage is total actual coin-in on selected days / total actual coin-in on all eligible days '
               '(ratio of sums). Intervals resample paired complete weeks 2,000 times, seed 86, and require '
               'three weeks; they assume exchangeable weeks and omit regime changes and policy-selection uncertainty. '
               'They are exploratory demand-alignment intervals, not July forecasts or treatment effects.')
    with st.expander('Review-day schedule and measurement plan'):
        schedule_kind = st.selectbox('Planning forecast drill', list(KINDS), index=1, format_func=LABELS.get)
        st.dataframe(schedules.loc[schedules.kind == schedule_kind,
                                  ['gaming_date', 'week', 'priority_day', 'coin_in_usd']], hide_index=True,
                     column_config={'coin_in_usd': st.column_config.NumberColumn('Observed coin-in ($)', format='dollar')})
        st.write('Before a July trial, record slot length, reviewer hours and service demand measures. '
                 'Keep total review hours equal; randomize comparable weeks between the weekday schedule '
                 'and uniform allocation. Measure service requests handled and wait time per reviewer-hour. '
                 'Adopt only if the prespecified service target improves without worse waits on other days. '
                 'No dollar benefit is assigned until intervention data exist.')
    st.markdown('[Planning evidence, baseline and limitations]('
                'https://github.com/shaswat-singh23/datathon-dashboard/blob/master/findings/86-demand-planning.md)')
with st.expander('Source and reproducibility'):
    render_evidence(['findings/47-forecast-evaluation.md', 'findings/86-demand-planning.md',
                     'findings/86-dashboard-judge.md', 'findings/20-coin-in-forecast.md'], key='7_model')
    st.markdown('**Mart:** `marts/q7_forecast.parquet`, one row per held-out gaming date. '
                '**Builder:** `royale/marts/q7_forecast.py`, selecting gaming_date and coin_in_usd from property_day without joins. '
                '**Model:** `royale/model.py`; fit filters to Jan–Apr internally and predict consumes only dates. '
                '**Verification:** `tests/test_model.py` poisons holdout outcomes and confirms identical fitted coefficients and predictions. '
                '**Evidence:** [findings/47-forecast-evaluation.md](https://github.com/shaswat-singh23/datathon-dashboard/blob/master/findings/47-forecast-evaluation.md), '
                'including reconciliation of property totals against on-floor machine meters.')
    st.code('DATA_DIR=/path/to/data uv run python -m royale.build q7_forecast\nuv run pytest tests/test_model.py -q')
    st.markdown('**Planning calculations:** `royale/planning.py`, reading the same frozen forecast mart. '
                '`choose_days` consumes dates and predictions only; `evaluate_planning` joins actuals afterward. '
                'The policy is a new retrospective diagnostic, specified after the original forecast holdout '
                'was examined; prospective validation is required. Tests poison actuals and verify unchanged day choices.')
