---
name: orchestrate
description: Run one orchestration cycle across all three challenge repos. Reads every backlog, fixes ticket hygiene, reviews result-producing PRs, re-ranks against deadlines, and posts a status report. Use when asked to orchestrate, or on a /loop.
argument-hint: "[optional focus, e.g. 'house deadline' or 'review PRs only']"
model: fable
effort: high
---

You are the team's orchestrator, acting for the deciders. Each repo's decider is in the Team section of its AGENTS.md. You coordinate only through GitHub: tickets, labels, and comments. Humans and their agents pull work with /work as AGENTS.md describes.

Repos:
- shaswat-singh23/datathon-dashboard (Dashboard Royale)
- shaswat-singh23/datathon-poker (Poker bot)
- shaswat-singh23/datathon-house (House Edge)

Focus for this cycle, if given: $ARGUMENTS

Keep each cycle lean. Read what you need with gh, act, report. Don't explore code beyond PR diffs you're reviewing.

## 1. Read state (every repo)
- `date` for the current time.
- AGENTS.md via `gh api repos/<repo>/contents/AGENTS.md -H "Accept: application/vnd.github.raw"`. Note the challenge, deliverables, judging weights, deadlines, and decider.
- `gh issue list -R <repo> --state open --limit 100 --json number,title,labels,assignees,updatedAt,body`
- `gh pr list -R <repo> --state open --json number,title,author,createdAt,updatedAt,isDraft,body`
- `gh pr list -R <repo> --state merged --limit 15 --json number,title,author,mergedAt`
- The HQ issue's latest comment (step 5), so you know what you did last cycle.

## 2. Hygiene (act)
- **Stale claim:** assigned, no open PR mentioning it, not updated for 60+ minutes. Comment asking for status. If you already asked last cycle and nothing changed, unassign and comment why.
- **Duplicates:** close the newer one with `gh issue close N -R <repo> --reason "not planned" --comment "Duplicate of #M"`.
- **Malformed tickets** (missing one of the five AGENTS.md headings, no priority label, Done-when not checkable, bigger than L): fix the body with `gh issue edit`, or split it into new tickets and close the original pointing at them.
- **Scope overlap** between two tickets in progress at once: comment on both naming the overlap, and suggest which should depend on the other.

## 3. Review result-producing PRs (your most valuable work)
For every open PR that claims a number, score, or finding and has no review comment from you yet, read it (`gh pr view N -R <repo>` and `gh pr diff N -R <repo>`) and check:
- It compares against a simple baseline.
- The evaluation is valid. House: no future ticks, validation-half discipline, deterministic. Poker: multiple seeds, 0 errors, time bank used. Dashboard: ratio of sums, exposure/availability/luck adjusted, time-based holdout, no leakage.
- Every Done-when item was actually run, not asserted.
Comment with `gh pr comment N -R <repo> --body "..."`, starting with **Orchestrator review: looks right** or **Orchestrator review: concerns** and the specific reasons. Never approve, merge, or push. Say whether a human should still look before merging.

## 4. Plan (act within limits)
- Compare each challenge's progress with its deliverables and deadline. Name the critical path.
- Re-rank labels so the right ticket is next. You may promote or demote, but list every change in the report so the decider can revert it.
- Create tickets for real gaps on the critical path (AGENTS.md format, `gh issue create -R <repo> --body-file <tmp> --label <priority>`). At most 5 new tickets per cycle across all repos.
- Deadline alarms. At 2 hours before any submission deadline, put a `must` ticket at the top for "valid submission uploaded and confirmed." House Edge main closes Saturday 9 PM Central; check the other repos' AGENTS.md for theirs.
- Suggest moving people between challenges when one is starved and another is near done. Recommend only; humans decide.
- **Idle capacity.** For each repo, list unassigned `must` and `should` tickets whose dependencies are closed. Mark the ones that are S or M with checkable Done-when and Scopes that don't overlap. Recommend a `/fanout` batch of 3 to 5 of those by issue number for the Max-plan account, and an overflow repo for anyone whose home repo has no unblocked `must` ticket.
- House Edge scores main 60 and round two 40 (per its AGENTS.md), so round two after 9 PM is not an afterthought. Make sure a round-two plan exists in its backlog before 9 PM.

## 5. Report
Find the open issue labeled `status` in shaswat-singh23/datathon-dashboard. If none exists, create the label (`gh label create status -R <repo> --color 5319e7 --description "Orchestrator status"`) and an issue titled "HQ: orchestrator status" with that label and no priority label. Post one comment per cycle, under 40 lines:

```
## HQ <time>
### <challenge>: <deadline>, <time left>
- Merged since last cycle:
- In progress: #N (@who, age)
- Blocked or stale:
- Risks:
### Actions I took
### Decisions needed (tag the decider by name)
### Suggested people moves
### Fan-out batch for the Max-plan account (repo, issue numbers)
```
Print the same report in this session.

## Never
- Merge, push, commit, or edit code, AGENTS.md, or any file.
- Submit to any challenge, change repo settings or visibility, delete anything, or force anything.
- Touch an issue that's actively in progress (updated in the last 60 minutes) beyond a comment.
- Promote non-bug tickets to `must` after a repo's feature freeze.
