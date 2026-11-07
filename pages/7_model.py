"""Forecast evaluation from a committed mart; calendar-only inputs."""
import calendar

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from royale.evidence import render_evidence

from royale import io
from royale.model import FITTED_KIND, KINDS, LABELS, score_forecasts
from royale.overview import weekday_profile

st.set_page_config(page_title='Coin-in forecast: The Gilded Ace', page_icon='♠', layout='wide')
st.title('Can the calendar improve a daily demand forecast?')
st.caption('Daily whole-floor coin-in in a fictional casino. Coin-in includes replayed winnings; it is not revenue or visitor spending.')
try:
    data = io.mart('q7_forecast')
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()
data['gaming_date'] = pd.to_datetime(data.gaming_date)

st.subheader('Validation: earlier months train, later months test')
st.markdown('**Training:** January 1–April 30, 2025 (120 days). **Held-out test:** May 1–June 30, 2025 (61 days). '
            'Each forecast is fitted once on the training period, then frozen for the entire test horizon. '
            'Inputs are the gaming date’s weekday and, for the trend model, elapsed calendar days. '
            'No test-day results, lagged holdout outcomes, later-published tourism, surveys, or future repairs are used.')
st.markdown('**Constant baseline:** the mean daily coin-in during training. **Weekday baseline:** the training mean for each weekday. '
            '**Fitted regression (weekday + linear trend):** seven weekday intercepts and one shared linear time slope, fitted by least squares. '
            'Negative predictions are clipped to zero. These specifications are fixed; no hyperparameters are selected using the test period.')

start, end = st.slider('Evaluation period', min_value=data.gaming_date.min().date(), max_value=data.gaming_date.max().date(),
                       value=(data.gaming_date.min().date(), data.gaming_date.max().date()))
view = data[data.gaming_date.dt.date.between(start, end)]
full_scores = score_forecasts(data)
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
winner = full_scores.idxmin()
st.metric('Lowest observed full-holdout MAE', f'${full_scores[winner]:,.0f}/day', LABELS[winner])
gap = full_scores[FITTED_KIND] - full_scores['weekday']
if gap >= 0:
    st.info(f'The fitted weekday + trend regression does not beat the weekday-mean baseline: '
            f'its full-holdout MAE is ${gap:,.2f}/day higher ({gap / full_scores["weekday"]:.2%}).')
else:
    st.info(f'The fitted weekday + trend regression beats the weekday-mean baseline by '
            f'${-gap:,.2f}/day on this holdout.')
st.info('Decision: use the weekday profile as a starting point for staffing timing, '
        'and use the holdout MAE to describe typical observed error. Check whether weekday scheduling beats constant staffing in a future trial. '
        'Coin-in is a demand proxy; this forecast does not estimate staffing needs or promotion lift directly. '
        'The lowest error in this one holdout does not establish future superiority.')

selected = st.multiselect('Forecasts to compare', list(KINDS), default=list(KINDS), format_func=LABELS.get)
fig = go.Figure(go.Scatter(x=view.gaming_date, y=view.coin_in_usd, name='Actual coin-in', line=dict(color='#222222')))
for kind, color in zip(KINDS, ['#777777', '#2a78d6', '#eb6834']):
    if kind in selected:
        fig.add_trace(go.Scatter(x=view.gaming_date, y=view[f'{kind}_prediction_usd'], name=LABELS[kind], line=dict(color=color)))
fig.update_layout(height=380, yaxis_title='Daily coin-in (USD)', hovermode='x unified', yaxis_tickformat='$,.0f')
st.plotly_chart(fig, width='stretch')

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
st.subheader('A calendar profile for a staffing trial')
profile = weekday_profile(data)
st.dataframe(profile, column_config={
    'weekday_prediction_usd': st.column_config.NumberColumn('Training weekday mean coin-in / day', format='dollar'),
    'constant_prediction_usd': st.column_config.NumberColumn('Constant training mean / day', format='dollar'),
    'vs_constant': st.column_config.NumberColumn('Demand above/below constant', format='percent'),
})
st.caption('Fixed January–April estimates recovered from the frozen forecast columns, Monday to Sunday. '
           'The evaluation-period filter does not change this training profile. '
           'Wagers do not translate directly into staff hours, so these are demand comparisons rather than headcounts.')
st.markdown('**Prospective test:** keep total weekly staff hours fixed and compare weekday-profile allocation '
            'with constant daily allocation in a randomized sequence of weeks. Before starting, choose the '
            'minimum worthwhile reduction in fault waiting hours per 1,000 scheduled machine-hours and the '
            'maximum acceptable change in availability. Report both arms, their difference and uncertainty. '
            'Adopt the profile only if it clears that predeclared target without breaching the availability '
            'guardrail. No staffing saving or revenue lift is assumed from this retrospective forecast.')

with st.expander('Source and reproducibility'):
    render_evidence(['findings/47-forecast-evaluation.md', 'findings/20-coin-in-forecast.md'], key='7_model')
    st.markdown('**Mart:** `marts/q7_forecast.parquet`, one row per held-out gaming date. '
                '**Builder:** `royale/marts/q7_forecast.py`, selecting gaming_date and coin_in_usd from property_day without joins. '
                '**Model:** `royale/model.py`; fit filters to Jan–Apr internally and predict consumes only dates. '
                '**Verification:** `tests/test_model.py` poisons holdout outcomes and confirms identical fitted coefficients and predictions. '
                '**Evidence:** [findings/47-forecast-evaluation.md](https://github.com/shaswat-singh23/datathon-dashboard/blob/master/findings/47-forecast-evaluation.md), '
                'including reconciliation of property totals against on-floor machine meters.')
    st.code('DATA_DIR=/path/to/data uv run python -m royale.build q7_forecast\nuv run pytest tests/test_model.py -q')
