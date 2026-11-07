---
name: improve
description: Continuous loop that raises the dashboard's score on the judging rubric. It runs an automated rubric check, takes the worst-failing weighted check, fixes it in a worktree, and opens a PR, then repeats. Look and theme are out of scope. Use on a /loop, or when asked to improve the dashboard against the rubric.
effort: high
---

You raise this dashboard's score on the judging rubric, one failing check at a time, until every check passes. Then you look for checks the rubric should have and add them. Judges score analytical validity 30%, dashboard and communication 25%, modeling and validation 20%, recommendations 15%, and originality 10%. Look and theme (colors, fonts, layout polish) are **out of scope**: don't touch them. AGENTS.md is the standard: Challenge rules, Rules, Token hygiene, Working a task.

## Step 0: the rubric checker
If `tools/rubric.py` doesn't exist, building it is your first ticket. It runs every check below that can be automated, and writes `data/rubric.json` (one row per check: id, weight, pass or fail, details) plus a one-line score. Pages run headless through `streamlit.testing.v1.AppTest`. Mark checks that can't be automated as `manual` and leave them out of the score. Run it with `uv run python tools/rubric.py`, and add a pytest that runs it.

## The checks (weight in brackets)
**What judges do with every dashboard** (communication, 25%)
- R1 [3] Every page in `app.py` and `pages/` runs headless with no exception, using only the committed `marts/` (unset `DATA_DIR`), and renders in under 5 s.
- R2 [3] Every page has a period control, and changing it changes at least one number on the page.
- R3 [2] Every page has a drill control (bank, zone, machine, or guest group) that changes what's shown.
- R4 [2] Every page has a "Source" expander that names its mart, the query behind it, and the `findings/` file.
- R5 [3] The model page shows the time-based holdout (train January to April, test May to June), MAE against the constant-mean baseline, and a predicted-vs-actual chart.
- R6 [3] Every recommendation on the actions page links to the evidence for it: a page plus a `findings/` file.

**Analytical validity** (30%)
- R7 [4] Every number in `docs/` and the README matches a `findings/` file whose "Checked by" isn't `unchecked`.
- R8 [3] The Claims & Evidence appendix has an entry for every finding: table or query, result, alternative explanation tested, and limitation.
- R9 [2] Comparisons between machines or groups show uncertainty, such as intervals or a luck band, not just point values.
- R10 [2] Money math goes through `royale/money.py`. No hand-rolled hold or theo calculations, no means of daily ratios, and off-floor rows excluded.

**Modeling, recommendations, deliverables** (35%)
- R11 [2] Forecast inputs only use what was known at prediction time. No LVCVA or survey data in model code.
- R12 [3] `royale/budget.py` validates the plan: at most 3 action types, at most $100,000, quantity limits and incompatibilities respected. Each action states its cost, expected effect, uncertainty, and how it'll be measured.
- R13 [2] The write-up is 400 words or fewer, and the AI-use disclosure exists.
- R14 [2] The deployed URL returns 200 and loads the home page.
- R15 [1] Every mart is under 5 MB, and `uv run pytest -q` passes.
- R16 [2] Charts don't rely on color alone, and every chart has a title and labeled axes. This is about accessibility, not looks.
- R17 [1] At least one finding is marked as unexpected and gives the steps to reproduce it (originality).

## Each run
1. `git fetch origin`, run the rubric on master, and read `data/rubric.json`.
2. Pick the failing check with the highest weight that no open issue or PR already covers. Never take an issue that has a worktree in this clone (`git worktree list`), or one assigned to you that this session didn't create: your other sessions share your GitHub login.
3. Create an issue (AGENTS.md format, labels `experiment` and `should`) naming the check ID, and assign it to yourself.
4. Fix it in a worktree named `N-<slug>`, inside one question's three files (mart, page, findings), `docs/`, or `tools/rubric.py`. Respect each ticket's Scope as AGENTS.md describes.
5. Re-run the rubric. The check must now pass, and no other check may get worse. Open a PR with `Closes #N`, listing the rubric score before and after. The merge-queue reviewer verifies it.
6. Repeat. When every automated check passes, look for gaps a judge would notice (for example a claim with no alternative tested, a confusing drill, an empty state), add a check for it to `tools/rubric.py`, and continue.

## When you hit a limit
Find the workaround, note it on the issue, and keep going. A page that can't run headless gets a smaller test. A slow check gets a cached mart. A blocked ticket means pick the next failing check. Only stop to ask a human about anything irreversible. Submitting to Devpost is human-only.

## Never
- Change colors, fonts, or theme, or any styling that's purely visual.
- Merge anything, edit `dashboard-royale/`, force-push, or submit.
- Mark a finding as checked when you wrote it yourself.
