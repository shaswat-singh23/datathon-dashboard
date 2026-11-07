# Dashboard walkthrough: inspect before replacing

Issue: #25. Target length: 1:55, including navigation and narration.

## Before the clock starts

- Public URL: **PENDING #24**; use the link recorded in [the deployment finding](../findings/24-deploy.md) when it lands. Shaswat [authorized local rehearsal while deployment is pending](https://github.com/shaswat-singh23/datathon-dashboard/issues/25#issuecomment-6713273848). Local target: `http://localhost:8525`, started with `uv run streamlit run app.py --server.port 8525`.
- **Evidence gate:** the findings linked below are currently `Checked by: unchecked`. This is rehearsal copy. Before recording or presenting results, confirm their independent checks and matching [appendix](claims_evidence.md) entries have landed (#64–#67); reconcile any changed values here. Do not turn provisional readouts into approved video claims. Never describe an inspection lead as wrongdoing or an observational demand change as causal.
- Use a desktop window at 1440 × 1000, with the sidebar open. Visit Home, Demand, Machines, Players, Model and Actions once to warm the app. Reset every period to its full range; Demand to **All zones**, Machines to **All banks**, Players' three group filters to **All**, and Model's **Error breakdown** to **Month**. Return to Home at the top.
- The sidebar labels are **app**, **machines**, **demand**, **downtime**, **players**, **comps**, **actions**, **model**. Each page owns its filters: changing Home does not filter other pages. Speak while controls update; scroll to the named heading rather than searching the whole page.

## Exact click path and spoken script

Times are cumulative cues. The quoted sentences are the complete narration; bracketed instructions are silent.

| Time | Click / screen action | Say |
|---|---|---|
| 0:00–0:13 | Start on **app**. In **Analysis period**, focus the left slider handle and press **Right Arrow** once: January → February. Let the KPIs update, then press **Home** on that handle to restore January–June. | “Our provisional finding: Back Forty demand fell during the walkway closure without a matching decline elsewhere. Investigate access before replacing machines; this is an association.” |
| 0:13–0:26 | Sidebar → **demand**. Open **Zone drill** → **Back Forty (Z-B40)**. Keep the full January–June period. Scroll past **Zones: coin-in per available machine-hour** to **Back Forty vs rest of floor**, the weekly comparison chart with both series and the shaded closure window. | “The shaded closure window lets us compare Back Forty with the rest of the floor. We divide wagers by available machine-hours. Renovation and machine mix remain alternative explanations.” |
| 0:26–0:43 | Sidebar → **machines**. With **All banks**, point to **Manager picks surviving adjustment** and the two ranking tables. Open **Bank drill** → **B-01**; wait for the tables to change, then restore **All banks**. | “The baseline is the manager's lowest total house win. We compare expected contribution per available hour. A bank drill recomputes both lists within that bank. Rankings alone cannot justify replacement.” |
| 0:43–0:55 | Sidebar → **players**. Open **Home region** → **Local**. Point to **Player net** and the carded-play caption; do not interpret a group total as a per-person effect. | “Here we drill into local guests. Player net is payout minus wagers. Carded records miss untracked play, and these results never justify encouraging heavy losers to gamble more.” |
| 0:55–1:17 | Sidebar → **model**. Show **Validation: earlier months train, later months test** and the full-holdout accuracy table. Scroll to **Where are the forecast errors?**, choose **Weekday**, then open **Source and reproducibility** immediately below it. | “We train on January through April and freeze predictions for May and June. Compare constant mean, weekday mean and fitted trend using daily absolute error. The weekday baseline wins this holdout; future performance is uncertain. This source names the model and leakage tests.” |
| 1:17–1:41 | Sidebar → **actions**. Point to **Plan cost**, **Budget preserved** and **Funded action types**. Scroll to **Tradeoffs against preserving the budget**, showing all options and their spend, then return to the funded-inspection paragraph. | “Fund one twelve-hundred-dollar configuration inspection and preserve ninety-eight thousand eight hundred dollars. Maintenance costs nine thousand; extra technician coverage, eleven thousand five hundred twenty. Both are deferred. Preserving everything wins the monetary comparison; inspection buys information, with no positive recovery estimated.” |
| 1:41–1:55 | Open **Trace: funded inspection** → **Machines: raw ranking, adjusted economics and payout screen**. On Machines, scroll to **Leak: inspect, not proof**, then open **Leak source and method**. End on the source and screening limitation. | “Follow the funded inspection to its payout screen and source. Verify configuration by July second, then monitor availability and payout residuals against same-configuration controls through July thirtieth. An unusual payout is an inspection lead.” |

The funded plan has **one** action type. Maintenance and technician coverage are priced alternatives, not additional commitments. The preserve-all comparison is the zero-spend baseline. Keep that distinction even if a presenter shortens the wording.

## Evidence to have open in backup tabs

| Script segment | Finding and appendix trace |
|---|---|
| Opening / closure | [Demand finding](../findings/16-demand-changes.md), appendix row 4; closure comparison uses the finding's before/during/after windows, not the whole-period average shown at the top of Demand. |
| Manager baseline / bank drill | [Machine ranking](../findings/22-machines.md), appendix row 1. Full-floor findings do not become bank-specific claims after filtering. |
| Guest group | [Player outcomes](../findings/18-player-outcomes.md), appendix row 11. No group-specific numerical claim is scripted. |
| Validation | [Forecast evaluation](../findings/47-forecast-evaluation.md), appendix rows 15–16. MAE describes observed error, not a prediction interval. |
| July decision / final trace | [July plan](../findings/23-july-actions.md), appendix row 14; [payout screen](../findings/32-leak-screen.md), row 2. The final UI expander identifies `marts/q1_leak.parquet`, its builder, variance calculation and limitations. |

## Rehearsal record

- Sahith (`sahith1021`), with Codex; 2026-11-07 15:49 America/Chicago, local browser rehearsal.
- Target: `http://localhost:8525`; Chromium, 1440 × 1000, warmed pages, all seven steps above. **Elapsed: 1:55.07 (115.07 seconds)** from the opening period change to the final source expander.
- Method: automated browser clicks with concurrent narration time allowances at **145 words/minute** for the **229-word** script, holding each segment to its cue. This was not a human spoken take. All seven steps passed with zero browser errors or Streamlit exceptions; the comparison chart included both Back Forty and the rest of the floor, and the final trace opened the payout-screen mart and method.
- Supporting checks: all relative document links resolve, the seven cue ranges are contiguous through 1:55, `git diff --check` passes, and `uv run --no-sync pytest -q` reports **56 passed**.
- Kyle (`kyledong25`), with Claude Code; 2026-11-07 17:40 America/Chicago, **deployed-URL rehearsal** (#70). Target: `https://datathon-dashboard-o5xb3rbuuqzppphcqeglmq.streamlit.app/`, anonymous session, Google Chrome headless, 1440 × 1000, warmed pages, all seven steps above. **Elapsed: 1:51.93 (111.93 seconds)** from the opening period change to the final source expander, same automated-click method with narration allowances. Clicks alone took 77.2 s; segment 3 (bank drill and restore) ran 1.5 s over its cue and was absorbed. Zero browser errors or Streamlit exceptions; cold page loads were 4.5 to 9.1 s over the public link. Record: [judge-path QA finding](../findings/70-judge-qa.md).
- Known drift (#92): since PR 84 the Home slider is day-grain, so step 1's Right Arrow moves Jan 1 to Jan 2 rather than January to February, and the Home title and KPI row differ from the wording above. The route still completes. The presenter should rehearse aloud before recording; the automated timing does not verify human delivery.
