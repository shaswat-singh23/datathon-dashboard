# Judge-path QA on the public URL: every page survives period, drill and Source
- Issue: #70 | Author: Kyle (kyledong25), with Claude Code | Time: 2026-11-07 17:45 America/Chicago
- Claim: On the deployed app, Home and all seven question pages render with zero Streamlit exceptions and zero browser errors when the period is narrowed to one month and to the 23-hour day Mar 8, when the page's drill is used, and when the Source expander and its in-app evidence picker are opened. The demo click path completes on the public URL in 111.9 s, inside the 1:55 target.
- Evidence: 8 of 8 pages PASS from an automated Playwright run (system Google Chrome, headless, 1440 x 1000) against `https://datathon-dashboard-o5xb3rbuuqzppphcqeglmq.streamlit.app/` on master `fd5e0d2` (PR 84 home page; evidence picker lists `findings/86-*`, so the deployment tracks master). Per-page record below.
- So what: AGENTS.md promises judges a period filter, one drill and a Source expander on every page. This run shows each of those controls works on the public app, not just locally, and that the narrowest judge-chosen period (a single 23-hour day) returns numbers rather than an error.
- Checked by: unchecked

## Method

Public URL opened anonymously (no GitHub session). The app renders inside an iframe at `/~/+/`, so the script drove that path directly. For each page: load, read KPIs; set the period slider to one month via keyboard (Home/End plus arrow steps); set it to one day; apply the page's drill; reset the period; open the Source expander and pick the second document in its "Evidence document" selector. A page fails if `stException` appears, a chart renders no traces after scrolling into view, or a KPI does not change when the period changes on a page that claims to recompute.

Cold page loads over the public link, seconds: app 8.0, machines 9.1, demand 4.6, downtime 4.5, players 6.0, comps 6.0, actions 6.3, model 6.0. Warm navigation is 2 to 5 s.

## Per-page record

| Page | Single month | Single day (Mar 8) | Drill | Source expander | Result | Note |
|---|---|---|---|---|---|---|
| app (Home) | pass: coin-in $248,905,219 (Jan–Jun) -> $43,647,425 (Mar); overlap 8/10 -> 3/10 | pass: $1,805,103, hold 10.82%, overlap 0/10 | Bank drill B-01: 6/6 overlap, 6 machines | pass; picker -> `findings/16-demand-changes.md`, 1 download button | PASS | Caption restates the selected scope. |
| machines | pass: overlap 8/10 -> 3/10; leak 1/310 -> 1/308 | pass: 0/10, leak screen 2/300 tested, location chart hidden | Bank drill B-01: 6/6, "No machine crosses the payout-inspection threshold" | pass; picker -> `findings/32-leak-screen.md` | PASS | On a single day the ±3.8 SE screen flags 2 of 300 machines; the page labels these leads, not findings. |
| demand | pass: $1,375k/day -> $1,408k/day | pass: $1,805k/day, "No event days in this period" info | Zone drill Back Forty (Z-B40): $138k/day, 25.4% | pass; picker -> `findings/34-demand-context.md` | PASS | Comparison chart "Back Forty vs rest of floor" renders with both series. |
| downtime | pass: 5,021 lost h -> 979 | pass: 38 lost h, 0.55%, 9 fault tickets | Zone drill Back Forty: 573 lost h, 126 tickets | pass; picker -> `findings/18-player-outcomes.md` | PASS | |
| players | pass: wagers $163.8M -> $28.9M | N/A: month-grain slider, finest period is one month | Compare groups by = age_band | pass; picker -> `findings/17-downtime.md` | PASS | |
| comps | pass: comp cost $190,669 -> $33,256 | N/A: month-grain slider | Home region = Local: $139,696, 1.54% reinvestment | pass; picker -> `findings/17-downtime.md` | PASS | |
| actions | KPIs unchanged by design ($1,200 / $98,800 / 1 of 3): the Evidence period drives the evidence table, not the fixed July plan | same | Action drill = Preventive maintenance sweep for one manufacturer | pass; picker -> `findings/22-machines.md` | PASS | Page text says the plan uses the complete Jan–Jun record; no error on a one-day evidence period. |
| model | pass: full-holdout MAE $68,699/day stays fixed (labelled full holdout); selected-period table shrinks 6 -> 4 tables for one day | May 8 used: slider starts May 1 (holdout), so Mar 8 is unreachable | Error breakdown = Weekday | pass; picker -> `findings/86-dashboard-judge.md` | PASS | |

Browser console errors: 0. Streamlit exceptions: 0. Blank charts after scroll-into-view: 0.

## Demo click path on the public URL (docs/demo_script.md)

Elapsed 111.93 s from the opening slider nudge to the final "Leak source and method" expander, against the 115 s cue table. Clicks alone took 77.2 s; each segment then held to its cue as a narration allowance. Segment 3 (machines bank drill and restore) ran 1.5 s over its cue and was absorbed by later segments. All seven segments landed: the Back Forty comparison chart, the overlap metric with B-01 then All banks (6/6 then 8/10), Players Home region = Local with the carded caption, Model Weekday breakdown plus Source and reproducibility, Actions KPIs ($1,200, $98,800, 1/3) and the Tradeoffs heading, and the funded-inspection page link landing on Machines with the leak expander naming `q1_leak`.

Script drift found (no page failure): step 1 says one Right Arrow moves January to February, but since PR 84 the Home slider is day-grain, so it moves Jan 1 to Jan 2; the Home title and KPI row also changed. Tracked as #92 (`nice`); this ticket does not edit the click path.

## Reproduce

Playwright 1.49.1 with `channel: 'chrome'` against `<public URL>/~/+/`. Sliders are `input[type=range]` inside `[data-testid="stSlider"]` (keyboard Home/End/Arrow keys, one step per day); selectboxes are react-aria comboboxes (type the option text, Enter); expanders are `[data-testid="stExpander"]` with the title in `summary [data-testid="stMarkdownContainer"]`; wait for `[data-testid="stStatusWidget"]` and `[data-stale="true"]` to clear after each action. Scripts are not committed (outside this ticket's Scope); the run log is summarised above.
