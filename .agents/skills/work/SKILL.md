---
name: work
description: Pick up a backlog issue and carry it through to a pull request, following AGENTS.md. Use when the user says work, take, or pick up an issue, or asks for the next task. The user may give an issue number after the skill name.
---

Follow "Picking a task" and "Working a task" in AGENTS.md exactly. If the user gave an issue number, use it. Otherwise choose one.

1. **Clean start.** Run `git status`. If there are uncommitted changes, stop and ask what to do with them.
2. **Choose** (only if no number was given). List unassigned open issues by priority: `gh issue list --state open --search "no:assignee" --label must`, then `should`, then `nice`. Pick the oldest one whose Depends on issues are all closed (`gh issue view <dep> --json state`). Say which you picked and why.
3. **Claim.** `gh issue edit N --add-assignee @me`, then `gh issue view N --json assignees`. If anyone else is assigned, unassign yourself and go back to step 2.
4. **Branch.** `git fetch origin && git switch -c <github-username>/N-<short-slug> origin/master`.
5. **Plan.** Read the issue, then state in a few lines how you'll meet each Done-when item inside Scope.
6. **Build.** Stay inside Scope. Work you find outside Scope becomes a new issue (use the ticket skill), not a fix. Commit as `#N: <what>`.
7. **Verify.** Run every Done-when check. Any result that will be claimed gets a file in `findings/`.
8. **Ship.** `git fetch origin && git rebase origin/master`, verify again, `git push -u origin HEAD`, and open the PR as AGENTS.md describes (`gh pr create --title "#N: <goal>" --body-file <tmp>` with `Closes #N`). Comment the PR link on the issue.
9. **Report.** What changed, how each Done-when item was checked, and whether it needs a reviewer before merging. Don't merge unless the user says to.
10. **Reset.** `git switch master && git pull`, so the next ticket starts clean.
