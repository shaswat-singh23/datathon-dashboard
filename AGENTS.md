# Team conventions

Read by Claude Code, Cursor, Codex, and Copilot. Using ChatGPT or Gemini in a browser? Paste this file in at the start.

All work is a GitHub issue. Agents do the building; humans decide what gets built and check results.

## Team
- Shaswat, Sahith, Kyle, Alex. Everyone builds by pulling tickets.
- **Decider:** Shaswat. Ranks the backlog, sets `must`, calls freezes, and is the only one who edits this file after kickoff.
- **Story:** everyone presents. Story work is `must` tickets with deadlines (created at kickoff). The decider makes sure they land on time.

## Challenge
Dashboard Royale (TAMU Datathon). Fictional 300-machine casino, The Gilded Ace, Jan 1 to Jun 30 2025. Docs and data: `dashboard-royale/` (organizer clone, gitignored), start with `dashboard-royale/GUIDE.md`.
- Challenge: management will replace the 10 machines that earned the least. Is that right, or is it luck, location, or a leak?
- Deliverables: public interactive dashboard (link), video walkthrough under 2 min, write-up under 400 words, one ML or time-series method vs a simple baseline on a time-based holdout, up to 3 priced action types within $100,000 for Jul 1 to Jul 30 2025 (cost, expected effect, uncertainty, measurement plan), all code, AI-use disclosure, Claims & Evidence appendix (table/query, result, alternative explanation, limitation).
- Judging weights: analytical validity 30%, dashboard and communication 25%, modeling and validation 20%, recommendations and tradeoffs 15%, originality 10%.
- Core question: which of the manager's bottom-10 machines are truly underperforming once exposure, availability and luck are accounted for, and which cause (luck, location, leak) do the data support?
- Headline result: ___ (decider updates at each sync)

Judges will: change the analysis period, drill into one bank or one guest group, find how the model was validated, and trace one recommendation back to its evidence. Every page gets a period filter, one drill, and a "Source" expander.

### Challenge rules
- **Baselines.** Machine claims are compared against the manager's list: bottom 10 by raw total house win over active days. The forecast is compared against the training-period constant daily mean (train Jan to Apr, test May to Jun, report MAE).
- **Money math** goes through `royale/money.py`. Ratios are ratios of sums. Theo = coin-in x (1 - configured RTP). Luck residual = house win - theo. Compare per available hour, not raw totals. Scheduled hours come from `calendar_day.scheduled_seconds` (Mar 8 has 23 h).
- **Exclude off-floor rows** (`location_id` null, 1,018 rows) from machine comparisons. Use `placements` for location on a date; machines move.
- **Comp cost is inside POS cogs.** Subtract it once.
- **Carded tables see only carded play.** Compare with `carded_*` columns in `machine_day`, never with totals.
- **No leakage.** Time-based split only. Forecast inputs are what was known on the prediction date; LVCVA and survey tables were published after 2025 and cannot feed a forecast.
- **No accusations.** Unusual payouts are leads to inspect, not findings of wrongdoing. Report player outcomes honestly; no ideas that push heavy losers to play more.
- **Action pricing** goes through `royale/budget.py`: `quantity x (unit_cost + recurring_per_day x max(0, 30 - lead_days))`, at most 3 action types, respect `quantity_limit` and `incompatibility_group`.

## Stack
Python 3.11+ managed by `uv`. Streamlit multipage app, DuckDB for queries over parquet, pandas, Plotly, scikit-learn, pytest. Deploy target: Streamlit Community Cloud from master.
- Run: `uv run streamlit run app.py`
- Build marts: `uv run python -m royale.build`
- Test: `uv run pytest -q`
- Add a package: `uv add <pkg>` in its own small PR, merged first.

## Layout
```
royale/            Python package shared by every page
  config.py        DATA_DIR, table registry, window and budget constants
  io.py            io.table(name), io.sql(query) over DATA_DIR; io.mart(name) over marts/
  money.py         money-math helpers (ticket #1). All pages use these.
  budget.py        action pricing and plan validation (ticket #2)
  marts/           plugin folder: one module per mart, defines NAME and build(con)
  build.py         builds every mart into marts/
app.py             Streamlit home page
pages/             one page per question: 1_machines.py ... 6_actions.py, 7_model.py
marts/             committed derived parquet, each under 5 MB (tests enforce). Pages read only these.
tests/             pytest. Tests that need raw data skip when DATA_DIR is empty.
findings/          one file per result. See "Findings" below.
docs/              write-up, Claims & Evidence appendix, AI disclosure
dashboard-royale/  organizer clone: data + docs. gitignored. NEVER modify.
.env               DATA_DIR and secrets. gitignored. Copied into Claude worktrees by .worktreeinclude.
```
Raw data never enters the repo. Code reads it from the `DATA_DIR` environment variable (absolute path to the folder holding `1_prepared_views/`), so every worktree uses the same data without copying it. A question ticket owns three things and nothing else: `royale/marts/qN_<slug>.py`, `pages/N_<slug>.py`, and its `findings/` files.

