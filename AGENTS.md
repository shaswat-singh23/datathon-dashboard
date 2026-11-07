# Team conventions

Read by Claude Code, Cursor, Codex, and Copilot. Using ChatGPT or another chat tool? Paste this file in at the start.

## Team (fill in before the event)
- Claude driver: Shaswat. Core build, parallel Claude sessions.
- Data owner: ___. Question framing, domain context, audits every number.
- Analyst: ___. Modeling, evaluation, validation.
- Storyteller: ___. README, slides, video. Starts by hour 4.

## Challenge
Filled in at kickoff (`/kickoff`).
- Challenge: ___
- Deliverables: ___
- Judging weights: ___

## Stack
Filled in at kickoff. Until then, nothing is installed and nothing is assumed.

## Layout
Filled in at kickoff. Defaults that hold for any challenge:
```
data/raw/     original data exactly as downloaded. NEVER modify. gitignored.
FINDINGS.md   every insight, number, and decision. Single source of truth.
.env          API keys and secrets. gitignored. Never commit, never paste into code.
```

## Rules
1. Never edit or overwrite anything in data/raw.
2. Every result is compared against a simple baseline (naive model, random agent, rule of thumb). No baseline, no claim.
3. If a result looks too good, assume a bug or leakage until proven otherwise.
4. When combining data, check row counts before and after.
5. A number goes in FINDINGS.md, with the code that produced it, before it goes in slides or the README.
6. main always runs. Check before every merge.
7. Small commits with clear messages. Pull before you push.
8. Secrets live in `.env` and are read from environment variables. Each person uses their own API key when possible.

## Git
- One branch per person: `<name>/<topic>`. Merge to main every 2 to 3 hours.
- Never commit data/raw, `.env`, or files over 50 MB.

## FINDINGS.md entry format
```
### <title> (<name>, <time>)
- Claim:
- Evidence: <number> from <script or query>
- So what: <why a judge should care>
```
