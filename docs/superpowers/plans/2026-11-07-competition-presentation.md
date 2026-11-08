# Competition Presentation Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax. This document proposes work; it does not authorize deployment or change the running app.

**Goal:** Turn the current dashboard into a clear, memorable competition demo with investor-style storytelling and verifiable claims.

**Architecture:** Keep Streamlit, all eight existing routes, and the committed parquet marts. Share presentation and filter controls through small helpers; reuse the existing money, ranking, budget, and forecasting functions. Introduce no new backend or framework.

**Tech Stack:** Existing Python, Streamlit, pandas, Plotly, DuckDB, pytest; local SVG/CSS artwork.

**Spec:** [Competition presentation design](../specs/2026-11-07-competition-presentation-design.md).

## What the current experience needs

The casino artwork now gives the app an identity. However, the illustrated header, long question, recommendation paragraph, explanatory captions, three links, and filters push the first metrics below the opening viewport, especially in the narrow companion browser. Eight equal-weight navigation links offer little guidance about the story. Analytical pages often put methodology ahead of the visual result. Each page owns separate filters, so a person can accidentally compare different populations after navigation.

The app already contains valuable capabilities: accessible evidence documents, rank sensitivity, priced alternatives, frozen forecast validation, and a review-day planning comparison. Improve their visibility rather than rebuilding them.

## Global constraints

- Fictional casino and synthetic data must remain visibly disclosed.
- Budget preserved is not savings, profit, or measured return on investment.
- Observational associations and hypothetical recovery scenarios must remain identified.
- The main write-up stays at or below 400 words; the submitted video stays at or below 120 seconds.
- Keep existing routes and numerical definitions; presentation changes must not silently change populations or calculations.
- Maintain accessible contrast, keyboard controls, and responsive layouts. Decorative art must not obstruct reading or interaction.
- Keep the local dashboard running for the user's exploration. Implementation and publication are separate from this planning task.

## Review focus

1. A bank selected on Home must not silently reset when the person follows its machine evidence.
2. Monthly player/comp data and the May–June model holdout must not imply that arbitrary daily filters apply unchanged.
3. A partial period, an empty bank, or zero available hours must show an honest empty/undefined state.
4. A changed historical filter must not silently reprice the fixed July recommendation or rewrite full-holdout model scores.
5. Mobile navigation, keyboard focus, chart alternatives, and evidence access must survive the presentation refinements.

## Priority and estimated effort

Estimates are planning ranges for one implementer familiar with this repo, excluding review delays and recording retakes.

| Priority | Work | Estimate | Outcome |
|---|---|---:|---|
| P0 | Decision-first home and story | 2–3 hours | Judges understand the case quickly |
| P0 | Guided navigation and clear filter scope | 2–4 hours | Exploration stays coherent |
| P1 | Three decision visuals and action comparison | 3–5 hours | The reasoning is memorable and inspectable |
| P1 | Visual hierarchy and accessibility pass | 1–2 hours | Luxury styling supports readable analysis |
| P0 before submission | Evidence reconciliation and timed rehearsal | 1–2 hours | Submission tells a defensible story |
| Optional | Interactive floor map | 3–5 hours | A useful spatial investigation, if time remains |

Recommended core scope: approximately **9–16 hours**. If time is short, finish Home, navigation, and the rehearsal first. Do not delay the required video to build the map.

## Task 1 — Rebuild Home around the decision

**Files:** `app.py`, `royale/overview.py`, `tests/test_dashboard_utility.py`.

**Interfaces:** Consume existing `period_totals`, `summarize`, `proposed_plan`, and `budget.plan_cost_usd`. No new financial metric or model is required.

- [ ] Place a compact title above the decision: **“Investigate before replacing.”** Keep the original ten-machine question as a one-line subtitle.
- [ ] Present the fixed July decision in three clearly named cards: **Inspection budget $1,200**, **Budget retained $98,800**, and **One configuration inspection**. Compute these from the existing plan. Keep “not measured savings” and “information purchase; revenue uplift unproven” next to the cards.
- [ ] Add three evidence cards below: **8/10 remain in the adjusted bottom ten**, **Back Forty shows an access association**, and **M-1158 merits inspection**. Each has one sentence, a period label, an important caveat, and a link to its existing analytical route. Use the reconciled sources in the appendix; avoid copying unchecked findings.
- [ ] Separate fixed-case narrative from filtered exploration with an explicit “Explore the historical data” section. Put existing period/bank controls and operational KPIs there. Decision cards must say “Fixed July plan”; fixed evidence cards must say “Full January–June case”; historical cards must show the active scope.
- [ ] Keep long calculation descriptions in labeled expanders; keep material uncertainty visible beside the result.
- [ ] Extend `test_home_changes_dollars_and_rank_scope_with_bank_and_period` to assert historical metrics change while the fixed July budget remains $1,200/$98,800. Retain the zero-exposure regression test.

