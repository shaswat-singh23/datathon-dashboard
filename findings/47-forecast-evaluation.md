# Fitted demand forecast versus constant and weekday baselines
- Issue: #47 | Author: sahith1021 (Codex) | Time: 14:24 America/Chicago, 2026-11-07
- Claim: The weekday-mean baseline wins the May–June holdout at $68,698.55/day MAE. The fitted weekday-plus-trend regression does not beat it: MAE is $27,959.28/day (40.70%) higher. Weekday means improve on the constant baseline by $149,559.55/day (68.52%).
- Evidence: The reproduction below rebuilds all 61 frozen forecasts from raw `property_day`, matches the committed mart, scores each method, and reconciles daily property coin-in against on-floor machine meters.
- So what: Calendar regression is not automatically better than a seasonal baseline. Retain the weekday profile as a planning starting point and test scheduling changes prospectively; coin-in forecasts do not establish staffing requirements or promotion lift.
- Checked by: unchecked

| Method | Full May–June MAE (USD/day) | May (31 days) | June (30 days) |
|---|---:|---:|---:|
| Constant training mean | $218,258.10 | $233,993.90 | $201,997.77 |
| Weekday training mean | **$68,698.55** | $61,360.66 | $76,281.04 |
| Fitted weekday + linear trend | $96,657.83 | $81,473.42 | $112,348.38 |

The fitted regression was already present in #20. This ticket distinguishes it from the two baselines and adds selected-period evaluation and month/weekday error drills; it does not introduce another model after inspecting holdout scores. The existing regression fits seven weekday intercepts and one shared slope by least squares on January 1–April 30 only (120 days). Predictions use the date alone, with elapsed days measured from January 1 in 30-day units, and are clipped at zero. Coefficients remain frozen for May 1–June 30 (61 days). No holdout targets, later-published tourism or survey data, or target-derived lag features enter fitting or prediction.

MAE is the equally weighted mean of absolute daily dollar errors. The page displays full-holdout and selected-period MAE together for all three methods. Filtering updates selected-period scores, the chart, and either a month or weekday drill without refitting; the full-holdout score and winner stay fixed. Group MAEs require weighting by day count to recover overall MAE, rather than taking an unweighted mean of group means.

## Target reconciliation

January–June `property_day.coin_in_usd` (181 unique daily rows) totals **$248,905,219.25**. All 56,110 `machine_day` rows include **1,018 off-floor rows** (`location_id IS NULL`); excluding them leaves **55,092 on-floor machine-days**, grouped into 181 daily rows. Convert the summed `coin_in_cents` with `royale.money.cents_to_usd`: the on-floor total is also **$248,905,219.25**, a **$0.00** total difference and **$0.00** maximum daily difference. A validated one-to-one outer join retains 181 rows, all matched, with no missing dates or row multiplication. The committed `property_day` mart's dates and coin-in match the raw property table, and rebuilding Q7 matches its committed 61 rows and every prediction exactly.

The reconciliation joins two daily aggregates for verification only. The forecast builder reads `gaming_date` and `coin_in_usd` directly from `property_day`, without joins, and rejects missing or duplicated dates.

## Reproduction

Requires organizer data release `0.9.0-draft` through `DATA_DIR` (local clone `/home/sahith/dashboard-royale/data`). Raw data are read only; no committed mart needs to change.

```bash
uv run pytest -q
uv run python - <<'PY'
import numpy as np
import pandas as pd
from royale import io, money
from royale.marts.q7_forecast import build
from royale.model import score_forecasts

con = io.connect()
prop = con.sql('''
    SELECT gaming_date, CAST(coin_in_usd AS DOUBLE) AS coin_in_usd
    FROM property_day ORDER BY gaming_date
''').df()
machine = con.sql('''
    SELECT gaming_date, count(*) AS machine_rows,
           sum(coin_in_cents) AS coin_in_cents
    FROM machine_day WHERE location_id IS NOT NULL
    GROUP BY gaming_date ORDER BY gaming_date
''').df()
print('machine rows, off-floor rows:', con.sql('''
    SELECT count(*), count(*) FILTER (WHERE location_id IS NULL)
    FROM machine_day
''').fetchall())
machine['machine_coin_in_usd'] = money.cents_to_usd(machine.coin_in_cents)
joined = prop.merge(machine, on='gaming_date', how='outer',
                    validate='one_to_one', indicator=True)
assert joined._merge.eq('both').all()
np.testing.assert_allclose(joined.coin_in_usd, joined.machine_coin_in_usd,
                           rtol=0, atol=1e-6)
print('property / grouped-machine / joined rows:', len(prop), len(machine), len(joined))
print('on-floor machine-days:', machine.machine_rows.sum())
print('property / machine sums:', prop.coin_in_usd.sum(), machine.machine_coin_in_usd.sum())
print('max daily difference:', (joined.coin_in_usd - joined.machine_coin_in_usd).abs().max())
pd.testing.assert_frame_equal(
    prop, io.mart('property_day')[['gaming_date', 'coin_in_usd']].astype({'coin_in_usd': float})
)
forecast = build(con)
pd.testing.assert_frame_equal(forecast, io.mart('q7_forecast'))
print('holdout rows:', len(forecast))
print('full holdout MAE:', score_forecasts(forecast).to_dict())
for month, rows in forecast.groupby(forecast.gaming_date.dt.month):
    print('month / days / MAE:', month, len(rows), score_forecasts(rows).to_dict())
errors = score_forecasts(forecast)
print('weekday gain USD / %:', errors.constant - errors.weekday,
      100 * (1 - errors.weekday / errors.constant))
print('regression excess USD / %:', errors.weekday_trend - errors.weekday,
      100 * (errors.weekday_trend / errors.weekday - 1))
PY
```

Verification: `uv run pytest -q` passes **56 tests**, including **18 model/page tests**. Poisoned-holdout tests cover every method with NaN, infinity, negative extremes, and nonnumeric targets, and require exact equality with training-only fits. A known synthetic regression checks recovered coefficients and exact extrapolation. Streamlit AppTest checks full versus selected scores, individual month and weekday group errors, day-weighted reconciliation, an empty chart selection, and a one-day period; model fitting is patched to fail if the page attempts it. `git diff --check` passes.

Alternative explanation tested: adding a shared linear demand trend to weekday seasonality might improve extrapolation; it increases error here. Limitations: one fictional property, one contiguous holdout, retrospective method comparison, potentially correlated errors, and no formal prediction interval. The best observed method can change with events or demand shifts. MAE summarizes observed errors rather than bounding future errors, and no causal business benefit is established.
