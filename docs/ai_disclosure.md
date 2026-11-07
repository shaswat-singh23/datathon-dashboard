# AI-use disclosure

This project was built by a four-person team using AI coding agents under the conventions in [AGENTS.md](../AGENTS.md). Humans decided what to build, ranked the backlog, reviewed results and own every claim. Agents did most of the typing.

## Tools used

| Tool | Evidence in the repository | Used for |
|---|---|---|
| Claude Code (Anthropic), models Claude Opus 5.5 and Claude Fable 5.1 | `Co-Authored-By` trailers on commits; the `/work`, `/ticket`, `/fanout`, `/merge-queue` and `/orchestrate` skills in `.claude/skills/` | Writing mart builders, pages, tests and findings drafts from GitHub tickets; drafting PR descriptions; an independent reviewer session that re-ran each PR's checks before merging; an orchestrator session that kept tickets well-formed and posted status reports; this appendix and disclosure |
| OpenAI Codex | Author lines in `findings/18-player-outcomes.md`, `20-coin-in-forecast.md`, `23-july-actions.md`, `34-demand-context.md`, `47-forecast-evaluation.md` | Same ticket-driven building for the players, forecast, actions and context work |
| Other assistants allowed by AGENTS.md (Cursor, GitHub Copilot, ChatGPT, Gemini in a browser) | Named in `SETUP.md`; no repository evidence of use beyond that | Permitted for ticket work by any teammate; nothing in this repo is attributed to them |

## What the agents did

- Turned each GitHub issue (goal, done-when, scope) into code, tests and a `findings/` file, inside the issue's scope.
- Wrote the SQL and pandas behind every mart in `royale/marts/`, the Streamlit pages in `pages/`, and the pytest suite.
- Drafted the text of findings files, this appendix, the write-up and PR bodies from the numbers their own code produced.
- Reviewed pull requests as a separate agent session that re-ran the tests on the exact commit and either merged or requested changes.

## What the humans did

- Chose the questions, the money-math rules and the baselines (AGENTS.md "Challenge rules"), and ranked which tickets got built.
- Read every PR summary, re-ran checks where they chose to, merged or requested changes, and decided which claims go in the story.
- Recorded the video, presented, and uploaded the submission.

## What AI did not do

- No large language model runs inside the dashboard or the analysis pipeline. The app, marts, model and tests call only DuckDB, pandas, scikit-learn, Plotly and Streamlit; there is no LLM API client in `royale/`, `pages/` or `app.py`.
- No number in the dashboard, findings or write-up comes from a model's memory. Every figure is computed by code in this repository from the organizer's data, and each finding carries a Reproduce block.
- Agents did not label any machine, guest or employee as cheating or at fault. Unusual payouts are reported as inspection leads only.

## Limits of this process

- Agent-written reconciliation checks were run by the same agent that wrote the code. Independent human re-runs are tracked in the `Checked by` line of each finding and in the last column of [claims_evidence.md](claims_evidence.md); at the time of writing none has been completed.
- Agents drafted prose from their own results, so wording may overstate certainty in places. Findings state their alternative explanations and limitations to counter this; readers should weigh those sections as heavily as the headline numbers.
- The synthetic organizer dataset and the AI-assisted workflow are both documented so that a judge can re-run any claim without trusting either.
