# Inspect one payout configuration; preserve $98,800
- Issue: #23 | Author: sahith1021 (with Codex) | Time: 13:50 America/Chicago
- Claim: Fund one `A-INSPECT` for M-1158 at **$1,200** and preserve **$98,800** of the July 1–30 budget. This buys information, with no positive revenue recovery estimated. Monetary scenarios alone favor preserving the full budget. Neither manufacturer maintenance nor an extra grave technician covers its price under the historical recovery scenarios below.
- Evidence: `uv run python -m royale.build q6_actions`, then `proposed_plan` and `assess` in `royale/marts/q6_actions.py`. `validate_plan` returns **[]**. One action type, quantity 1 (limit 15), one-day lead, two-hour inspection downtime; execute July 2. Mart: **56,314 rows**, **1,720,777 bytes** (under 5 MB).
- So what: Investigate a specific payout/configuration question before committing to new titles. The historical ranking supplies no causal replacement-demand estimate; spending the full budget is not an objective.
- Checked by: unchecked

## Evidence and baseline

The manager baseline is the ten lowest summed house-win machines on active on-floor days, Jan 1–Jun 30. In order: M-5076, M-1158, M-1120, M-1118, M-1238, M-1181, M-1035, M-1179, M-1017, M-1265. Leasing all ten costs **$33,800** (16 operating days); buying them costs **$220,000**, over budget. Both prices use `royale.budget`, and neither has a demonstrated replacement uplift.

Of the manager picks still on the floor June 30, only M-1158 passes the existing Q1 screen, z < −3.8. Its full-period z is **−4.57015**, raw rank 2, with **$51,961.00** theo, **$15,796.25** actual house win and **4,339.9853** available hours across 181 days. This is an inspection lead, not evidence of wrongdoing or a confirmed faulty paytable. Historical residuals are not future recoverable cash. See [Q1 finding](22-machines.md) and [Machines page](../pages/1_machines.py).

The decision baseline is preserve all $100,000: zero incremental spend and zero incremental theo. The recommendation deliberately spends $1,200 for a documented configuration check; its information value is not monetized. Two hours at M-1158's ratio-of-sums theo/hour imply **$23.95** displaced theo. Operational low/high scenarios are **−$35.12 / $0**, using two hours at its 90th-percentile historical daily theo/hour / no displacement. These do not bound any later benefit from correcting a configuration, which is unknown.

## Priced alternatives and sensitivity

Amounts are incremental theo versus no action, after implementation downtime, before direct spend. They are decision scenarios, **not fitted intervention effects or confidence intervals**. Base recovery is an assumed 50% of historical lost theo/waiting; low/high recovery is 0%/100%. Halving changes 50% to 25%, retaining fixed spend and downtime.

| Option | Targets / quantity | Cost | Theo low | Theo base | Theo high | Base theo less spend | Halved recovery less spend | Rank base → half |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Preserve all | Full budget | $0 | $0 | $0 | $0 | $0 | $0 | 1 → 1 |
| Inspect (funded) | M-1158 / 1 | $1,200 | −$35.12 | −$23.95 | $0 | −$1,223.95 | −$1,223.95 | 2 → 2 |
| Preventive sweep (defer) | Ridgeline / 1 manufacturer | $9,000 | −$2,417.35 | $676.47 | $3,770.30 | −$8,323.53 | −$9,870.44 | 3 → 3 |
| Extra technician (defer) | Grave 22:00–06:00 / 1 shift | $11,520 | $0 | $647.38 | $1,294.75 | −$10,872.62 | −$11,196.31 | 4 → 4 |

- Preventive: Ridgeline has the highest historical lost share of scheduled hours (see [Q3 finding](17-downtime.md), [Downtime page](../pages/3_downtime.py)). Use the **92 machines on the floor June 30**, excluding retired machines from July's footprint. For each target, selected-period lost hours / observed on-floor days × its theo per available hour, summed and projected across **23 operating days** after the seven-day lead. This gives **$6,187.66** at 100% recovery, before **$2,417.35** implementation displacement (90 minutes per machine). All downtime, including non-fault outages, is generously considered recoverable. Even this high case nets **−$5,229.70** after the package price. Manufacturer/game/location differences can explain historical fault rates; no measured maintenance efficacy is claimed.
- Technician: **303** grave faults waited **1.9627 h** on average versus **0.8663 h** for other shifts. Sum each grave fault's wait × that machine's theo/available hour; divide by **181 calendar days**, multiply by **23 operating days**. Eliminating all such waiting gives **$1,294.75**, or **−$10,225.25** after cost. Repair time remains. Severity and shift demand can confound the staffing comparison. Other operating benefits or labor savings are unpriced.
- Halving the assumed recovery leaves the full-period ranking unchanged. The inspection has no positive recovery to halve; its cost and downtime remain. The period slider recalculates the evidence and ranks, while targets and July plan stay fixed using the complete Jan–Jun history.

## Measurement plans

