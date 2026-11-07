---
name: kickoff
description: Set up the repo and seed the backlog for the challenge we picked. Use right after /triage, once the team has chosen a challenge.
argument-hint: "[chosen challenge name, link, or pasted description]"
disable-model-invocation: true
---

We picked: $ARGUMENTS

Read the challenge's deliverables, judging criteria, data, and any starter code. Then:

1. **Starter code.** If organizers provide a starter repo, say so and stop. We'll copy AGENTS.md, .claude/, .github/, .worktreeinclude, PLAYBOOK.md, and findings/ into theirs instead of reshaping it.
2. **AGENTS.md.** Fill in Challenge (name, deliverables, judging weights, core question), Stack, and Layout. Pick the simplest stack that hits the deliverables. Add challenge-specific rules, such as what the baseline is and how results are measured.
3. **Design for parallel work.** Lay out the code so independent tickets touch different files: one module per feature, plugin-style folders instead of one central file, and shared helpers created now so later tickets don't fight over them. Code reads data from `DATA_DIR` (default `./data`).
4. **Environment.** Set it up with the right tool (for Python: `uv init --bare`, then `uv add` only what the plan needs). Commit the lockfile. Add `.env.example` listing every required variable with no values, including `DATA_DIR`.
5. **Skeleton.** Create only the folders and entry points the plan needs, each runnable.
6. **Permissions.** Add allow rules to `.claude/settings.json` for the stack's run, install, and test commands.
7. **SETUP.md.** Fill in "Stack setup" with the exact commands a teammate runs after `git pull`, ending with one command that proves it works.
8. **Backlog.** Create issues using the AGENTS.md ticket format:
   - A first wave of 4 to 8 `must` tickets with no dependencies on each other and non-overlapping Scope, so everyone can start at once.
   - Then the rest of the plan as `must` or `should` tickets, linked through Depends on.
   - One story ticket for the README and demo, owned by the story owner.

Show the plan (stack, layout, ticket list with Scope) before creating anything. After approval: build, run the proof command, commit to master as `kickoff: <challenge>`, push, then create the issues and print the list.
