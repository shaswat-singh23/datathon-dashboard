---
name: kickoff
description: Set up the repo for the challenge we picked. Use right after /triage, once the team has chosen a challenge.
argument-hint: "[chosen challenge name, link, or pasted description]"
disable-model-invocation: true
---

We picked: $ARGUMENTS

Read the challenge's deliverables, judging criteria, data, and any starter code. Then:

1. **Starter code**: if organizers provide a starter repo, say so and stop. We will copy AGENTS.md, .claude/, PLAYBOOK.md, and FINDINGS.md into theirs instead of reshaping it.
2. **AGENTS.md**: fill in Challenge (name, deliverables, judging weights), Stack, and Layout. Pick the simplest stack that hits the deliverables. Add challenge-specific rules (for example: what the baseline is, how results are evaluated, what must be demoable).
3. **Environment**: set it up with the right tool for the stack (for Python: `uv init --bare`, then `uv add` only what the plan needs). Commit the lockfile.
4. **Skeleton**: create only the folders and entry points the plan needs, each runnable. Add `.env.example` listing required keys, no values.
5. **Permissions**: add allow rules to `.claude/settings.json` for the stack's run, install, and test commands.
6. **SETUP.md**: add a "Stack setup" section with the exact commands a teammate runs after `git pull`, ending with one command that proves it works.
7. **FINDINGS.md**: fill in the Decisions section.

Show the plan before creating files. After approval, build it, run the proof command, and commit to master as "kickoff: <challenge>".
