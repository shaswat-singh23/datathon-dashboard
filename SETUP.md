# Setup (do tonight, about 15 minutes)

## 1. Everyone
1. Install git and VS Code.
2. Install uv:
   - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
3. Accept the GitHub invite, then:
   ```bash
   git clone <repo-url> && cd <repo>
   uv sync                                # installs Python 3.12 and every package
   uv run python scripts/verify_env.py    # every line should say PASS
   ```
   macOS: if lightgbm fails, run `brew install libomp` and rerun.
4. Open the folder in VS Code. When it asks for an interpreter, pick `.venv`.
5. Join the Devpost team, the Discord channel, and the Drive folder.

Venue wifi will be bad. Doing this tonight is the point.

## 2. AI tools
- **Claude Code (VS Code):** Extensions view, search "Claude Code", install the one by Anthropic, sign in. Open this repo folder and trust it when asked. Repo skills: `/triage`, `/eda`, `/baseline`, `/ship-check`.
- **Cursor, Copilot, Codex:** they read `AGENTS.md`. Nothing to do.
- **ChatGPT or claude.ai in a browser:** paste `AGENTS.md` at the start of the chat.

Whatever tool you use, the rules in AGENTS.md apply. The two that matter most: print row counts around every join, and compare every model to a naive baseline.

## 3. Dry run (Claude driver, 10 minutes)
```bash
uv run python scripts/make_sample_data.py
```
In Claude Code:
1. `/eda data/raw/_sample`
2. `/baseline units sales`
3. Check the answer key below. Did it catch all 5? If not, tighten the skill.
4. `rm -rf data/raw/_sample EDA.md src/models/baseline_units.py` and reset FINDINGS.md.

## 4. Deploy once tonight
1. Push to GitHub.
2. share.streamlit.io, then Create app. Repo: this one, branch `main`, file `app/app.py`.
3. It installs from `app/requirements.txt`. After adding a package the app needs, add it there too, or regenerate:
   `uv export --no-dev --no-hashes --no-emit-project -o app/requirements.txt`
4. The deployed app only sees `app/data/`. With no data it shows a "No data found" message. That's expected.

## Git cheat sheet
```bash
git switch -c <name>/<topic>            # start work
git add -A && git commit -m "what"      # save
git pull origin main                    # get teammates' work into your branch
git push -u origin HEAD                 # share; merge to main on GitHub
```
Conflict? Ask the Claude driver. Don't force-push.

## Dry-run answer key
1. products.csv has a duplicated product_id (17). A naive sales-products join fans out rows.
2. sales.revenue = units * price. It leaks the target when predicting units.
3. price has -1 sentinels. units has negatives (returns).
4. store 9 is in sales but not in stores.csv.
5. store 3 has no sales from Mar 4 to Mar 27.
