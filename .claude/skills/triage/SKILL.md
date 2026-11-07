---
name: triage
description: Rank datathon challenges and pick one. Use right after challenges are released, when the user pastes or links challenge descriptions.
argument-hint: "[pasted challenges, links, or a file path]"
disable-model-invocation: true
---

We are a 4-person team at a roughly 24-hour datathon. Team roles and strengths are in AGENTS.md.

Challenges: $ARGUMENTS

If these are links, fetch every one. If data is downloadable, peek at it (shape, columns, obvious mess). Read each challenge's data, deliverables, and judging criteria.

Score each challenge 1 to 5 on:
- **Data**: provided, usable, rich enough to find something non-obvious?
- **Clarity**: clear metric or rubric?
- **Judging fit**: what do the weights reward (insight, technical, creativity, utility)? Can we win the top-weighted criterion?
- **Competition**: how many teams will pick it? Narrow sponsor prizes often have fewer entrants.
- **Demo**: can we show something compelling in a 2 to 3 minute video?
- **Team fit**: given the roles in AGENTS.md.
- **Stacking**: can the same project also qualify for a side or mini prize?

Output:
1. Table: challenge | score per axis | total | biggest risk (one line)
2. Top pick and runner-up, each with the specific angle or insight we would chase
3. First 3 hours for the top pick, split by role (Claude driver, data owner, analyst, storyteller)
4. Kill criteria: what we could learn in the first 2 hours that should make us switch

Be blunt. If two options are close, say what information would break the tie.
