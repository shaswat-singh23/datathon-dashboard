# Judge utility audit and self-contained evidence
- Issue: #81 | Author: sahith1021 (Codex) | Time: 16:57 America/Chicago, 2026-11-07
- Claim: The original dashboard met most analytical requirements but made the replacement decision and evidence harder to reach. A separate reviewer estimated 79/90 excluding originality; the estimate is a diagnostic rubric interpretation, not an actual judging result. This change addresses the Home decision/drill/Source gaps, exposes findings/appendix/disclosure inside all eight app routes, and quantifies the training-only weekday planning comparison.
- Evidence: Baseline `uv run pytest -q`: 56 passed. Full-window committed marts reproduce 8/10 surviving manager picks, a $1,200 inspection of M-1158 and $98,800 preserved. March 8 has 300 on-floor machines, 23 scheduled hours each (6,900 machine-hours), $1,805,102.85 coin-in, 6,861.8391667 available machine-hours and 99.44694444% availability. The new interaction tests verify these states without raw data; final verification is recorded below.
- So what: A judge can start at the manager's decision, change the evidence scope, inspect validation and read/download the supporting evidence without access to the private GitHub repository. Descriptive ranks and inspection leads do not establish a replacement benefit or wrongdoing.
- Checked by: independent Codex dashboard_judge agent, 2026-11-07 (AppTest, training-profile reconciliation and independent month-deletion reconstruction; not a human review)

## Reproduction

```bash
uv run pytest tests/test_dashboard_utility.py -q
uv run pytest -q
uv run streamlit run app.py
```

In Home, set Analysis period to March 8 alone and select a bank; historical KPIs and machine rows recalculate. Open Source and choose `docs/claims_evidence.md` or `docs/ai_disclosure.md`. Both display fully inside the app and download as Markdown. The same document picker exists on all seven analytical pages. The fixed July recommendation remains based on the full January–June record.

```python
from datetime import date
from royale import budget, io
from royale.marts.q1_machines import summarize
from royale.marts.q6_actions import proposed_plan
from royale.overview import period_totals, select_machine_days, weekday_profile

machines = io.mart('q1_machines')
ranks = summarize(machines)
manager = ranks.sort_values('raw_rank').head(10)
print('overlap', len(set(manager.index) & set(ranks.head(10).index)))
day = select_machine_days(machines, date(2025, 3, 8), date(2025, 3, 8))
print('machine-days', len(day), 'scheduled seconds', sorted(day.scheduled_seconds.unique()))
print('March 8', period_totals(day))
actions = io.mart('q6_actions')
catalog = actions[actions.record_type == 'catalog']
plan = proposed_plan(actions)
print('plan', plan, 'cost', budget.plan_cost_usd(catalog, plan), 'violations', budget.validate_plan(catalog, plan))
print(weekday_profile(io.mart('q7_forecast')).round(4))
```

Training weekday coin-in estimates are $1,112,941.95 on Tuesday (−19.6385% versus the constant) and $1,820,595.19 on Saturday (+31.4586%). The constant training mean is $1,384,919.05. These are frozen training estimates, not observed holdout averages or staff-hour requirements. Changing holdout outcomes leaves the displayed profile unchanged; the test also reconciles it independently to January–April in committed `property_day`.

To reproduce rank sensitivity:

```python
from royale.overview import rank_stability
print(rank_stability(machines, manager.index))
```

## Interpretation and limits

See [the audit](../docs/dashboard_audit.md) for category-by-category deductions, measurable acceptance targets and limitations. Existing checked findings #22, #23 and #47 remain the analytical sources. No raw data, marts, prices, model fit, dependency or deployment setting changed. In-app evidence retains each document's stated period, review status and limitations; it is not rewritten by page filters.

The follow-up rank-sensitivity check deletes each complete month in turn and reports descriptive ranges and bottom-ten counts. At the full-window selection, M-1179 ranks 9–11 and stays in the bottom ten in 5/6 runs; M-1158 ranks 68–82 and stays there in 0/6. The independent reviewer reconstructed all six deletions and four deletions in a January 15–June 15/B-01 selection, including partial-boundary behavior, and matched every displayed value. This addresses the last identified diagnostic deduction; the reviewer counts 90/90 checklist coverage, not a prediction of a perfect judge score. Runs overlap and do not quantify a calibrated probability, confidence interval or replacement effect. The separate public-code, video, final submission and deployed-QA obligations remain with their existing owners.

## Final verification

- `uv run pytest tests/test_dashboard_utility.py -q`: **22 passed**. Home plus all seven registered pages exercised period/drill changes and appendix/disclosure switching with raw-data reads forbidden; March 8 and zero exposure checked explicitly.
- `uv run pytest -q`: **78 passed** after integration, compared with **56 passed** before.
- A fresh Chromium context on the local Streamlit preview opened Source, selected and displayed the appendix, downloaded `claims_evidence.md`, followed the Home-to-Model link, and rendered the training planning profile; **zero browser errors**. Screenshots retained in `/tmp/dashboard-81-{home,evidence,model}.png` during this session.
- Independent reviewer reproduced full-window and partial-window/bank rank-sensitivity results and reconciled all seven weekday training means. No correctness blocker found.
- `git diff --check`: clean. These results describe the branch implementation; deployed-URL QA remains #70 after independent PR review and merge.
