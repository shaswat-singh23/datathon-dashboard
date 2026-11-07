# Dashboard figures

Issue [#26](https://github.com/shaswat-singh23/datathon-dashboard/issues/26).
Captured locally on November 7, 2026 (America/Chicago), from application and mart
commit `fddf14324d0c1414fb991de8104bbd773bb14771`. The public deployment is tracked
separately in #24. These are real Chromium captures of the Streamlit pages, with
the navigation, filters and complete selected sections visible. The headline is
a standalone Plotly chart of the existing README result.

**Provisional:** all linked source findings currently say `Checked by: unchecked`.
Matching a screenshot to its source is an author verification, not independent
analytical review. Retain that status when reusing these figures in slides or
Devpost; finalize claims after the source findings are independently checked.

| Figure | Period and drill | Finding and reproduction | Values checked / comparison |
|---|---|---|---|
| [q1.png](q1.png) | Jan 1–Jun 30, 2025; All banks | [#22 machines](../findings/22-machines.md), `q1_machines.summarize` | 8/10 overlap; all ten manager rows' house win, adjusted rank and luck z match the finding. Baseline: bottom ten by total house win over active on-floor days. |
| [q2.png](q2.png) | Jan 1–Jun 30, 2025; All zones; Daily | [#16 demand](../findings/16-demand-changes.md), zone/day and month aggregations of `q2_demand`; [#47 floor-total reconciliation](../findings/47-forecast-evaluation.md) | $248,905,219.25 over 181 days rounds to the displayed $1,375k/day; February/June exposure-adjusted rates are $197.1/$179.7. Daily trend and month table use the same mart and ratios of sums as the finding. |
| [q3.png](q3.png) | Jan 1–Jun 30, 2025; All zones | [#17 downtime](../findings/17-downtime.md), `machine_day` and `fault_repair` records in `q3_downtime` | 5,021 lost hours; 0.38%; $973,564 lost coin-in rounds to $974k; $90,663 lost theo rounds to $90.7k; 1,207 faults. All six monthly lost-hour totals match. Manufacturer shares use the fleet-wide lost share as baseline. |
| [q4.png](q4.png) | Jan–Jun gaming months; all regions, ages and opening tiers | [#18 player outcomes](../findings/18-player-outcomes.md), `q4_players.outcomes` and `monthly_summary` | Five monetary totals, six active-player counts, ahead shares, and top-1%/10% wager/loss shares match the finding. Wagers $163,804,869.65; payout $148,219,409.05. Equal-share baseline is explained below the concentration table. |
| [q5.png](q5.png) | Jan–Jun gaming months; no tier or region restriction | [#19 comps](../findings/19-comps.md), tracked monthly aggregates in `q5_comps` | Economic cost $190,669.30; menu value $682,749.50; cost/theo 1.2313% rounds to 1.23%. Economic cost and menu value are distinct. The finding also supplies the earlier-period redemption-intensity baseline; its later page section is outside this capture. |
| [q6.png](q6.png) | July 1–30 plan; Jan 1–Jun 30 evidence | [#23 July actions](../findings/23-july-actions.md), `q6_actions.proposed_plan`, `assess`, and `royale.budget` | One funded M-1158 inspection costs $1,200 and preserves $98,800; validation has no violations. All priced alternatives and halved-recovery rankings match the finding. Preserve-all is the $0-spend/$0-incremental-theo baseline. |
| [q7.png](q7.png) | May 1–Jun 30 holdout; all three forecasts; Month drill | [#47 forecast evaluation](../findings/47-forecast-evaluation.md), `royale.model.score_forecasts` on `q7_forecast` | Constant / weekday / fitted trend MAE: $218,258.10 / $68,698.55 / $96,657.83 per day. Lowest MAE rounds to $68,699/day. Training is Jan–Apr; the fitted regression does not beat the weekday baseline. |
| [headline.png](headline.png) | Before Jan 27–Mar 2; during Mar 3–Apr 6; after Apr 7–May 11, 2025 | [#16 demand, evidence 1](../findings/16-demand-changes.md); [render_headline.py](render_headline.py) | Back Forty $135.5 / $96.3 / $125.9 versus rest of floor $206.1 / $210.7 / $197.4 per available machine-hour. Each window has 35 gaming days. All six labels are recomputed from the mart and asserted against the finding. |

The headline uses `royale.money.per_available_hour`: total coin-in divided by total
available machine-hours. It uses a zero-origin vertical axis and shows the same
windows for both series. The closure windows are gaming-date windows from #16;
the underlying UTC closure ends April 7. The chart describes an association:
machine mix, renovation and seasonality remain alternative explanations.

## Reproduce

From the repository root, start the app in one terminal:

```bash
uv run streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8526
```

In another terminal, generate the chart and capture the pages. Playwright is
temporary capture tooling installed outside the project; Chromium requires its
usual operating-system libraries. No project dependency or raw data is needed.

```bash
uv run python -m figures.render_headline /tmp/26-headline.html
npm install --prefix /tmp/royale-figures playwright@1.56.1
PLAYWRIGHT_BROWSERS_PATH=/tmp/royale-figure-browsers node /tmp/royale-figures/node_modules/playwright/cli.js install chromium
PLAYWRIGHT_BROWSERS_PATH=/tmp/royale-figure-browsers NODE_PATH=/tmp/royale-figures/node_modules node figures/capture.cjs
```

`FIGURES_BASE_URL` can select another local port, and `HEADLINE_HTML` can select
another generated HTML path. The capture script waits for Streamlit to finish,
rejects page exceptions, checks key displayed values, and crops before the next
section so tables and charts stay complete. It rejects any PNG at or above
1,000,000 bytes (a stricter limit than 1 MiB). Browser/platform font differences
can change pixels without changing the underlying values.

Verification for this capture: all seven pages completed without exceptions;
all eight PNGs decode and are below 1,000,000 bytes; the source-value checks in the
table above passed. To repeat the numerical checks beyond the capture's key-value
assertions, use each linked finding's reproduction block. The app and committed
marts were read without rebuilding or changing them.
