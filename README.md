# The Gilded Ace: luck, location, or a leak?

Management wants to replace the lowest-earning machines. Our Streamlit dashboard compares the manager's picks with adjusted machine rankings, investigates luck, location and downtime, prices a July action plan and evaluates a demand forecast. **Provisional headline:** Back Forty coin-in per available machine-hour fell from **$135.5 before the walkway closure to $96.3 during it**, while the rest of the floor went from **$206.1 to $210.7** ([finding, comparison windows and queries](findings/16-demand-changes.md)). This descriptive result is awaiting independent review; it supports investigating access before blaming machines, rather than establishing a causal effect.

[![Provisional demand comparison: Back Forty and the rest of the floor before, during and after the walkway closure; independent review pending.](figures/headline.png)](figures/README.md)

## Live dashboard

Public URL: PENDING. Deployment runbook, verification and the URL once live: [findings/24-deploy.md](findings/24-deploy.md). Until then, run locally using the instructions below.

## What we built

An interactive dashboard over a fictional casino's synthetic gaming, operations and guest records. Pages read committed derived parquet marts, so viewing the app does not require raw data. Machines, Demand, Downtime, Players, Comps, Actions and Model are implemented. Use each page's period filter, drill controls and source expander to trace the analysis. Implementation is complete for these pages; analytical findings remain provisional until independently checked.

### Machines: which underperform after adjustment?

Open **Machines** to compare the manager's bottom ten by total house win with expected contribution per available hour, then change the period or drill into a bank. Explore the variance-adjusted payout screen and same-game location comparisons. Rankings are descriptive screens; they establish neither a replacement benefit nor wrongdoing. Provisional evidence awaiting independent review: [rankings and baseline](findings/22-machines.md), [location comparisons](findings/31-location.md) and [payout screen](findings/32-leak-screen.md).

### Demand: what changed across the floor?

Open **Demand**, change the period and drill into Back Forty to examine the walkway closure alongside floor demand. The headline above uses before/during/after windows and the rest of the floor as a comparison. Machine mix and renovation effects remain alternative explanations. [Evidence and limitations](findings/16-demand-changes.md).

### Downtime: how much availability was lost?

Open **Downtime** to compare lost hours, estimated lost play and repair patterns by manufacturer, bank or zone. Lost-play estimates use the same machine's available-hour play rate within the month; guest substitution can reduce the recoverable opportunity. [Evidence and baseline](findings/17-downtime.md).

### Players: what did tracked guests experience?

Open **Players** to inspect wagers, payouts, net outcomes and concentration against an equal-share baseline, then drill into a guest group. Carded records do not describe uncarded guests; wagers include replayed winnings and are not cash spent. These summaries are for understanding outcomes, never for encouraging heavy losers to play more. [Evidence and definitions](findings/18-player-outcomes.md).

### Comps: what did loyalty rewards cost?

Open **Comps** to compare economic cost with menu value, inspect redemption intensity over time and drill by opening tier or home region. The baseline is earlier-period redemption intensity. Comp costs are already inside POS cost of goods sold and must be subtracted only once. [Evidence and reconciliation](findings/19-comps.md).

### Actions: what should management fund?

Open **Actions** to inspect the proposed payout/configuration inspection and compare its price and downtime with preserving all funds, preventive maintenance and extra technician coverage. Change the evidence period, drill into an option and trace its measurement plan and source findings. Recovery scenarios are assumptions, and the monetary comparison favors preserving all funds; the inspection buys information without an estimated positive revenue recovery. The recommendation remains provisional pending independent review. [Plan, prices, baselines and limitations](findings/23-july-actions.md).

### Model and validation

Open **Model** to compare a fitted weekday-plus-trend regression with constant and weekday-mean baselines. Training uses January–April; frozen forecasts are evaluated on May–June using mean absolute error. Change the evaluation period to recalculate selected-period scores and drill into errors by month or weekday. Inputs use calendar dates only. The weekday-mean baseline has the lowest observed holdout error; future superiority is unproven. [Evaluation, target reconciliation and limitations](findings/47-forecast-evaluation.md) remain provisional pending independent review.

## Data and analytical approach

Source: the organizer's [Dashboard Royale repository](https://github.com/tamu-datathon-org/dashboard-royale); start with its GUIDE.md and data dictionary. Prepared daily/property views and player-period records are supplemented by machine placements, game math, calendar, operations, traffic and loyalty records. Raw data stays outside version control; builders read it through `DATA_DIR`.

Money calculations use `royale/money.py`: aggregate ratios use sums, theoretical win uses configured game RTP, and luck is observed house win minus theoretical win. Machine comparisons exclude off-floor records, follow dated placements and use available hours. Contextual associations are descriptive; unusual payouts are inspection leads, not accusations.

All linked findings currently await independent review. The [Claims & Evidence appendix](docs/claims_evidence.md) lists every claim on the README or a page with its table or query, result, alternative explanation and limitation, and tracks each one's review status. The [AI-use disclosure](docs/ai_disclosure.md) states which tools the team used and for what.

## Setup and run

These commands follow [SETUP.md — Stack setup](SETUP.md#stack-setup). Install git and [uv](https://docs.astral.sh/uv/getting-started/installation/) first. From a fresh checkout:

```bash
git clone https://github.com/shaswat-singh23/datathon-dashboard.git
cd datathon-dashboard
uv sync
uv run pytest -q
uv run streamlit run app.py
```

The app uses the committed `marts/`. To rebuild them, stop Streamlit and fetch the organizer data:

```bash
git clone --depth 1 https://github.com/tamu-datathon-org/dashboard-royale.git
cp .env.example .env
# Edit .env: set DATA_DIR to the absolute path of dashboard-royale/data.
uv run python -m royale.build
uv run pytest -q
uv run streamlit run app.py
```

Data-dependent tests skip when raw data is unavailable. Never commit raw data or secrets. Dependencies and the Python requirement are declared in [pyproject.toml](pyproject.toml) and locked in [uv.lock](uv.lock).

## Team workflow

[AGENTS.md](AGENTS.md) defines issue scope, review and evidence rules; [PLAYBOOK.md](PLAYBOOK.md) describes team coordination. Findings must be independently checked before submission claims are finalized.
