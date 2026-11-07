"""Forecast evaluation from a committed mart; calendar-only inputs."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from royale import io
from royale.model import KINDS, LABELS

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
st.markdown('**Baseline:** the constant mean daily coin-in during training. **Weekday mean:** the training mean for each weekday. '
            '**Weekday + linear trend:** seven weekday intercepts and one shared linear time slope, fitted by least squares. '
            'Negative predictions are clipped to zero. These specifications are fixed; no hyperparameters are selected using the test period.')

scores = pd.DataFrame([{'Model': LABELS[k], 'MAE (USD/day)': (data[f'{k}_prediction_usd'] - data.coin_in_usd).abs().mean()}
                       for k in KINDS])
baseline = scores.iloc[0]['MAE (USD/day)']
scores['Change vs baseline'] = (baseline - scores['MAE (USD/day)']) / baseline if baseline else float('nan')
st.subheader('Full held-out test: mean absolute error')
st.caption('MAE is the average absolute dollar error per day; smaller is better. Positive change means improvement. '
           'This table always scores the full May–June holdout, regardless of the chart filter below.')
st.dataframe(scores, hide_index=True, column_config={'MAE (USD/day)': st.column_config.NumberColumn(format='dollar'),
              'Change vs baseline': st.column_config.NumberColumn(format='percent')})
winner = scores.loc[scores['MAE (USD/day)'].idxmin()]
st.metric('Lowest observed holdout MAE', f"${winner['MAE (USD/day)']:,.0f}/day", winner['Model'])
st.info('Decision: use the weekday profile as a starting point for staffing and promotion timing, '
        'with the holdout error as a planning tolerance. Check whether weekday scheduling beats constant staffing in a future trial. '
        'Coin-in is a demand proxy; this forecast does not estimate staffing needs or promotion lift directly. '
        'The lowest error in this one holdout does not establish future superiority.')

start, end = st.slider('Chart period', min_value=data.gaming_date.min().date(), max_value=data.gaming_date.max().date(),
                       value=(data.gaming_date.min().date(), data.gaming_date.max().date()))
selected = st.multiselect('Forecasts to compare', list(KINDS), default=list(KINDS), format_func=LABELS.get)
view = data[data.gaming_date.dt.date.between(start, end)]
fig = go.Figure(go.Scatter(x=view.gaming_date, y=view.coin_in_usd, name='Actual coin-in', line=dict(color='#222222')))
for kind, color in zip(KINDS, ['#777777', '#2a78d6', '#eb6834']):
    if kind in selected:
        fig.add_trace(go.Scatter(x=view.gaming_date, y=view[f'{kind}_prediction_usd'], name=LABELS[kind], line=dict(color=color)))
fig.update_layout(height=380, yaxis_title='Daily coin-in (USD)', hovermode='x unified', yaxis_tickformat='$,.0f')
st.plotly_chart(fig, width='stretch')
st.dataframe(view, hide_index=True)
st.caption('Uncertainty: errors may be correlated over time, and events or demand shifts can break calendar patterns. '
           'MAE describes this holdout’s observed error; it is not a prediction interval or a guaranteed error bound.')
with st.expander('Source and reproducibility'):
    st.markdown('**Mart:** `marts/q7_forecast.parquet`, one row per held-out gaming date. '
                '**Builder:** `royale/marts/q7_forecast.py`, selecting gaming_date and coin_in_usd from property_day without joins. '
                '**Model:** `royale/model.py`; fit filters to Jan–Apr internally and predict consumes only dates. '
                '**Verification:** `tests/test_model.py` poisons holdout outcomes and confirms identical fitted coefficients and predictions. '
                '**Evidence:** [findings/20-coin-in-forecast.md](https://github.com/shaswat-singh23/datathon-dashboard/blob/master/findings/20-coin-in-forecast.md).')
    st.code('DATA_DIR=/path/to/data uv run python -m royale.build q7_forecast\nuv run pytest tests/test_model.py -q')
