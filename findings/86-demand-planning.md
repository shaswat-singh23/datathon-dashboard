# Frozen forecasts align review days with held-out demand
- Issue: #86 | Author: sahith1021 (Codex) | Time: 17:14 America/Chicago, 2026-11-07
- Claim: A fixed two-day weekly operational-review scenario selected from frozen January–April weekday forecasts covers 35.6841% of observed wagers in complete May–June weeks, versus 28.5714% expected under uniform allocation of the same review-day slots. This is retrospective demand alignment, not a staffing or financial effect.
- Evidence: `royale.planning.evaluate_planning(io.mart('q7_forecast'), 2)` gives eight complete weeks, 56 evaluation days and 16 review-day slots. Weekday forecasts select Friday and Saturday; gain is 7.1126 percentage points. Paired week-bootstrap 95% interval: [6.4573, 7.8579] percentage points, 2,000 resamples, seed 86. Independent reviewer reconstructed selection and enumerated uniform allocations; a separate 50,000-resample bootstrap gave [6.4297, 7.8325] percentage points.
- So what: The calendar forecast changes which days management would review under a fixed time budget. Prospective service measurements are required before claiming better service, changing headcount or pricing a benefit.
- Checked by: independent Codex judge_dashboard agent, 2026-11-07; direct frozen ranking, equal-slot accounting, uniform-allocation enumeration and independent week bootstrap (not human review).

| Review days/week | Selected weekdays | Complete weeks | Review-day slots | Observed wager share | Uniform expected share | Gain, percentage points | Exploratory 95% interval, pp |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | Saturday | 8 | 8 | 18.7920% | 14.2857% | 4.5063 | [4.0115, 5.0917] |
| 2 (default scenario) | Friday, Saturday | 8 | 16 | 35.6841% | 28.5714% | 7.1126 | [6.4573, 7.8579] |
| 3 | Friday, Saturday, Sunday | 8 | 24 | 50.6313% | 42.8571% | 7.7742 | [6.7972, 9.0089] |

**Source/query:** `marts/q7_forecast.parquet`, one frozen forecast/actual row per held-out gaming date; builder `royale/marts/q7_forecast.py`. Selection code `royale/planning.py:choose_days` reads dates and predicted values only. Within complete Monday–Sunday weeks, select the largest k frozen predictions, breaking ties by earlier date. Evaluation joins actual wagers afterward, with a one-to-one date join. Ratio of sums uses `royale.money.hold`. No raw data or refitting is used.

**Baselines:** A uniform k-of-seven weekly allocation has exactly k/7 expected demand coverage using the same k equal-length review-day slots. This is an expectation over assignments, not a claimed realized random schedule. Also show the constant training-mean forecast policy with deterministic earlier-date ties: at k=2 it selects Monday/Tuesday and covers 23.8790% of wagers. That arbitrary tie rule is not the primary neutral baseline. The fitted weekday-plus-trend policy chooses the same days as the weekday policy here; its poorer MAE does not imply a different ordering of weekdays.

**Selection and exclusions:** Full holdout is May 1–June 30 (61 days). Eligible complete weeks are May 5–June 29 (56 days); May 1–4 and June 30 are excluded equally for every policy. The date filter reevaluates only full weeks contained in its window. Fewer than three weeks gives point estimates without intervals; no complete week gives an explanatory message. Slot counts 1/2/3 are displayed sensitivity scenarios, not values optimized on holdout outcomes.

**Alternative explanation:** Weekend wagers are high, and a simple weekday rule captures that pattern without fitted regression. High wagers can reflect bet size, repeat betting or player mix rather than service demand. No experiment established that an operational review on these days changes any outcome.

**Limitations:** This policy/metric was specified after the original forecast holdout had been examined; it is an exploratory retrospective diagnostic, not an untouched policy-validation experiment. Frozen forecast coefficients still use January–April only, and chosen dates never read holdout actuals. The interval resamples paired whole observed weeks and ratios their summed selected/all demand. It assumes exchangeable weeks, describes variation relative to the *expected* uniform comparator, and excludes random realized-assignment variation, July regime shifts, treatment effects and policy-selection uncertainty. Eight weeks provide limited evidence. Coin-in includes replayed winnings and is neither revenue nor staffing workload. Review slots are hypothetical equal-length units, not priced catalogue actions or a change to the July spending plan.

**Measurement plan:** Before a July trial, record review-slot length, total reviewer hours, service requests and waiting-time measures. Keep total hours equal and randomize comparable weeks between weekday and uniform scheduling. Prespecify the minimum worthwhile improvement in handled requests per reviewer-hour and the permitted waiting-time change on other days. Report both arms, differences and uncertainty; make an adoption decision only against those prespecified thresholds. No dollar benefit is assigned from these historical wagers.

Reproduce from the repo root:

```bash
uv run pytest tests/test_planning.py -q
uv run python - <<'PY'
from royale import io
from royale.planning import evaluate_planning
for slots in (1, 2, 3):
    summary, schedule = evaluate_planning(io.mart('q7_forecast'), slots)
    print(slots, summary.to_string(index=False))
PY
```

`uv` is absent from this session's PATH; validation used the existing locked environment's `.venv/bin/python` for equivalent commands. Tests poison/remove actuals and shuffle rows to verify unchanged choices, check equal resources, missing dates/boundary weeks, zero demand, weighted ratios, reproducibility and page filter/drill behavior without raw reads or refitting.
