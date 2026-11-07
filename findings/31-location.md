# Seven manager picks have a descriptive location association
- Issue: #31 | Author: sahith1021 | Time: 14:05 America/Chicago
- Claim: For Jan 1–Jun 30, **7 of the manager's bottom 10** meet the location screen below, all in Back Forty. Nine picks sit in Back Forty; one is in High-Limit Room. These are associations, not a causal count of machines whose poor earnings are explained by location. Requiring 95% rather than 90% of local peer demand reduces the screen count to **5**; requiring 100% reduces it to **3**.
- Evidence: `uv run python -m royale.build q1_location`, followed by the reproduction block below. The mart has **2,446 rows**, **18 columns**, **82,009 bytes**. The manager baseline is ascending total house win over active, on-floor machine-days, with machine ID breaking ties. Rates use ratios of sums via `royale.money`.
- So what: A replacement-only decision overlooks a low-demand, low-traffic location shared by several picks. A measured location experiment merits consideration before attributing low earnings to the machine. This analysis supplies no relocation benefit or priced action.
- Checked by: Kyle (Claude Code, Fable 5.1), 2026-11-07 17:05

## Comparison and uncertainty

For each subject segment, match configuration (therefore title) and calendar month. Remove that machine from **every** peer zone, including its other placements. Compare other same-title machines in its zone against same-title machines in other zones. Weight both expected rates by the subject's available hours, so moves and unequal exposure are retained. Other-zone traffic is weighted by matching peer machine-hours; local traffic is the subject zone's entries per observed counter hour. Traffic describes the full zone, not individual players or a machine's footfall.

Screen rule, chosen as a descriptive heuristic: at least 80% of available hours have usable local/other-zone peers, at least three matched months, both local-vs-other demand and traffic gaps have negative upper 95% bootstrap bounds, and the subject achieves at least 90% of its local same-title peer demand. The 90% tolerance is not an equivalence test. Resample calendar months jointly for both sides, 2,000 draws, seed 31; use percentile 95% bounds. Fewer than three months gives no interval or positive screen.

Demand gap = local same-title peer coin-in/hour divided by other-zone same-title peer coin-in/hour minus one. All nine matched subjects have 100% matched available-hour coverage; the High-Limit title has no cross-zone match.

| Manager pick | Matched months | Own $/available h | Local peer $/h | Other-zone peer $/h | Local demand gap, 95% interval | Own/local | Screen |
|---|---:|---:|---:|---:|---|---:|---|
| M-5076 | 2 | 127.84 | 144.39 | 206.30 | −30.0%; insufficient months | 88.5% | No |
| M-1158 | 6 | 119.73 | 110.06 | 182.74 | −39.8% [−46.6%, −35.1%] | 108.8% | Yes |
| M-1120 | 5 | 120.06 | 143.55 | 216.12 | −33.6% [−40.7%, −27.9%] | 83.6% | No |
| M-1118 | 0 | — | — | — | No same-title cross-zone comparison | — | Unknown |
| M-1238 | 6 | 153.00 | 133.62 | 213.47 | −37.4% [−43.7%, −32.8%] | 114.5% | Yes |
| M-1181 | 6 | 93.79 | 99.79 | 165.09 | −39.6% [−44.7%, −35.7%] | 94.0% | Yes |
| M-1035 | 6 | 142.39 | 137.22 | 213.45 | −35.7% [−42.1%, −31.1%] | 103.8% | Yes |
| M-1179 | 6 | 97.64 | 98.50 | 165.09 | −40.3% [−45.6%, −36.6%] | 99.1% | Yes |
| M-1017 | 6 | 136.29 | 139.19 | 213.46 | −34.8% [−40.3%, −31.1%] | 97.9% | Yes |
| M-1265 | 6 | 92.88 | 100.11 | 165.09 | −39.4% [−44.9%, −35.9%] | 92.8% | Yes |

For the seven positive screens, matched local traffic gaps range from **−82.8% to −82.1%**. Every traffic interval's upper bound is below zero (individual bounds are returned by `assess`). These percentages compare sensor crossings in zones occupied by the same title, not unique visitors or machine-level demand conversion.

## Walkway context and baseline

W-ENT-B40 connects Main Entrance and Back Forty. It was closed from `2025-03-03 14:00 UTC` to `2025-04-07 13:00 UTC`. Overlapping gaming dates are March 3–April 6 inclusive, **35 days**. Before/during/after groups use UTC gaming-day boundaries; reopening is April 7.

| Back Forty period | All-title coin-in/available h | Entries/coverage h |
|---|---:|---:|
| Before closure | $134.55 | 25.19 |
| During closure | $96.25 | 17.62 |
| After reopening | $124.14 | 22.77 |

Against the simple before-closure baseline, Back Forty demand falls **28.5%** and traffic falls **30.0%** during closure. Holding title fixed gives the same directional pattern for all eight Back Forty titles: declines between **23.6% and 32.6%**. For example, Royal Draw is $149.56/h before, $111.19/h during, and $141.77/h after. The page exposes each title across zones and banks, plus phase traffic for other zones as context. These are unadjusted before/after associations, with no causal closure estimate or future-effect interval.

## Reconciliation and checks