| Action | Metric | Comparison | Duration / decision |
|---|---|---|---|
| Funded inspection | Documented paytable/meter match to configured RTP; availability and variance-standardized payout residual as monitoring | Uninspected machines on the same configuration and June pre-period | Verify July 2; monitor July 2–30. Record pass/fail; any correction needs a separate decision and benefit estimate. Regression to the mean is not an effect. |
| Maintenance, if reconsidered | Faults per 1,000 scheduled hours; theo per scheduled hour | Randomized service order within same-title/bank blocks; not-yet-serviced controls | July 8–30. Seek a fault-rate reduction and property benefit, accounting for sweep downtime. |
| Technician, if reconsidered | Wait hours per fault, downtime per scheduled hour, property theo | Randomized covered vs uncovered grave shifts, blocked by weekday | July 8–30. Re-estimate benefit before expansion. |
| Preserve funds | Continue availability and payout monitoring | Existing June process | Through July 30; reconsider only with actionable inspection or controlled-pilot evidence. |

## Reproduce

```bash
uv run python -m royale.build q6_actions
uv run pytest -q
```

```python
from royale import io, budget
from royale.marts.q6_actions import assess, proposed_plan
d = io.mart('q6_actions')
c = d[d.record_type == 'catalog']
p = proposed_plan(d)
assert budget.validate_plan(c, p) == []
assert budget.plan_cost_usd(c, p) == 1200
options, evidence = assess(d)  # pass start/end to reproduce evidence-period changes
print(p)
print(options.round(2).to_string(index=False))
print(evidence['machines'].loc[evidence['inspection_targets']])
```

Independent raw SQL reconciled the manager order and the target's z/opportunity cost, using supplied `machine_day.theo_cents` rather than Q6's calculated theo:

```sql
SELECT machine_id, SUM(house_win_cents) AS win
FROM machine_day WHERE active AND location_id IS NOT NULL
GROUP BY 1 ORDER BY win, machine_id LIMIT 10;

SELECT (SUM(house_win_cents)-SUM(m.theo_cents))
         / SQRT(SUM(m.sum_bet_squared*g.payout_multiplier_variance)) AS z,
       2*SUM(m.theo_cents)/100.0/(SUM(available_seconds)/3600.0) AS displaced_theo
FROM machine_day m JOIN game_math g USING(config_id)
WHERE machine_id='M-1158' AND active AND location_id IS NOT NULL;
```

Independent maintenance check (run with `io.sql`):

```sql
WITH target AS (
  SELECT machine_id FROM machine_day JOIN machines USING(machine_id)
  WHERE gaming_date=(SELECT MAX(gaming_date) FROM machine_day)
    AND active AND location_id IS NOT NULL AND manufacturer='Ridgeline'
), per_machine AS (
  SELECT machine_id, COUNT(*) AS observed_days,
         SUM((c.scheduled_seconds-m.available_seconds)/3600.0) AS lost_h,
         SUM(m.theo_cents)/100.0/(SUM(m.available_seconds)/3600.0) AS rate
  FROM machine_day m JOIN target USING(machine_id)
  JOIN calendar_day c USING(gaming_date)
  WHERE active AND location_id IS NOT NULL GROUP BY 1
)
SELECT COUNT(*) AS machines, SUM(lost_h/observed_days*rate)*23 AS recovery,
       SUM(rate)*1.5 AS displacement FROM per_machine;
```

Independent technician check:

```sql
WITH rate AS (
  SELECT machine_id, SUM(theo_cents)/100.0/(SUM(available_seconds)/3600.0) AS theo_per_h
  FROM machine_day WHERE active AND location_id IS NOT NULL GROUP BY 1
)
SELECT SUM(epoch(work_started_at_utc-opened_at_utc)/3600.0*theo_per_h)/181*23 AS recovery
FROM operations JOIN rate USING(machine_id)
WHERE event_type='fault_repair'
  AND (hour(opened_at_local)>=22 OR hour(opened_at_local)<6);
```

## Verification and limits

- Mart joins preserve **55,092** active on-floor machine-days and all **1,226** operation rows before selecting **1,207** faults. **1,018** null-location machine-days are excluded. Placement at gaming-day start is reused from Q1; machines move. Scheduled hours come from `calendar_day`, including the 23-hour March 8. Catalogue contributes 13 rows; two audit rows record join counts.
- `uv run pytest -q`: **45 passed**. Independent raw SQL matches scenario components, manager baseline and z. All catalogue unit prices reconcile to the guide formula; proposed and alternative plans pass budget validation. Single-day January 1, single-day March 8, June, and a synthetic zero-signal preserve-all fallback were checked.
- Streamlit AppTest starts at `app.py`, switches to `pages/6_actions.py`, and renders all four action drills across full-period, June and single-day selections without exceptions. Raw IO methods were replaced with functions that raise, and DATA_DIR was set to a nonexistent path: the page uses committed marts only. Cost and remaining budget remain $1,200 / $98,800 throughout.
- Reproduce the UI check from the repo root with `AppTest.from_file('app.py').run().switch_page('pages/6_actions.py').run()`; the main entrypoint is needed to register internal page links.
- Net is incremental theo less action spend and implementation displacement, not full profit. Taxes, lease-share changes, demand substitution, future demand shifts, repair-cost savings and information value are excluded. No new comp spending is proposed. Operating-benefit scenarios may fail if July differs or service does not work; they are not statistical bounds on all possible benefits.
- Short periods are noisy; missing available-hour rates are omitted and flagged as incomplete. Payout z assumes independent spins and configured game variance. Repeated filter searches weaken its approximate error calibration. Source findings and this recommendation need independent review before presentation as checked evidence.
