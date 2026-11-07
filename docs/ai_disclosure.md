# AI-use disclosure

This project was built by a four-person team using AI coding agents under the conventions in [AGENTS.md](../AGENTS.md). Humans decided what to build, ranked the backlog, reviewed results and own every claim. Agents did most of the typing.

## Tools used

| Tool | Evidence in the repository | Used for |
|---|---|---|
| Claude Code (Anthropic), models Claude Opus 5.5 and Claude Fable 5.1 | `Co-Authored-By` trailers on commits; the `/work`, `/ticket`, `/fanout`, `/merge-queue` and `/orchestrate` skills in `.claude/skills/` | Writing mart builders, pages, tests and findings drafts from GitHub tickets; drafting PR descriptions; two independent reviewer sessions (`/merge-queue`) that re-ran each PR's tests on its exact commit and then merged it or requested changes; an orchestrator session that kept tickets well-formed and posted status reports; this appendix and disclosure |
| OpenAI Codex | Author lines in `findings/18-player-outcomes.md`, `20-coin-in-forecast.md`, `23-july-actions.md`, `34-demand-context.md`, `47-forecast-evaluation.md` | Same ticket-driven building for the players, forecast, actions and context work |
| Other assistants allowed by AGENTS.md (Cursor, GitHub Copilot, ChatGPT, Gemini in a browser) | Named in `SETUP.md`; no repository evidence of use beyond that | Permitted for ticket work by any teammate; nothing in this repo is attributed to them |

## What the agents did

- Turned each GitHub issue (goal, done-when, scope) into code, tests and a `findings/` file, inside the issue's scope.
- Wrote the SQL and pandas behind every mart in `royale/marts/`, the Streamlit pages in `pages/`, and the pytest suite.
- Drafted the text of findings files, this appendix, the write-up and PR bodies from the numbers their own code produced.
- Reviewed pull requests in two separate reviewer agent sessions, both running the `/merge-queue` skill under Kyle's GitHub account and both posting comments that start with `Reviewer:` on the exact commit they checked. The first ran from about 20:25 UTC on 2026-11-07; the second ran a shorter loop from about 22:40 to 23:05 UTC. The GitHub record shows:
  - PRs #1 to #50 were merged by team members before any reviewer session existed (the `/merge-queue` skill itself landed in #49 at 19:35 UTC). None has a reviewer comment.
  - A reviewer session approved and then merged, within seconds, #51, #52, #53, #55, #57, #58, #68, #71, #80, #82, #83, #84 and #87. The second session is the one that merged #71, #80, #82 and #83.
  - Humans merged #77 and #85 after a reviewer approval.
  - Seven PRs were merged before a reviewer had approved them: #54 (merged by its author after a conflict-only change request), #61 (merged one commit past the reviewed commit, after a change request), #62 (merged while labeled needs-human, with no prior review), #63 (merged as a draft before any review), #73, #75 and #76 (merged before any review). Each received a reviewer check after the merge. Those checks found no blocking problem except on #75, whose merge commit reverted one appendix row; that was filed and fixed separately (#78, #79, #82).
- Independently re-ran the Reproduce blocks of findings #23, #31, #32, #34 and #47 in the first reviewer session and matched their numbers. These are agent re-runs, not human checks; see "Limits of this process".

## What the humans did

- Chose the questions, the money-math rules and the baselines (AGENTS.md "Challenge rules"), and ranked which tickets got built.
- Read PR summaries and the reviewer sessions' reports, merged PRs themselves (every PR up to #50, and later #54, #61, #75, #76, #77 and #85), and decide which claims go in the story. The reviewer sessions merged the rest.
- Will record the video, present, and upload the submission (tickets #30, #28 and #29); none of these had happened when this disclosure was written.

## What AI did not do

- No large language model runs inside the dashboard or the analysis pipeline. The app, marts, model and tests call only DuckDB, pandas, scikit-learn, Plotly and Streamlit; there is no LLM API client in `royale/`, `pages/` or `app.py`.
- No number in the dashboard, findings or write-up comes from a model's memory. Every figure is computed by code in this repository from the organizer's data, and each finding carries a Reproduce block.
- Agents did not label any machine, guest or employee as cheating or at fault. Unusual payouts are reported as inspection leads only.

## Limits of this process

- Agent-written reconciliation checks were first run by the same agent that wrote the code. The merge-queue reviewer agent then independently re-ran five findings' Reproduce blocks (#23, #31, #32, #34, #47) and matched their numbers. No human has re-run any finding at the time of writing. Human checks are tracked in the `Checked by` line of each finding and in the last column of [claims_evidence.md](claims_evidence.md); whether agent re-runs count toward that line is the decider's call.
- Agents drafted prose from their own results, so wording may overstate certainty in places. Findings state their alternative explanations and limitations to counter this; readers should weigh those sections as heavily as the headline numbers.
- The synthetic organizer dataset and the AI-assisted workflow are both documented so that a judge can re-run any claim without trusting either.
