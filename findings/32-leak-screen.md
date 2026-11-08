# One machine crosses the variance-adjusted payout inspection threshold
- Issue: #32 | Author: sahith1021 | Time: 14:15 America/Chicago
- Claim: For Jan 1–Jun 30, 2025, one of 310 active on-floor machines, M-1158, has configured RTP outside its approximate observed-payout interval at ±3.8 standard errors. It ranks second-lowest on the manager's raw house-win baseline. This is an inspection lead, not proof of a leak or wrongdoing.
- Evidence: `uv run python -m royale.build q1_leak`; `summarize(io.mart('q1_leak'))` and `volatility_check` in `royale/marts/q1_leak.py`. The stricter screen flags **1/310**, versus **24/310** for the simple per-machine |z| > 1.96 screen. Join checks preserve **55,092** active on-floor machine-days, **24,890,521,925** wager cents and **22,526,706,415** payout cents; **1,018** off-floor rows are excluded. Mart: 24 columns, **4,662,984 bytes**, below 5 MiB.
- So what: Inspect M-1158's payout meters, configuration history and service records before attributing its low house win to weak demand or recommending replacement. The screen does not estimate an intervention's benefit.
- Checked by: Alex (Claude Code, Opus 5.5), 2026-11-07 16:15

| Candidate | Paid spins | Observed RTP | Configured RTP | Interval lower | Interval upper | Payout z | Manager raw rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| M-1158 | 674,454 | 96.9600% | 90.0000% | 91.1729% | 102.7471% | +4.570146 | 2 |

Payout z has the opposite sign to the house-win luck z on the existing Machines page. M-1158's excess payout relative to configured expectation is $8.33 per available hour over this window. An interval upper endpoint above 100% is retained: a realized payout ratio can exceed 100%, and clipping would misrepresent the normal approximation.

## Method and baseline

- Compare the payout ratio to the supplied configured RTP, the no-deviation baseline. Both are ratios of sums: observed = SUM(payout) / SUM(coin-in); configured = 1 − SUM(theo) / SUM(coin-in). The configured comparator is wager-weighted if a machine changes games.
- Expected house win and payout z use `royale.money.theo`, `hold` and `luck_z`. All meters and variance calculations stay in cents until presentation.
- V = SUM(sum_bet_squared × payout_multiplier_variance). `sum_bet_squared` already sums over paid spins; do not multiply by spins again. RTP standard error = sqrt(V) / SUM(coin-in). The interval is observed RTP ± 3.8 standard errors, and the inspection rule is configured RTP outside that interval (equivalently |payout z| > 3.8).
- A two-sided standard-normal tail at 3.8, multiplied by 310 machines, gives a Bonferroni upper bound of **4.486%** for at least one false flag under the null assumptions. This is an approximate simultaneous inspection interval, not an ordinary per-machine 95% interval. The fixed threshold is retained for smaller bank selections.
- Daily intervals are included in the mart for diagnostics. The page recalculates all period statistics from summed daily meters and variances; it never averages daily RTPs, z scores or interval endpoints. No-play/zero-variance selections are not tested. Placement intervals determine each day's bank at gaming-day start.
- Manager rank uses the same selected period and bank as the existing raw-total-house-win baseline. The simple |z| > 1.96 screen is shown to make the cost of unadjusted multiple comparisons visible.

## Volatility check

| Volatility class | Tested machines | Candidates at 3.8 | Flag rate | Flags at 1.96 | Simple flag rate | Median RTP standard error |
|---|---:|---:|---:|---:|---:|---:|
| low | 80 | 0 | 0.000% | 3 | 3.750% | 0.225 percentage points |
| medium | 122 | 1 | 0.820% | 11 | 9.016% | 0.839 percentage points |
| high | 90 | 0 | 0.000% | 8 | 8.889% | 1.389 percentage points |
| very_high | 18 | 0 | 0.000% | 2 | 11.111% | 2.888 percentage points |

The stricter screen does not disproportionately flag high/very-high classes in this window: both have zero candidates. Their larger typical uncertainty is allowed for explicitly. These descriptive rates do **not** prove equal false-positive rates: class sizes, bets, exposure, game distributions and possible configuration/meter issues differ. In particular, only 18 machines are very-high volatility. Mixed-class machines would be labeled `mixed`; none change configuration in this release.

## Unexpected result