**Acceptance:** At 1440×900, the opening screen contains the decision and all three decision cards without scrolling. At 390px wide, the decision precedes the illustration and analytical controls. Three unfamiliar readers can describe the recommendation after 15 seconds without calling retained budget profit.

## Task 2 — Make navigation and filters predictable

**Files:** `royale/theme.py`, new `royale/filters.py`, `app.py`, `pages/1_machines.py`, `pages/2_demand.py`, `pages/3_downtime.py`, `pages/4_players.py`, `pages/5_comps.py`, `pages/6_actions.py`, `pages/7_model.py`, new `tests/test_filters.py`, `tests/test_dashboard_utility.py`.

**Interfaces:** Introduce `analysis_period(key: str, minimum: date, maximum: date) -> tuple[date, date]` in `royale/filters.py`; persist the daily investigation range separately from route widget state. Persist the bank selection for Home and Machines. Monthly guest views and model evaluation retain independent, visibly labeled scopes.

- [ ] Group the eight existing links into **Overview**, **Investigate** (Machines, Demand, Downtime), **Guests & loyalty** (Players, Comps), and **Decide & validate** (Actions, Model). Keep route paths unchanged.
- [ ] Add a compact recommended path on Home: **Machines → Demand → Actions → Model**. Use ordinary links rather than an autoplay tour or modal overlay.
- [ ] Add date presets: **Full period**, **Q1**, **Q2**, **Custom**, with a clear reset. Presets use the dataset’s 2025 dates, not today.
- [ ] Share the daily investigation period across compatible pages; preserve the bank only where it has the same meaning. Show active date/population beside every headline metric and chart.
- [ ] Label guest pages **Monthly guest scope**, Model **May–June evaluation scope**, and Actions **Historical evidence scope; July plan fixed**. Never silently round a day range to months or clamp a January range into May.
- [ ] Replace visible implementation copy such as “validate_plan: no violations” with **“Within budget and catalogue limits.”** Keep diagnostic detail in Source.
- [ ] Add tests for navigation persistence, reset, independent monthly/holdout scopes, empty results, and fixed-plan preservation. Exercise controls by their labels rather than fragile positional indexes.

**Acceptance:** Date and bank context survive Home → Machines. Each route states its scope before results. Reset restores the documented default without changing the fixed forecast or recommendation.

## Task 3 — Replace table-first storytelling with three strong visuals

**Files:** `pages/1_machines.py`, `pages/2_demand.py`, `pages/6_actions.py`, `pages/7_model.py`, `royale/marts/q6_actions.py` if needed for scenario calculations, new `tests/test_presentation_views.py`.

**Interfaces:** Use `summarize(selected)` for rank comparisons, the existing closure-window aggregates for Demand, `assess(data, start, end)` for action scenarios, and `score_forecasts(view)` for forecast error. Presentation transformations must consume these outputs rather than recompute financial definitions.

- [ ] **Machines:** Add a labeled slope chart from manager rank to adjusted rank for the original ten picks. Emphasize M-1158 and M-1118; retain the exact table as the accessible numerical alternative. Explain that a rank shift is not estimated replacement uplift.
- [ ] **Demand:** Promote the existing Back Forty versus rest-of-floor comparison. Annotate the actual closure window and show before/during/after rates with units. Keep an observational-association caption visible. Where the selected window cannot support the comparison, show why rather than silently substituting the full period.
- [ ] **Actions:** Replace the initial dense alternative table with a cost comparison and four short cards: inspect, maintenance, technician coverage, preserve funds. Each card states spend, lead time, downtime, assumed benefit, and the decision. Retain the zero-cost baseline.
- [ ] Offer **0% / 25% / 50% / 100% assumed recovery** as explicit scenarios for maintenance and staffing only. Extend the existing 0/50/100 and halved-recovery work, rather than introducing a separate ROI calculator. Reuse the budget and downtime formulas; inspection never gains hypothetical revenue through this control. Label outputs as scenarios and display implementation costs even at zero recovery.
- [ ] **Model:** Put the three-model MAE comparison and actual-versus-prediction chart before the long methodology section. Lead with the observed weekday-baseline result and its decision implication; do not imply that more complex ML won. Surface the existing review-day planning comparison rather than building another scheduling feature.
- [ ] Add reconciliation tests: chart rank points equal the table values; cost bars equal budget outputs; zero-recovery scenarios retain spend/downtime; changing display order or filters never refits forecasts. Keep data tables downloadable.

**Acceptance:** Each primary chart answers one question, names the comparison, labels units, and offers exact values. A judge reaches the relevant finding and source from a recommendation in no more than two interactions.

## Task 4 — Refine the luxury visual system

**Files:** `royale/theme.py`, `royale/theme.css`, `royale/casino.svg`, `.streamlit/config.toml`, all page header calls if the theme signature changes.

**Interfaces:** Extend `apply_theme(section: str, *, compact: bool = False) -> None`. Home uses the full illustrated identity; inner pages use `compact=True` with a small crest and section label.

