# Dashboard judging audit: utility and measurable evidence

Issue [#81](https://github.com/shaswat-singh23/datathon-dashboard/issues/81). Independent reviewer: a separate Codex agent, before implementation and again afterward. Rubric: organizer `GUIDE.md`, sections 7–8, available in the verified organizer clone at `DATA_DIR/../GUIDE.md`; also summarized in `AGENTS.md`. Originality's 10 points are excluded, leaving **90 possible points**.

These are diagnostic estimates, not actual judge feedback. The organizer supplies category weights, not a point allocation for individual interface defects. A passing check demonstrates behavior; it does not prove a judge will award a particular number of points.

| Criterion | Before estimate | Reason for estimated deduction | Improvement |
|---|---:|---|---|
| Analytical validity | 29/30 | Expected-contribution ranks had no quantified stability check. | Add complete-month deletion sensitivity: rank ranges, bottom-ten counts and testable-run counts, with explicit nonindependence and exposure caveats. |
| Dashboard and communication | 16/25 | Home omitted the replacement decision (−3), bank drill (−1), and Source (−1). Findings and appendix links required private GitHub access (−4). | Home leads with a bounded decision, recalculates historical metrics and ranks by day/bank, links to the relevant pages, and embeds evidence documents in Source on every page. |
| Modeling and validation | 19/20 | The link from forecast to an operating decision lacked a numeric planning profile (−1). | Show frozen January–April weekday means versus constant demand and describe a prospective staffing allocation trial with a predeclared success target. |
| Recommendations and tradeoffs | 15/15 | No demonstrated defect: cost, budget limits, alternatives, sensitivity, uncertainty, and measurement are present. | Surface the existing decision on Home and retain its fixed historical basis. |
| **Total excluding originality** | **79/90** | **11 estimated points of headroom; all identified deductions addressed.** | **Independent re-review: 90/90 checklist coverage. This is not a prediction of a perfect judge score.** |

The fitted regression losing to the weekday baseline is **not** a deduction. The guide explicitly permits a model that does not beat its baseline; the dashboard reports that result and keeps frozen, time-based validation.

## Observable targets and results

| Target | Before | After / verification |
|---|---|---|
| A manager finds a replacement decision on Home | Property KPIs and a list of questions; no decision | Home explains why to defer blanket replacement and identifies the catalogue-priced inspection; direct links open Machines, Actions, and Model. |
| Home supports the promised judge controls | Period only; zero bank drills and zero Source expanders | Daily period slider, bank drill, Source, recomputed dollars/exposure/ranks; `test_home_changes_dollars_and_rank_scope_with_bank_and_period`. |
| Period and bank describe the same historical population | Home offered property-level totals only | All Home historical KPIs/chart/ranks use the selected active on-floor machine-days. Other pages have independent filters, explicitly stated. |
| March 8 uses 23 scheduled hours | Not exercised by the home month selector | Single-day selection reconciles to the property mart: 300 machines, 6,900 scheduled machine-hours, $1,805,102.85 coin-in; `test_dst_day_uses_23_hours_and_reconciles_property_totals`. |
| Ranking sensitivity is inspectable | No quantitative stability summary | Delete each complete month in turn when at least three are selected; display minimum/maximum adjusted ranks and bottom-ten/testable counts. Independently reconstructed for full and partial windows. |
| Zero exposure does not fabricate rates or ranks | Home had unguarded divisions | Undefined hold/ranks are labeled; zero availability remains 0%; `test_home_zero_exposure_does_not_invent_adjusted_ranks`. |
| Evidence is accessible to anonymous app viewers | GitHub source links require repository access | Each of eight routes renders/downloads committed findings, appendix, and disclosure inside Source. Tests switch documents after period/drill changes with raw-data functions forbidden. |
| Documents cannot expose arbitrary files | No in-app document reader | Publication is restricted to numbered findings and the two submission documents; path traversal and symlink escapes are rejected. |
| Forecast changes a concrete planning comparison | General suggestion to use weekdays | Seven fixed training weekday estimates versus constant demand; a randomized allocation trial keeps weekly staff hours fixed and predeclares its outcome threshold and availability guardrail. No headcount or revenue effect is invented. |

Full-window Home reproduces **8/10** manager picks surviving adjustment. Its stability check shows M-1179 at ranks **9–11**, bottom ten in **5/6** month deletions; M-1158 ranks **68–82**, bottom ten in **0/6**. The fixed July decision is **one $1,200 inspection of M-1158**, preserving **$98,800**. Changing historical filters does not retarget or reprice it. See the [audit finding](../findings/81-dashboard-utility.md) for reproduction and checks.

## Remaining work and limits

- Ranking and its month-deletion ranges are descriptive screens. The runs overlap and the ranges are not confidence intervals or calibrated probabilities; neither a rank nor a sensitivity range estimates replacement uplift. With fewer than three complete months, the app asks for a longer period.
- Public code access, a final video, deployment records, and the final submission remain owned by existing tickets #24, #30, #69, and #70. Inline evidence makes the dashboard self-contained for claim reading; it does not satisfy the separate all-code deliverable or change repository visibility.
- Existing source documents preserve their review status and limitations. Appendix/check-status drift and disputed wording are tracked by #72, #74, and #78. This ticket does not rewrite those owners' evidence.
- Local interaction checks cannot certify the deployed commit. The independent reviewer confirmed the supplied public URL exists; deployed QA belongs to #70 after this PR is reviewed and merged.
- The staffing trial is a proposed measurement design. Its minimum worthwhile effect and availability tolerance must be chosen before execution; coin-in alone cannot determine a staffing level or a causal revenue gain.

## Reproduce

From the repository root:

```bash
uv run pytest tests/test_dashboard_utility.py -q
uv run pytest -q
uv run streamlit run app.py
```

The utility tests replace `DATA_DIR` with an empty directory and reject any attempted raw-table read. They exercise Home and all seven registered pages through the actual multipage entry point. March 8 is tested on daily pages; monthly player/comp pages select March, and the held-out model selects May 1 because its evaluation window starts in May.
