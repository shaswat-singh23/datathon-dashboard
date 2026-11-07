"""Decision summaries over committed marts, without raw data or model refitting."""
import calendar

import pandas as pd

from royale import money


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