## Ticket format
Every issue body has these five headings, in this order. The GitHub issue form produces them. Agents creating issues with `gh issue create` write them by hand.
```
### Goal
The outcome in 1 or 2 sentences, not the steps.

### Done when
- [ ] Checkable criteria: a command that runs, a number produced, a page that loads.

### Scope
Files or folders this ticket may create or change. Everything else is off limits.

### Depends on
#N, #M, or none

### Size
S (under 30 min), M (under 1 hour), or L (under 2 hours). Bigger means split it.
```
Each issue has exactly one priority label: `must`, `should`, or `nice`. Add `bug` for breakage.

## Adding a task
- Anyone can add one: the issue form on GitHub, `/ticket <idea>` in Claude Code, or `gh issue create` using the format above.
- Search open issues first. If it already exists, comment there instead.
- New tasks start as `nice`. Only the decider promotes to `should` or `must`.
- An agent that finds work outside its ticket's Scope does not do it. It creates an issue, mentions the current issue in it, and carries on.
- After feature freeze, only `bug` and story tickets get added.

## Picking a task
- Priority order: `must`, then `should`, then `nice`. Within a priority, oldest first.
- Only pick unassigned issues whose Depends on issues are all closed.
- Claim it: `gh issue edit N --add-assignee @me`. Then check the assignees again. If someone else is on it too, unassign yourself and pick another.
- One ticket per agent session. A person can run several sessions, each on its own ticket in its own worktree.

## Working a task
1. **Isolate.**
   - Claude Code: work in a worktree named `N-<slug>`. Either start with `claude --worktree N-<slug>` or ask Claude to work in a worktree with that name.
   - Other tools: `git fetch origin && git switch -c <yourname>/N-<slug> origin/master`.
2. **Stay inside Scope.** If the work needs a file outside Scope, stop, comment on the issue saying what and why, and continue only after a human OKs it.
3. **Commit small.** Messages start with the issue number: `#N: <what>`.
4. **Verify.** Check every Done-when item by actually running it. Don't assume.
5. **Sync.** `git fetch origin && git rebase origin/master`, fix any conflicts, then verify again.
6. **Open a PR.** Title `#N: <goal>`. The body has `Closes #N`, how each Done-when item was checked, and any number produced. Comment the PR link on the issue.
7. **Merge.** If the ticket produced a result that will be claimed (a number, a score, a finding), someone other than the author reviews it before merge. Anything else, the author merges once checks pass. Agents never merge without a human saying so.
8. **Blocked for more than 15 minutes?** Comment what's blocking on the issue, unassign yourself, and pick another.

## Avoiding merge conflicts
- Tickets running at the same time have non-overlapping Scope. Kickoff and the decider split work that way.
- Features live in separate files: one module per feature, and plugin-style folders (for example a `pages/` directory) instead of one file everyone edits.
- PRs stay small and merge within about 2 hours of starting. Long-lived branches cause conflicts.
- Dependency changes go in their own small PR, merged first. On a lockfile conflict, take master's lockfile and re-run the add command.
- Results go in their own files in `findings/`, never one shared file.

## Rules
1. Never edit or overwrite anything in data/raw or dashboard-royale/.
2. Every result is compared against a simple baseline (naive model, random agent, rule of thumb). No baseline, no claim.
3. If a result looks too good, assume a bug or leakage until proven otherwise.
4. When combining data, check row counts before and after.
5. A number goes in `findings/` before it goes in slides or the README.
6. master always runs.
7. Secrets live in `.env` and are read from environment variables. Each person uses their own API key. Never commit or paste a key.
8. Never force-push.

## Findings
One file per result: `findings/<issue>-<slug>.md`.
```
# <title>
- Issue: #N | Author: <name> | Time: <hh:mm>
- Claim:
- Evidence: <number> from <command, script, or query>
- So what: <why a judge should care>
- Checked by: <name>, or "unchecked"
```
