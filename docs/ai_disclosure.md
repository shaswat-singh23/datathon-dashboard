# AI-use disclosure

Team: Shaswat Singh, Sahith, Kyle Dong, Alex (dandelino-del). Dashboard Royale, TAMU Datathon, 2026-11-07.

We used AI coding agents throughout the build. Humans decided what to build, ranked the backlog, set the analytical rules and reviewed results. Agents wrote most of the code, tests and findings text under those rules. The evidence for this disclosure is the repository itself: `Co-Authored-By` trailers on commits, PR bodies, the `.claude/skills/` folder, and the author line of each `findings/` file.

## Tools

| Tool | Model(s) | Who used it | Evidence in the repo |
|---|---|---|---|
| Claude Code (Anthropic CLI agent) | Claude Opus 5.5, Claude Fable 5.1 | All four team members | 21 commits carry a Claude co-author trailer (18 Opus 5.5, 3 Fable 5.1); PR bodies for #14, #16, #17 and the workflow PRs state "Generated with Claude Code"; skills in `.claude/skills/` |
| OpenAI Codex (CLI agent) | Codex default model | Sahith, Alex | Findings #18, #20, #23, #34, #47 name Codex in their author line; PR #12 and the `$work`/`$ticket` Codex skills (PR #35) |
| Streamlit AppTest, pytest, DuckDB | n/a (not AI) | Agents and humans | Used to verify every page and mart; listed here because agents ran them |

No AI model was used as a data source. No LLM output is quoted as a fact anywhere in the dashboard or write-up.

## What the agents did

- **Scaffolding and conventions.** Claude Code drafted `AGENTS.md`, the ticket-driven workflow, the issue template and the team skills (`/work`, `/ticket`, `/orchestrate`, `/merge-queue`, `/fanout`). Shaswat reviewed and merged these.
- **Shared helpers.** `royale/money.py` (money math) and `royale/budget.py` (action pricing) were written by Claude Code against the rules in `AGENTS.md` and the organizer guide, with tests.
- **Marts and pages.** Each question ticket (#16 to #23, #31, #32, #34, #47) was worked by one agent session in its own worktree: the agent wrote the DuckDB queries in `royale/marts/`, the Streamlit page, the tests and the first draft of the `findings/` file. The agent also ran the independent raw-SQL reconciliations and Streamlit AppTest checks recorded in each finding.
- **Data verification.** Sahith's Codex session ran the organizer's unmodified `verify_data.py` and `verify_semantics.py` scripts (#33).
- **Ticket hygiene and review.** Claude Code sessions running `/orchestrate` and `/merge-queue` re-ran each PR's checks on its exact commit and posted review comments. Agents never merged a PR on their own.
- **Documents.** This disclosure, the Claims & Evidence appendix (#27) and the README draft (#21) were written by Claude Code from the `findings/` files and the git history.

## What the humans did

- Chose the question framing (luck, location, or leak), the baselines, the time-based split and the "no accusations" rule, and wrote them into `AGENTS.md` before any analysis started.
- Ranked the backlog, set priorities and deadlines, and decided which tickets were `must`.
- Reviewed PRs and decided what merged. Every merge was a human action.
- Decided the July recommendation: inspect one machine and preserve the remaining budget, rather than spend to the limit.
- Own the sign-off on findings. As of this writing every `findings/` file is still `Checked by: unchecked`; a second person must review each before its number is treated as confirmed (see the Claims & Evidence appendix).

## Known risks of this workflow and how we handled them

- **Agents can produce confident wrong numbers.** Every finding is required to carry an independent raw-data query that reproduces the headline figure, a simple baseline, an alternative explanation and a limitation. Several findings record row counts before and after every join.
- **Agents can leak future information into forecasts.** The forecast builder only reads gaming date and coin-in from `property_day`, and tests poison the holdout targets to prove the fit does not change.
- **Agents can over-claim.** The write-up and appendix call every result descriptive or an inspection lead; none claims a causal effect or accuses anyone of wrongdoing.

## Outside data

Public context data cited on the Demand page, both fetched by an agent and documented in `findings/34-demand-context.md`: NOAA daily weather for Las Vegas airport station USW00023169, and LVCVA monthly Las Vegas visitor counts (2026-08-20 revision). Neither feeds the forecast.