- Raw active/on-floor machine-days before joins: **55,092**. Daily placement joins preserve that count and unique machine/date keys; monthly/phase aggregation sums back to **55,092**. **1,018** off-floor rows are excluded.
- Raw and aggregated totals agree exactly: **24,890,521,925 cents** coin-in; **2,363,815,510 cents** house win; **4,740,792,916 available seconds**; **4,758,868,800 scheduled seconds** from `calendar_day`. March 8 uses its 23-hour gaming day.
- Traffic is aggregated once from sensor-hours, then repeated as zone context on machine rows. Deduplicating month/zone/phase before summing recovers **2,653,848 entries** and **30,214.95 coverage hours**, matching independent raw aggregation. Offline counts and their coverage are excluded; they are not zero entries. Duplicating machine rows leaves the deduplicated traffic result unchanged.
- Independent raw SQL reproduces the ordered manager list and every machine/month/zone/bank/configuration coin-in rate. Independent leave-one-out calculations reproduce M-1158's local and other-zone rates. Synthetic moved-machine checks exclude its other-zone segment from peers even on a bank drill; missing peers and zero hours return no signal rather than dividing by zero.
- Streamlit AppTest loads the default page (7/10), changes game to Royal Draw, drills a Back Forty bank, narrows to March–April (no three-month interval), selects March 8 alone (complete-month notice), and selects February alone without a closure phase. No exceptions. Pages read committed marts only.
- `uv run pytest -q`: **45 passed**. `git diff --check` passes. Findings remain unchecked pending independent review.

## Reproduce

Build the mart, run the suite, then run this from the repository root. It reproduces the result, baseline, joins/totals, traffic deduplication, closure comparison and default page check:

```bash
uv run python -m royale.build q1_location
uv run pytest -q
uv run python - <<'PY'
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from royale import io
from royale.marts import q1_location as q

d = io.mart('q1_location')
assert len(d) == 2446 and not d.duplicated(q.KEY).any()
ids = d.groupby('machine_id').house_win_cents.sum().sort_index().sort_values(kind='stable').head(10).index
raw_ids = io.sql('''SELECT machine_id FROM machine_day
  WHERE active AND location_id IS NOT NULL GROUP BY machine_id
  ORDER BY sum(house_win_cents), machine_id LIMIT 10''').machine_id.tolist()
assert list(ids) == raw_ids
r = q.assess(d, ids)
print(r.round(5).to_string())
assert r.location_signal.sum() == 7
for threshold in [.9, .95, 1.0]:
    print('Own/local threshold', threshold,
          'candidates', int((r.location_signal & (r.own_vs_local >= threshold)).sum()))

cols = ['machine_days', 'coin_in_cents', 'house_win_cents', 'available_seconds', 'scheduled_seconds']
raw = io.sql('''SELECT count(*) AS machine_days, sum(m.coin_in_cents) AS coin_in_cents,
  sum(m.house_win_cents) AS house_win_cents, sum(m.available_seconds) AS available_seconds,
  sum(c.scheduled_seconds) AS scheduled_seconds FROM machine_day m
  JOIN calendar_day c USING(gaming_date) WHERE active AND location_id IS NOT NULL''')
assert np.array_equal(d[cols].sum().to_numpy(), raw[cols].iloc[0].to_numpy())
t = q.traffic_rates(d, ['zone_id', 'phase'])
assert t.equals(q.traffic_rates(pd.concat([d, d]), ['zone_id', 'phase']))
assert np.isclose(t.zone_entries.sum(), 2653848)
assert np.isclose(t.coverage_hours.sum(), 30214.95)
print(q.rates(d[d.zone_id == 'Z-B40'], ['phase'])[['phase', 'coin_in_per_available_hour']])
print(t[t.zone_id == 'Z-B40'])
assert q.complete_months(d, '2025-03-08', '2025-03-08').empty
assert pd.isna(r.loc['M-5076', 'demand_low'])
assert r.loc['M-1118', 'matched_months'] == 0
a = AppTest.from_file('pages/1_machines.py').run(timeout=30)
assert not a.exception and next(m.value for m in a.metric if m.label == 'Manager picks with a location association') == '7 / 10'
PY
```

## Alternatives and limitations

- Month and title matching remove coarse seasonality and title mix, but leave bet-size preferences, events, bank visibility, guest mix, persistent machine differences, and placement selection. No machine is randomized across zones. Location association does not prove that moving or replacing a machine changes demand.
- With only six calendar-month clusters, bootstrap bounds are exploratory and sensitive to the exchangeability assumption. They do not capture all serial dependence, placement confounding, or uncertainty in the selected 90% local-peer threshold. There is no multiple-search correction. The candidate-count sensitivity is part of the result, not a confidence interval for a causal count.
- M-1120 and M-5076 can share a quiet zone while still underperforming local peers; M-5076 also lacks enough months for an interval. M-1118's Platinum Reels title is confined to High-Limit, so this test cannot distinguish its title from location. Zero matches do not establish the absence of a location effect.
- M-1158 already has a payout-inspection flag in #22. Location, luck, availability, and payout behavior can coexist; these screens are not mutually exclusive and are not accusations.
- The previous #22 heuristic found no location flags because it compares expected contribution against zone peers with a different rule. This follow-up matches title/month, tests demand plus traffic, and allows a 10% local-peer tolerance. Its seven associations do not revise the earlier arithmetic or imply seven proven causes.
- Closure rates have a before-period baseline but no randomized control or causal counterfactual. Reopening coincides with other calendar changes. Zone crossings can reflect routing and repeat crossings; a quiet zone is not equivalent to a small number of unique guests.
- The location section uses **complete calendar months inside the page filter**, explicitly labeled. Other machine rankings still use the exact selected days. Bank selection restricts candidate earnings/exposure to that bank; peer pools remain floor-wide, with the subject excluded everywhere. Zone traffic is whole-zone, full-month context, including when a subject was present for only part of a month.
