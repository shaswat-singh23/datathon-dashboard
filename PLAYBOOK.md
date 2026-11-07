# Event playbook

Times assume a ~24h event. Rescale if it's shorter.

## Roles
| Role | Owns | First 3 hours |
|---|---|---|
| Claude driver | core build, parallel Claude sessions | `/triage`, `/kickoff`, skeleton running on real data |
| Data owner | the question, domain context, auditing numbers | read rubric and data or inputs, write the core question in FINDINGS.md, sanity-check first outputs |
| Analyst | models, evaluation | define the baseline and how results are measured; own "does this actually beat the baseline" |
| Storyteller | README, slides, video | sponsor research, README skeleton, slide outline, keep asking "what's the headline number?" |

## Timeline
| When | What |
|---|---|
| 0:00 to 0:45 | Everyone reads the challenges. Claude driver runs `/triage`. Decide by 0:45, no later. |
| 0:45 to 1:15 | Claude driver runs `/kickoff`: stack, skeleton, SETUP.md. Everyone else: data into Drive, read deliverables and rubric. |
| 1:15 to 3:00 | Everyone pulls and runs the stack setup in SETUP.md. Data owner writes the core question. Analyst gets a baseline. |
| 3:00 | Sync. Commit to an angle or switch using the triage kill criteria. Last free switch. |
| 3:00 to T-6h | Build. Sync every 3 hours. Merge to main every 2 to 3 hours. |
| Overnight | Sleep in shifts, 2 people at a time, 3 to 4 hours each. Nobody codes 24h straight. |
| T-6h | Feature freeze. No new analyses. |
| T-4h | Code freeze. Polish the demo. Run `/ship-check`. |
| T-3h | Record the video. Record it twice. |
| T-1h | Submit. Devpost gets slow near the deadline. |

## Sync (10 minutes, every 3 hours)
Each person: done, next, blocked. Update FINDINGS.md Decisions. Storyteller states the current headline. If nobody can state it, that's the problem to fix next.

## Rules of thumb
- One question answered convincingly beats five answered shallowly.
- Everything in the final demo answers a question a sponsor would ask.
- When Claude's numbers look great, the data owner checks them before anyone celebrates.
