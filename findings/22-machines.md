# Eight manager picks remain in the adjusted bottom ten
- Issue: #22 | Author: sahith1021 | Time: 13:24 America/Chicago
- Claim: Over Jan 1–Jun 30 2025, 8 of the manager's 10 lowest-house-win machines also rank in the bottom 10 by expected contribution per available hour. This is descriptive screening, not evidence that replacement will help.
- Evidence: `uv run python -m royale.build q1_machines`; then `summarize(io.mart('q1_machines'))` from `royale.marts.q1_machines`. Manager rank is ascending SUM(house_win_cents) over active on-floor rows; adjusted rank is ascending (SUM(theo_cents)/100 - SUM(supplied_cost_usd)) / (SUM(available_seconds)/3600). Both break ties by machine ID. Intersection of each rank <= 10 yields **8**. Mart: 55,092 rows, 18 columns, 1.65 MB; 1,018 off-floor rows excluded.
- So what: Raw totals and exposure/luck-adjusted economics disagree on two replacement candidates. Inspect the mechanisms before spending the replacement budget.
- Checked by: Alex (Claude Code, Opus 5.5), 2026-11-07 16:15

| Manager pick | House win USD | Adjusted rank | Luck z | Triage |
|---|---:|---:|---:|---|
| M-5076 | 3,573.25 | 2 | -1.853 | weak |
| M-1158 | 15,796.25 | 74 | -4.570 | leak-candidate |
| M-1120 | 16,355.00 | 1 | -0.788 | weak |
| M-1118 | 20,050.00 | 111 | -0.649 | luck/exposure |
| M-1238 | 24,932.75 | 5 | -1.815 | weak |
| M-1181 | 26,977.00 | 7 | -2.406 | luck |
| M-1035 | 30,303.50 | 4 | -0.136 | weak |
| M-1179 | 30,393.75 | 10 | -1.455 | weak |
| M-1017 | 31,939.50 | 3 | 0.578 | weak |
| M-1265 | 32,071.00 | 6 | -0.060 | weak |

Adjusted bottom ten, in order: M-1120, M-5076, M-1017, M-1035, M-1238, M-1265, M-1181, M-1053, M-1270, M-1179.

## Reproduce

```python
from royale import io
from royale.marts.q1_machines import summarize
r = summarize(io.mart('q1_machines'))
manager = r.sort_values('raw_rank').head(10)
adjusted = r.head(10)
print(len(set(manager.index) & set(adjusted.index)))  # 8
print(manager[['house_win', 'adjusted_rank', 'luck_z', 'triage']])
```

Independent baseline query (raw DATA_DIR, not the mart):

```sql
SELECT machine_id, SUM(house_win_cents)/100.0 AS house_win
FROM machine_day WHERE active AND location_id IS NOT NULL
GROUP BY machine_id ORDER BY house_win, machine_id LIMIT 10;
```

## Alternative explanations and limitations

- Exposure: active days and available hours are shown explicitly. M-1118 leaves the bottom ten without a large negative z; the combined luck/exposure label must not be interpreted as statistically unusual luck.
- Luck: z uses summed squared bets × configured payout variance in cents squared. M-1158's -4.570 is a lead for configuration/payout inspection, not proof of wrongdoing. A -3.8 threshold roughly screens 310 machines at one-sided 5% familywise error under normal independent-spin assumptions; heavy tails and repeated filters weaken that interpretation.
- Location: a heuristic flag requires below-floor zone peers and a machine meeting its zone peer expected contribution rate. Peers exclude the subject and rates are weighted by its hours across visited zones. No manager pick meets this rule for the full window. Game mix, costs and demand confound this comparison, so this does not rule out location effects.
- Weak: remaining bottom-ten picks without preceding signals merit investigation, not automatic replacement. No causal replacement benefit or confidence interval for future machine demand is estimated.
- Supplied costs are prepared-view lease, service, power and repair costs, counted once. Shared labor and nongaming economics are excluded. Theo replaces realized win but realized revenue-share lease costs still depend on daily payout luck.
- Period and bank drills recalculate all ranks and zone benchmarks within the selection; they do not preserve the floor-wide manager list. Short periods have higher noise.

## Verification

- Build asserts row-count preservation and unique machine-date keys; placements at gaming-day start agree with machine_day location. Calendar hours correctly give March 8 23 hours.
- Independent raw SQL reproduces the ordered manager list; summed house win and theo reconcile to active machine_day totals. Every machine's z reconciles to an independent variance formula.
- Streamlit AppTest checks the default page and single-day bank drill. `uv run pytest -q`: 45 passed.
- Review required: findings remain unchecked until another person reviews them.
