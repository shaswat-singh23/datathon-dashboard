---
name: ship-check
description: Pre-submission check that the repo, README, app, and demo are ready. Use before submitting or when the user asks whether we are ready to ship.
disable-model-invocation: true
---

Run every check below. Report pass or fail for each, fix what you can, then re-check.

## Repo
- [ ] Fresh clone works: clone main into a temp dir, `uv sync`, start the app. Report any error.
- [ ] Nothing in data/raw, no secrets, no `.env`, no file over 50 MB is tracked (`git ls-files` plus sizes).
- [ ] main has everyone's latest work merged.

## App
- [ ] Starts clean: `uv run streamlit run app/app.py --server.headless true --server.port 8599`, then `curl -s localhost:8599/_stcore/health` returns ok. Check the log for errors or warnings. Stop the server after.
- [ ] Uses only data in the repo (app/data/) or data it downloads. No teammate-local paths.
- [ ] `requirements.txt` is current: `uv export --no-dev --no-hashes -o requirements.txt`.
- [ ] Deployed URL, if any, loads.

## README (judges read this)
- [ ] Opening paragraph: problem, what we built, the key insight with a number.
- [ ] Datasets used and how they were combined.
- [ ] Setup and run steps, verified by the fresh-clone check above.
- [ ] 2 or 3 example use cases.
- [ ] Every number matches FINDINGS.md.
- [ ] Images and figures render.

## Submission
- [ ] Video is under the time limit, shows the app working, and states the insight in the first 20 seconds.
- [ ] Devpost: all teammates added, correct challenges selected, repo link public or shared with judges.

Finish with the 3 riskiest remaining issues.
