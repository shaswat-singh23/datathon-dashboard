# Loyalty cost and redemption intensity, January–June 2025
- Issue: #19 | Author: sahith1021 | Time: 12:57 America/Chicago
- Claim: Tracked guests redeemed comps costing $190,669.30, with $682,749.50 of menu value. Cost / tracked theo was 1.2313%. Monthly tracked comp costs reconcile to property costs to the cent. Points redeemed per comp menu dollar fell from 13.0852 in January–April to 5.7788 in May–June (55.84% lower).
- Evidence: `uv run python -m royale.build q5_comps` builds 42 rows (36 month × opening-tier × region groups plus 6 property-month rows), 8,191 bytes. Aggregation preserves 148,893 player-month input rows and 181 property-day input rows, recorded in source_rows. No raw-table joins; the reconciliation joins six monthly totals to six monthly totals one-to-one. Raw and mart cost, menu-value and theo sums agree within $0.000001. Largest monthly cost reconciliation difference before rounding: $0.000000000008.
- So what: Budget comps using economic cost, not menu value. May marks a descriptive break in redemption intensity while economic reinvestment increases; inspect program and accounting definitions before calling this a policy effect.
- Checked by: unchecked

## Reproduce
Set DATA_DIR to the organizer data directory, then run `uv run python -m royale.build q5_comps`. In `uv run python`, run:

```python
from royale import io, money
m = io.mart('q5_comps')
t = m[m.population.eq('tracked')]
p = m[m.population.eq('property')]
print(t[['comp_cost_usd', 'comp_face_value_usd', 'theo_usd']].sum())
print(money.comp_reinvestment(t.comp_cost_usd, t.theo_usd))
a = t.groupby('month').sum(numeric_only=True)
b = p.set_index('month')
print(a[['comp_cost_usd', 'points_earned', 'points_redeemed']])
print(a.comp_cost_usd - b.comp_cost_usd)
for frame in [a.loc[:'2025-04'], a.loc['2025-05':]]:
    print(frame.points_redeemed.sum() / frame.comp_face_value_usd.sum())
    print(money.comp_reinvestment(frame.comp_cost_usd, frame.theo_usd))
print(t.source_rows.sum(), p.source_rows.sum())
```

Underlying query for the change comparison:

```sql
SELECT CASE WHEN period_month < '2025-05' THEN 'Jan-Apr' ELSE 'May-Jun' END AS period,
       SUM(points_redeemed) / SUM(comp_face_value_usd) AS points_per_menu_dollar,
       SUM(comp_cost_usd) / SUM(theo_usd) AS reinvestment
FROM player_period GROUP BY 1 ORDER BY 1;
```

## Baseline and alternatives
The simple baseline is constant January–April points redeemed per menu dollar (13.0852). May–June's observed 5.7788 is below this volume-adjusted baseline. Monthly points redeemed were 1,433,623; 1,411,208; 1,531,314; 1,404,060; 719,172; and 673,602. Reinvestment was 1.1940% for January–April versus 1.3060% for May–June. Comp menu value remains substantial after April, so fewer comp menu dollars alone do not explain the points break. The dashboard also offers a first-selected-month constant-intensity baseline for interactive windows.

This is descriptive, with no statistical change-point or causal identification. Guest composition, comp item mix, points conversion rules, redemption timing and accounting changes remain possible explanations. Monthly aggregates cannot identify the precise change date or establish a program rule change. No confidence interval is claimed. Tracked theo is carded only; property theo includes all play, so their reinvestment ratios answer different questions. Comp costs are already in POS cogs and are never subtracted again. Points earned are not a cash liability estimate.

## Verification
- `uv run pytest -q`: 38 passed.
- Streamlit AppTest: default page, May–June period, and combined opening-tier/home-region drill render without exceptions.
- Rebuilt mart equals committed mart; independent raw cost, menu-value and theo sums reconcile; source row counts preserved. Mart under 5 MB.
- Findings require independent human review before being used as a checked claim or merged by the decider.
