"""Decision summaries over committed marts, without raw data or model refitting."""
import calendar
import re

import pandas as pd

from royale import budget, config, money
from royale.evidence import read_document
from royale.marts.q6_actions import proposed_plan

# Fixed full-period evidence for Home. Every number is copied from the cited finding;
# the card shows that finding's own "Checked by" line rather than a claimed status.
EVIDENCE_CARDS = (
    dict(title="8/10 remain in the adjusted bottom ten",
         body="Eight of the manager's ten lowest-house-win machines still rank in the bottom ten by "
              "expected contribution per available hour.",
         caveat="Descriptive screening: it does not show that a replacement would earn more.",
         findings=("findings/22-machines.md",), page="pages/1_machines.py", link="Machines: rank comparison"),
    dict(title="Back Forty shows an access association",
         body="Back Forty demand fell about 30% while the Main Entrance–Back Forty walkway was closed "
              "(Mar 3–Apr 6), then mostly returned. Nine of the manager's ten picks sit in Back Forty.",
         caveat="Observational association, not a causal estimate of earnings lost to location.",
         findings=("findings/16-demand-changes.md", "findings/31-location.md"), page="pages/2_demand.py", link="Demand: closure comparison"),
    dict(title="M-1158 merits inspection",
         body="One of 310 active machines, M-1158, has configured RTP outside its observed-payout interval "
              "at ±3.8 standard errors; it is second-lowest on the manager's ranking.",
         caveat="An inspection lead, not proof of a leak or wrongdoing.",
         findings=("findings/32-leak-screen.md",), page="pages/1_machines.py", link="Machines: payout screen"),
)


def select_machine_days(data, start, end, bank="All banks"):
    dates = pd.to_datetime(data.gaming_date).dt.date
    selected = data.loc[dates.between(start, end)]
    if bank != "All banks":
        selected = selected.loc[selected.bank_id == bank]
    return selected


def period_totals(data):
    """Use the same on-floor population for dollars and exposure denominators."""
    return {
        "coin_in": money.cents_to_usd(data.coin_in_cents.sum()),
        "house_win": money.cents_to_usd(data.house_win_cents.sum()),
        "theo": money.cents_to_usd(data.theo_cents.sum()),
        "hold": money.hold(data.house_win_cents, data.coin_in_cents),
        "availability": money.availability(data.available_seconds, data.scheduled_seconds),
        "available_hours": data.available_seconds.sum() / 3600,
        "scheduled_hours": data.scheduled_seconds.sum() / 3600,
    }


def rank_stability(data, machine_ids):
    """Delete each complete month in turn; report descriptive rank sensitivity.

    This is neither a confidence interval nor an estimate of replacement uplift.
    At least three complete months are needed. Any partial boundary months stay
    in the evidence; zero-exposure machines are unranked in that deletion run.
    """
    dates = pd.to_datetime(data.gaming_date)
    months = dates.dt.to_period("M")
    complete = [m for m in sorted(months.unique())
                if m.start_time.date() >= dates.min().date()
                and m.end_time.date() <= dates.max().date()]
    if len(complete) < 3:
        return pd.DataFrame()

    def ranks(rows):
        totals = rows.groupby("machine_id", sort=True)[["theo_cents", "supplied_cost_usd", "available_seconds"]].sum()
        rates = pd.Series({machine: money.per_available_hour(
            money.cents_to_usd(row.theo_cents) - row.supplied_cost_usd,
            row.available_seconds / 3600,
        ) for machine, row in totals.iterrows()}, dtype=float)
        return rates.dropna().rank(method="first").astype(int)

    full = ranks(data)
    deleted = pd.DataFrame({str(month): ranks(data.loc[months != month]) for month in complete})
    result = pd.DataFrame(index=pd.Index(machine_ids, name="machine_id"))
    result["full_adjusted_rank"] = full.reindex(result.index)
    runs = deleted.reindex(result.index)
    result["lowest_rank"] = runs.min(axis=1)
    result["highest_rank"] = runs.max(axis=1)
    result["bottom_ten_runs"] = (runs <= 10).sum(axis=1)
    result["testable_runs"] = runs.notna().sum(axis=1)
    result["complete_months"] = len(complete)
    return result


def weekday_profile(forecasts):
    """Read frozen training means, ignoring all observed holdout outcomes."""
    profile = forecasts[["gaming_date", "weekday_prediction_usd", "constant_prediction_usd"]].copy()
    profile["weekday_number"] = pd.to_datetime(profile.gaming_date).dt.day_of_week
    profile = profile.groupby("weekday_number")[["weekday_prediction_usd", "constant_prediction_usd"]].first()
    profile["vs_constant"] = profile.weekday_prediction_usd / profile.constant_prediction_usd.replace(0, float("nan")) - 1
    profile.index = [calendar.day_name[day] for day in profile.index]
    profile.index.name = "Weekday"
    return profile


def checked_by(finding):
    """The finding's own review line, verbatim; "unchecked" when absent or blank."""
    match = re.search(r"^- Checked by:\s*(.*)$", read_document(finding), re.M)
    return match.group(1).strip() if match and match.group(1).strip() else "unchecked"


def july_decision(actions):
    """Fixed July plan from the complete January–June record; never takes a historical filter."""
    catalog = actions.loc[actions.record_type == "catalog"]
    plan = proposed_plan(actions)
    violations = budget.validate_plan(catalog, plan)
    cost = budget.plan_cost_usd(catalog, plan)
    return dict(plan=plan, violations=violations, cost=cost, retained=config.BUDGET_USD - cost,
                inspections=sum(line.quantity for line in plan if line.action_type_id == "A-INSPECT"),
                targets=[target for line in plan for target in line.targets])
