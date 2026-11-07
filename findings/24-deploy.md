# Public dashboard on Streamlit Community Cloud
- Issue: #24 | Author: Kyle | Time: 15:05
- Claim: the dashboard deploys from `master` with committed marts only; no raw data, secrets or `DATA_DIR` are needed on the server.
- Evidence: with `DATA_DIR` pointed at an empty directory, `app.py` and all 7 pages in `pages/` render with zero exceptions under Streamlit AppTest, on both Python 3.13 (local) and Python 3.12 (Community Cloud default) using the locked dependency set (`uv sync --locked --python 3.12`: 45 packages). Script: `smoke_pages.py` (session scratchpad), result `FAILURES 0`. `marts/` is 12 MB across 11 parquet files, each under 5 MB.
- So what: judges open one link and every page works; the organizer data never leaves our machines.
- Checked by: unchecked

## Live URL

- Public URL: PENDING (fill in after the click-through below; also fill the "Live dashboard" line in README.md)
- First deploy verified in a private window: PENDING
- Redeploy on push to master confirmed: PENDING

## How it is deployed

Community Cloud has no API or CLI; the first deploy is a browser click-through by a GitHub collaborator on `shaswat-singh23/datathon-dashboard`.

1. Sign in at https://share.streamlit.io with GitHub (allow access to the `shaswat-singh23` org if asked).
2. Create app, "Deploy a public app from GitHub".
3. Repository `shaswat-singh23/datathon-dashboard`, branch `master`, main file path `app.py`.
4. App URL: pick a readable subdomain, for example `gilded-ace`.
5. Advanced settings: Python version **3.12** (matches `.python-version`). No secrets are needed.
6. Deploy. Dependencies install from `uv.lock` with uv (Community Cloud picks the first dependency file it finds, and `uv.lock` has priority). First build takes a few minutes.
7. Open the URL in a private window. Click each sidebar page and change one period filter per page.
8. Record the URL here and in README.md under "Live dashboard".
9. Redeploy check: after the next merge to master, reload the URL. Community Cloud redeploys on every push to the deployed branch; the app menu (bottom right) shows the commit. Record the date here.

## Why these files

- `.python-version` = 3.12: pins the interpreter for uv locally and documents the version to select on Community Cloud.
- `.streamlit/config.toml`: theme, headless server, usage stats off. Already present; unchanged.
- `uv.lock`: the server installs exactly what we test locally.

## Limitations

- Community Cloud apps sleep after inactivity on the free tier; the first visit after sleep takes about a minute to wake. Open the link before the demo.
- The deploy is tied to the GitHub account that created it; a second collaborator should be added as an app owner in the Community Cloud workspace settings so the app survives one person's absence.