Expected: with 310 machines and a simple per-machine |z| > 1.96 screen, about 5% (~15) would flag by chance, mostly noise. Found: the simple screen flags 24/310 (7.7%), but the variance-adjusted ±3.8 screen leaves exactly one, M-1158, at payout z +4.570 (observed RTP 96.96% vs configured 90.00%). It is also the manager's second-lowest raw house-win machine. The baseline is the simple screen; the surprise is that one low performer stands out far beyond what luck among 310 machines explains. This remains an inspection lead, not a finding of wrongdoing. To reproduce, follow the Reproduce section below.

## Reproduce

Build the mart, run the suite, then run this independent raw-data comparison:

```bash
uv run python -m royale.build q1_leak
uv run pytest -q
```

```python
import numpy as np
from royale import io
from royale.marts.q1_leak import summarize, volatility_check
from royale.marts.q1_machines import summarize as rank

r = summarize(io.mart('q1_leak')).sort_index()
raw = io.sql('''
SELECT m.machine_id,
  SUM(m.payout_cents) / SUM(m.coin_in_cents) AS observed,
  SUM(m.coin_in_cents * g.configured_rtp) / SUM(m.coin_in_cents) AS configured,
  (SUM(m.payout_cents) - SUM(m.coin_in_cents * g.configured_rtp)) /
    SQRT(SUM(m.sum_bet_squared * g.payout_multiplier_variance)) AS z,
  SQRT(SUM(m.sum_bet_squared * g.payout_multiplier_variance)) /
    SUM(m.coin_in_cents) AS se
FROM machine_day m JOIN game_math g USING (config_id)
WHERE m.active AND m.location_id IS NOT NULL
GROUP BY m.machine_id ORDER BY m.machine_id
''').set_index('machine_id')
for column, source in [('observed_rtp', 'observed'), ('configured_rtp', 'configured'),
                       ('payout_z', 'z'), ('rtp_se', 'se')]:
    np.testing.assert_allclose(r[column], raw[source], rtol=1e-10, atol=1e-9)
np.testing.assert_allclose(r.ci_lower, raw.observed - 3.8 * raw.se)
np.testing.assert_allclose(r.ci_upper, raw.observed + 3.8 * raw.se)
np.testing.assert_array_equal(r.inspection_candidate, abs(raw.z) > 3.8)
np.testing.assert_allclose(r.payout_z, -rank(io.mart('q1_machines')).luck_z.reindex(r.index))
assert r[r.inspection_candidate].index.tolist() == ['M-1158']
print(r[r.inspection_candidate])
print(volatility_check(r))
```

Page verification without raw-data access:

```python
from datetime import date
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from royale import io

with patch.object(io, 'connect', side_effect=AssertionError('raw access')):
    app = AppTest.from_file(str(Path('pages/1_machines.py').resolve()), default_timeout=30).run()
    assert not app.exception
    assert next(m.value for m in app.metric if m.label == 'Payout inspection candidates') == '1 / 310 tested'
    app.slider[0].set_value((date(2025, 1, 1), date(2025, 1, 31))).run()
    assert not app.exception
    app.selectbox[0].select(app.selectbox[0].options[1]).run()
    assert not app.exception
    app.slider[0].set_value((date(2025, 3, 8), date(2025, 3, 8))).run()
    assert not app.exception
```

## Verification and limitations

- Build assertions check row counts before/after joins, unique machine-date keys, unchanged wager/payout sums, placement agreement, valid game variance and consistent payout/house-win meters.
- Independent raw SQL reconciles all 310 machines' days, spins, wagers, payouts, weighted configured RTP, observed RTP, z scores, standard errors and endpoints. Payout z also reconciles to the negative of the existing machine-ranking z.
- A temporary synthetic harness checks unequal wager weights, mixed configurations, summed variance, payout sign, cents scaling, zero play and zero variance. Streamlit AppTest passes for the full window, January, a bank drill and a March 8 single-day selection, with raw-data access disabled. Selected candidate counts and class tables agree with direct recomputation. `uv run pytest -q`: **45 passed**.
- Independent spins, correct configuration metadata and supplied payout variance are assumptions. Heavy tails and short windows can invalidate the normal approximation. Repeated period/bank searches invalidate the quoted familywise error interpretation. This screen does not establish wrongdoing or a persistent payout defect; meter reconciliation, configuration history and maintenance investigation are alternative explanations to inspect.
- Findings require independent review before being marked checked or reused as confirmed claims.
