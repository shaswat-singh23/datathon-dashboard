# Public dashboard on Streamlit Community Cloud
- Issue: #24 | Author: Kyle | Time: 15:05
- Claim: the dashboard deploys from `master` with committed marts only; no raw data, secrets or `DATA_DIR` are needed on the server.
- Evidence: with `DATA_DIR` pointed at an empty directory, `app.py` and all 7 pages in `pages/` render with zero exceptions under Streamlit AppTest, on both Python 3.13 (local) and Python 3.12 (Community Cloud default) using the locked dependency set (`uv sync --locked --python 3.12`: 45 packages). Script: the Reproduce block below, result `FAILURES 0` on both versions. `marts/` is 12 MB across 11 parquet files, each under 5 MB.
- So what: judges open one link and every page works; the organizer data never leaves our machines.
- Checked by: unchecked

## Reproduce

Pages are opened through `app.py` and `switch_page`, which is how Community Cloud serves them. Run standalone, `pages/6_actions.py` raises `StreamlitPageNotFoundError` from `st.page_link` under AppTest; that is a test-harness artifact, not a deploy bug.

```python
# Save anywhere as smoke.py, then from the repo root: uv run python smoke.py
# (DATA_DIR is overridden below; AppTest needs absolute paths)
import os, sys, tempfile
from pathlib import Path
os.environ["DATA_DIR"] = tempfile.mkdtemp()      # no raw data, like Community Cloud
from streamlit.testing.v1 import AppTest
root = Path.cwd()
failures = 0
at = AppTest.from_file(str(root / "app.py"), default_timeout=120).run()
print("app.py", "ok" if not at.exception else "FAIL")
failures += bool(at.exception)
for page in sorted((root / "pages").glob("*.py")):
    at = AppTest.from_file(str(root / "app.py"), default_timeout=120).run()
    at.switch_page(f"pages/{page.name}").run()
    bad = list(at.exception) + list(at.error)
    failures += bool(bad)
    print(page.name, "ok" if not bad else "FAIL", [str(b.value)[:200] for b in bad])
print("FAILURES", failures)
sys.exit(1 if failures else 0)
```

For the Python 3.12 run: `UV_PROJECT_ENVIRONMENT=/tmp/venv312 uv sync --locked --python 3.12`, then the same script with `uv run --python 3.12 --locked`.

## Live URL

- Public URL: https://datathon-dashboard-o5xb3rbuuqzppphcqeglmq.streamlit.app/ (deployed from `master`, `app.py`; first linked in PR #71, live by 22:42 UTC). Anonymous `curl -L` with a cookie jar: HTTP 200 after 3 redirects, Community Cloud app shell.
- First deploy verified in a private window: PENDING
- Redeploy on push to master confirmed: PENDING

## How it is deployed

Community Cloud has no API or CLI; the first deploy is a browser click-through by a GitHub collaborator on `shaswat-singh23/datathon-dashboard`.

The repo is **private** and owned by Shaswat. Community Cloud can deploy a private repo only if the repo owner authorizes the Streamlit GitHub app for private repositories (one private app per free account), so step 1 is best done by Shaswat, or the repo is made public first. Either way, set the app to **Public** under Sharing after deploy so judges need no login.

1. Sign in at https://share.streamlit.io with GitHub (allow access to the `shaswat-singh23` org if asked).
2. Create app, "Deploy a public app from GitHub".
3. Repository `shaswat-singh23/datathon-dashboard`, branch `master`, main file path `app.py`.
4. App URL: pick a readable subdomain, for example `gilded-ace`.
5. Advanced settings: Python version **3.12** (matches `.python-version`). No secrets are needed.
6. Deploy. Dependencies install from `uv.lock` with uv (Community Cloud picks the first dependency file it finds, and `uv.lock` has priority). First build takes a few minutes.
7. Open the URL in a private window. Click each sidebar page and change one period filter per page.
8. Record the URL here and in README.md under "Live dashboard".
9. Redeploy check: after the next merge to master, reload the URL. Community Cloud redeploys on every push to the deployed branch; the app menu (bottom right) shows the commit. Record the commit SHA and time here.

## Why these files

- `.python-version` = 3.12: the one Python version everywhere (local uv, the runbook, and the Advanced-settings dropdown). `pyproject.toml` and `uv.lock` are unchanged; the universal lock installs on 3.12 and 3.13.
- `.streamlit/config.toml`: theme, headless server, usage stats off. Already present; unchanged.
- `uv.lock`: the server installs exactly what we test locally.

## Limitations

- Community Cloud apps sleep after inactivity on the free tier; the first visit after sleep takes about a minute to wake. Open the link before the demo.
- The deploy is tied to the GitHub account that created it; a second collaborator should be added as an app owner in the Community Cloud workspace settings so the app survives one person's absence.
