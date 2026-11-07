# Event playbook

Times assume a ~24h event. Rescale if it's shorter.

## Roles
| Role | Owns | First 3 hours |
|---|---|---|
| Claude driver | pipeline, app, parallel Claude sessions | `/triage`, download data, `/eda`, app skeleton on real data |
| Data owner | the question, domain context, auditing numbers | read rubric and data dictionary, write the core question in FINDINGS.md, sanity-check EDA |
| Analyst | models, validation | `/baseline` or by hand; decide the split; own "does this actually beat naive" |
| Storyteller | README, slides, video | sponsor research, README skeleton, slide outline, keep asking "what's the headline number?" |

## Timeline
| When | What |
|---|---|
| 0:00 to 0:45 | Everyone reads the challenges. Claude driver runs `/triage`. Decide by 0:45, no later. |
| 0:45 to 3:00 | Data into Drive and data/raw. `/eda`. Data owner writes the core question. Analyst gets a baseline. |
| 3:00 | Sync. Commit to an angle or switch using the triage kill criteria. Last free switch. |
| 3:00 to T-6h | Build. Sync every 3 hours. Merge to main every 2 to 3 hours. |
| Overnight | Sleep in shifts, 2 people at a time, 3 to 4 hours each. Nobody codes 24h straight. |
| T-6h | Feature freeze. No new analyses. |
| T-4h | Code freeze. Polish the app. Run `/ship-check`. |
| T-3h | Record the video. Record it twice. |
| T-1h | Submit. Devpost gets slow near the deadline. |

## Sync (10 minutes, every 3 hours)
Each person: done, next, blocked. Update FINDINGS.md Decisions. Storyteller states the current headline. If nobody can state it, that's the problem to fix next.

## Rules of thumb
- One question answered convincingly beats five answered shallowly.
- Every chart in the final demo answers a question a sponsor would ask.
- When Claude's numbers look great, the data owner checks them before anyone celebrates.