- [ ] Keep the roulette/cards/dice/chips artwork on Home, sized around the decision content. On mobile, place the illustration after the decision so the full masthead does not bury the recommendation. Retain warm marquee lights as a static accent. Inner headers should be approximately 64–88px high rather than repeating the large illustration.
- [ ] Keep espresso, ivory, brass, and deep green. Reserve gold for navigation and emphasis; use distinct data colors plus labels/dashes. Red must communicate adverse outcomes or a deliberate series, not generic decoration.
- [ ] Use serif typography for titles and key totals, sans serif for controls, explanations, and tables. Establish consistent spacing and align card heights without truncating labels.
- [ ] Shorten displayed large values to readable forms such as **$248.9M** and **$189/hour**, with the full value available in a labeled detail/table accessible on touch. Retain exact values where decisions depend on them.
- [ ] Keep ordinary text contrast at least 4.5:1, large text at least 3:1, visible focus, and approximately 44px touch targets. Avoid flashing lights, autoplay wheel rotation, and count-up animations that make numbers harder to inspect.
- [ ] Inspect Home, a dense chart page, Actions, and Model at 1440×900 and 390×844. Verify no page-wide horizontal scrolling; tables may scroll within a labeled container. Check keyboard navigation and open/close behavior of the sidebar.

**Acceptance:** The decoration remains distinctive, while results appear sooner and all controls remain readable and reachable. Visual QA is required; passing AppTest alone does not establish layout quality.

## Task 5 — Package the competition story and rehearse

**Files:** `docs/demo_script.md`, `docs/presentation.md`, `docs/writeup.md`, `docs/claims_evidence.md`, `README.md`; update findings only after actually completing the relevant check.

- [ ] Reconcile the README/script’s blanket “unchecked” wording with claim-specific review records. Never mark a claim reviewed just to clear the presentation.
- [ ] Make the script follow this approximately **110-second** sequence, including transitions:
  - **0–15s:** The manager wants to replace ten machines; why raw earnings are insufficient.
  - **15–40s:** Adjusted ranking and the payout inspection lead.
  - **40–65s:** Back Forty closure comparison and the competing location explanation.
  - **65–90s:** The $1,200 inspection, retained budget, alternative costs, and measurement plan.
  - **90–110s:** Honest forecast validation and a closing route to the remaining questions/evidence.
- [ ] Keep Players, Comps, and Downtime plainly reachable for judge questions; the short recording need not visit every route.
- [ ] End with a testable recommendation: inspect configuration, record the result, then measure outcomes. Do not end with unsupported savings or a fabricated commercial ask.
- [ ] Run existing tests and the rubric once on the finished changes: `.venv/bin/python -m pytest -q`, then `.venv/bin/python tools/rubric.py --skip-pytest --output /tmp/gilded-presentation-rubric.json`. Inspect individual rows: the rubric’s process exit code alone does not mean every criterion passed.
- [ ] Rehearse from a clean session and anonymously verify the deployed version after publication. Test period changes, bank/guest drill, validation access, and evidence tracing. Record cold/warm behavior separately; a sleeping host must not be mistaken for a broken analysis.
- [ ] Record the final video at **120 seconds or less**, verify the write-up remains **400 words or less**, and include judge-accessible code, appendix, and disclosure. Keep a backup recording and opening instructions available.

**Acceptance:** Three unfamiliar readers can complete the four judge tasks. The timed narration finishes within the guide’s limit. Every spoken number has a checked source and the same meaning in the app, script, and write-up.

## Optional task — A floor map that helps explain location

**Files:** new `royale/marts/floor_map.py`, `pages/1_machines.py` or `pages/2_demand.py`, new `tests/test_floor_map.py`.

- [ ] Build a small committed spatial mart from organizer `floor_locations` and `floor_walkways`, verifying coordinate units and hierarchy first. Do not invent an architectural layout.
- [ ] Begin with a stable zone/bank overview colored by the selected period’s available-hour demand, with closure annotations. Click a bank to open its metrics; provide a selectbox equivalent for keyboard and mobile use.
- [ ] If individual machine locations are added, require an explicit snapshot date and resolve dated placements. Do not place six months of a moved machine’s totals at its final location.
- [ ] Verify totals reconcile with existing marts, missing coordinates remain visible in an accompanying table, and no-data locations differ from zero demand.

**Acceptance:** The map explains the access hypothesis faster than the existing chart. If it is merely ornamental or cannot preserve date/location meaning, omit it from this iteration.

## Recommended implementation order

1. Task 1, then Task 2: establish the story and reliable exploration.
2. Task 3, then Task 4: improve the evidence presentation and polish the final layouts.
3. Task 5: validate the exact result and record the submission.
4. Add the floor map only if core delivery is complete and the time budget permits it.

Keep authentication, payments, real-time ingestion, multi-property tenancy, a chatbot, and a frontend rewrite outside this competition iteration. They do not help demonstrate the supplied evidence and would make the demo harder to finish reliably.
