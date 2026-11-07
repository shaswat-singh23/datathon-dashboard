# Calendar-only daily floor coin-in forecast
- Issue: #20 | Author: dandelino-del (Codex) | Time: 13:08 America/Chicago, 2026-11-07
- Claim: The weekday-mean model reduces May–June daily coin-in MAE by 68.52% against a constant training-mean baseline. Adding a linear trend performs worse than weekday means alone in this holdout.
- Evidence: `DATA_DIR=/path/to/organizer/data uv run python -m royale.build q7_forecast` and the reproduction command below, using organizer release 0.9.0-draft property_day, downloaded 2026-11-07.
- So what: Use weekday demand patterns rather than a constant daily demand assumption when preparing staffing or promotion schedules, then validate the schedule in a future operational trial. The forecast does not estimate promotion lift or required staffing directly.
- Checked by: Kyle (Claude Code, Fable 5.1), 2026-11-07 16:26

## Full held-out result

| Model | May–June MAE (USD/day) | May MAE | June MAE |
|---|---:|---:|---:|
| Constant Jan–Apr mean (baseline) | $218,258.10 | $233,993.90 | $201,997.77 |
| Weekday mean | **$68,698.55** | $61,360.66 | $76,281.04 |
| Weekday + linear trend | $96,657.83 | $81,473.42 | $112,348.38 |

MAE = mean(abs(predicted daily floor coin-in − actual daily floor coin-in)). Improvement = 1 − weekday MAE / baseline MAE = 68.5242%. The full score weights every held-out day equally; the May and June columns are descriptive diagnostics, not additional tuning splits.

## Specification and decision

Training: January 1–April 30, 2025, 120 daily rows. Test: May 1–June 30, 2025, 61 daily rows. These dates are fixed in code. The constant model uses the training mean; weekday uses seven separate training means; weekday + trend fits seven weekday intercepts and one shared elapsed-day slope by least squares. Elapsed days are measured from Jan 1 and divided by 30 for scaling. Predictions are floored at zero. All coefficients are frozen before scoring the test period.

The alternative explanation tested is that a time trend, beyond recurring weekdays, improves forecasts. It lowers accuracy in this holdout relative to weekday means. This comparison does not prove there is no trend, nor that weekday means will remain best. The best holdout model is identified retrospectively; no further model or feature selection was performed after examining these scores.

Decision changed: replace a uniform daily coin-in assumption in staffing/promotion planning with the weekday profile. Treat the observed weekday-model MAE as a planning tolerance, not a guaranteed bound. Compare a future weekday-based staffing schedule against existing practice using service levels and cost; promotion timing also needs a controlled lift test. Coin-in includes replayed winnings, is a demand proxy, and is neither revenue nor cash visitor spending.

## Leakage and integrity checks

Inputs are only the gaming date's weekday and elapsed calendar days, both known on the prediction date. No LVCVA, survey, event outcomes, repairs, target-derived lags, or holdout-day observations enter prediction. `fit` filters the date window before converting or validating target values. Tests pass holdout targets set to NaN and require exact model equality with training-only fits, then check predictions remain identical when holdout outcomes are changed or removed.

No joins occur. The mart builder requires exactly one raw row for every date Jan–Jun (181 total), fits using 120, and projects the 61 test rows into the committed mart. Actuals are retained solely for scoring/display. The mart is **7,362 bytes**, far below 5 MB. A synthetic weekday + trend series independently checks exact fitted extrapolation, and the constant/weekday tests compare predictions against independently computed training means. Missing dates, duplicate training dates, invalid training values and insufficient weekday coverage are rejected.

The page reads only `io.mart('q7_forecast')`. The validation section explains the split, inputs and MAE in plain language; the chart allows period and model changes. Full-holdout scores remain fixed when changing the chart period, avoiding a misleading cherry-picked headline.

Limitations: one synthetic property and one contiguous holdout; errors may be autocorrelated. Holidays, events, seasonality and demand changes can break weekday patterns. No formal prediction interval, causal effect or guaranteed staffing benefit is claimed. MAE is an observed error summary, not a confidence band. Model specifications were written before the first local scoring run, but this was retrospective development on an existing synthetic dataset rather than a prospective forecast experiment.

## Reproduction

```bash
DATA_DIR=/path/to/organizer/data uv run python -m royale.build q7_forecast
uv run pytest tests/test_model.py -q
uv run python - <<'PY'
from royale import io
from royale.model import KINDS
m = io.mart('q7_forecast')
assert len(m) == 61
assert m.gaming_date.min().strftime('%Y-%m-%d') == '2025-05-01'
assert m.gaming_date.max().strftime('%Y-%m-%d') == '2025-06-30'
assert m.training_days.eq(120).all()
for kind in KINDS:
    error = (m[f'{kind}_prediction_usd'] - m.coin_in_usd).abs()
    print(kind, 'MAE', error.mean(),
          'May', error[m.gaming_date.dt.month == 5].mean(),
          'June', error[m.gaming_date.dt.month == 6].mean())
PY
```

Verification: model tests **7 passed**. Full repository suite with only the action catalog available to existing raw-data tests: **42 passed, 3 skipped** (other raw datasets unavailable). Streamlit AppTest passes default render, shorter chart period, one selected forecast and no selected forecasts; official MAE table equality is asserted after chart filtering. `git diff --check` passes.

```bash
uv run python - <<'PY'
from pathlib import Path
from datetime import date
from streamlit.testing.v1 import AppTest
at = AppTest.from_file(str(Path('pages/7_model.py').resolve()), default_timeout=30).run()
assert not at.exception
scores = at.dataframe[0].value.copy()
at.slider[0].set_value((date(2025, 5, 1), date(2025, 5, 11))).run()
assert not at.exception
assert scores.equals(at.dataframe[0].value)
at.multiselect[0].set_value(['weekday']).run()
assert not at.exception
at.multiselect[0].set_value([]).run()
assert not at.exception
PY
```
