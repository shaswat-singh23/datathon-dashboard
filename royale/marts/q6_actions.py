"""July decisions, with catalogue prices and historical evidence in one mart.

Effects of interventions are not identified by these observational data. The
downtime alternatives therefore use explicit 0/50/100% recovery scenarios, not
confidence intervals or fitted treatment effects. Inspection buys information;
no recovery of historical payout residuals is booked as future revenue.
"""
from __future__ import annotations

import pandas as pd

from royale import budget, money
from royale.marts import q1_machines, q3_downtime

NAME = "q6_actions"
SCREEN_Z = -3.8


def build(con) -> pd.DataFrame:
    md = q1_machines.build(con)
    before = len(md)
    makers = con.sql("SELECT machine_id, manufacturer FROM machines").df()
    md = md.merge(makers, on="machine_id", validate="many_to_one")
    assert len(md) == before
    md["record_type"] = "machine_day"

    tickets = con.sql(q3_downtime.TICKET_SQL).df()
    n_ops = con.sql("SELECT count(*) FROM operations").fetchall()[0][0]
    assert len(tickets) == n_ops
    assert tickets.operation_id.is_unique
    faults = tickets.loc[tickets.event_type == "fault_repair", [
        "gaming_date", "machine_id", "manufacturer", "bank_id", "operation_id",
        "shift", "wait_h", "fix_h", "response_h",
    ]].copy()
    assert (faults[["wait_h", "fix_h"]] >= 0).all().all()
    faults["record_type"] = "fault"

    catalog = con.sql("SELECT * FROM action_catalog").df()
    assert catalog.action_type_id.is_unique
    catalog["one_unit_cost_usd"] = [
        budget.line_cost_usd(catalog, budget.ActionLine(a, 1)) for a in catalog.action_type_id
    ]
    catalog["operating_days"] = [budget.effective_days(catalog, a) for a in catalog.action_type_id]
    catalog["record_type"] = "catalog"
    n_off = con.sql("SELECT count(*) FROM machine_day WHERE location_id IS NULL").fetchall()[0][0]
    audits = pd.DataFrame([
        dict(audit_table="active on-floor machine-day joins", rows_before=before,
             rows_after=len(md), excluded_off_floor=n_off),
        dict(audit_table="operation joins (before fault filter)", rows_before=n_ops,
             rows_after=len(tickets), excluded_off_floor=0),
    ])
    audits["record_type"] = "audit"
    return pd.concat([md, faults, catalog, audits], ignore_index=True)


def machine_summary(md: pd.DataFrame) -> pd.DataFrame:
    """Raw manager ranking and payout screen, recalculated from sufficient stats."""
    rows = []
    for machine, d in md.groupby("machine_id", sort=True):
        theo = money.cents_to_usd(d.theo_cents.sum())
        hours = d.available_seconds.sum() / 3600
        rows.append(dict(
            machine_id=machine, manufacturer=d.manufacturer.iloc[0],
            days=len(d), available_h=hours,
            house_win_usd=money.cents_to_usd(d.house_win_cents.sum()), theo_usd=theo,
            theo_per_h=money.per_available_hour(theo, hours),
            luck_z=money.luck_z(d.house_win_cents, d.theo_cents,
                              d.sum_bet_squared, d.payout_multiplier_variance),
        ))
    result = pd.DataFrame(rows).set_index("machine_id")
    result["raw_rank"] = result.house_win_usd.rank(method="first").astype(int)
    return result


def proposed_plan(data: pd.DataFrame) -> list[budget.ActionLine]:
    """Freeze targets from the complete Jan–Jun record, regardless of UI filters."""
    md = data[data.record_type == "machine_day"]
    ranked = machine_summary(md)
    current = set(md.loc[md.gaming_date == md.gaming_date.max(), "machine_id"])
    catalog = data[data.record_type == "catalog"]
    limit = int(catalog.set_index("action_type_id").loc["A-INSPECT", "quantity_limit"])
    targets = ranked.loc[
        (ranked.raw_rank <= 10) & (ranked.luck_z < SCREEN_Z) & ranked.index.isin(current)
    ].sort_values(["luck_z", "raw_rank"]).head(limit).index.tolist()
    return [budget.ActionLine("A-INSPECT", len(targets), targets)] if targets else []


def assess(data: pd.DataFrame, start=None, end=None) -> tuple[pd.DataFrame, dict]:
    """Compare fixed July options using the selected historical period as exposure.

    Net is incremental theo less catalogue spend and implementation downtime,
    relative to doing nothing. It is not a full-profit or causal forecast.
    Halving affects the assumed positive recovery, leaving fixed costs intact.
    """
    full = data.loc[data.record_type == "machine_day"].copy()
    full["gaming_date"] = pd.to_datetime(full.gaming_date)
    start = pd.Timestamp(start) if start is not None else full.gaming_date.min()
    end = pd.Timestamp(end) if end is not None else full.gaming_date.max()
    md = full[full.gaming_date.between(start, end)].copy()
    if md.empty:
        raise ValueError("No on-floor machine-days in the selected period")
    faults = data.loc[data.record_type == "fault"].copy()
    faults["gaming_date"] = pd.to_datetime(faults.gaming_date)
    faults = faults[faults.gaming_date.between(start, end)]
    catalog = data[data.record_type == "catalog"].set_index("action_type_id", drop=False)
    plan = proposed_plan(data)
    inspection_ids = plan[0].targets if plan else []
    summary = machine_summary(md)
    rates = summary.theo_per_h.dropna()
    days = (end - start).days + 1
    md["lost_h"] = (md.scheduled_seconds - md.available_seconds) / 3600

    # Manufacturer choice and July footprint are fixed using all available history.
    maker = full.groupby("manufacturer")[["scheduled_seconds", "available_seconds"]].sum()
    maker["lost_share"] = 1 - maker.available_seconds / maker.scheduled_seconds
    manufacturer = maker.lost_share.idxmax()
    current = full[full.gaming_date == full.gaming_date.max()]
    maintenance_ids = current.loc[current.manufacturer == manufacturer, "machine_id"].tolist()
    history = md[md.machine_id.isin(maintenance_ids)]
    # A per-machine daily rate handles installs/retirements without treating them as outages.
    daily_lost = history.groupby("machine_id").agg(lost_h=("lost_h", "sum"), days=("gaming_date", "size"))
    daily_lost["theo_per_h"] = daily_lost.index.map(rates)
    maintenance_daily = (daily_lost.lost_h / daily_lost.days * daily_lost.theo_per_h).sum()
    maintenance_down = (float(catalog.loc["A-PREVENTIVE", "downtime_minutes"]) / 60
                        * rates.reindex(maintenance_ids).sum())
    maintenance_headroom = maintenance_daily * int(catalog.loc["A-PREVENTIVE", "operating_days"])

    grave = faults[faults["shift"] == "grave"]
    others = faults[faults["shift"] != "grave"]
    # An extra grave technician could at most remove all observed waiting, not repair time.
    tech_daily = (grave.wait_h * grave.machine_id.map(rates)).sum() / days
    tech_headroom = tech_daily * int(catalog.loc["A-TECH-SHIFT", "operating_days"])
    inspection_down = (float(catalog.loc["A-INSPECT", "downtime_minutes"]) / 60
                       * rates.reindex(inspection_ids).sum())
    inspection_low = 0.0
    for machine in inspection_ids:
        d = md[(md.machine_id == machine) & (md.available_seconds > 0)]
        daily_rates = [money.per_available_hour(money.cents_to_usd(t), a / 3600)
                       for t, a in zip(d.theo_cents, d.available_seconds)]
        if daily_rates:
            inspection_low -= float(catalog.loc["A-INSPECT", "downtime_minutes"]) / 60 * pd.Series(daily_rates).quantile(.9)

    rows = []

    def option(action, quantity, targets, low, base, high, half, recovery, down, sample):
        line = budget.ActionLine(action, quantity, targets)
        cost = budget.line_cost_usd(catalog.reset_index(drop=True), line)
        rows.append(dict(action_type_id=action, action=catalog.loc[action, "name"],
                         quantity=quantity, targets=", ".join(targets), cost_usd=cost,
                         operating_days=int(catalog.loc[action, "operating_days"]),
                         low_theo_usd=low, base_theo_usd=base, high_theo_usd=high,
                         half_theo_usd=half, net_usd=base-cost, half_net_usd=half-cost,
                         low_net_usd=low-cost, high_net_usd=high-cost,
                         recovery_headroom_usd=recovery, implementation_theo_usd=down,
                         evidence_rows=sample))

    option("A-HOLD", 1, ["Unspent July budget"], 0, 0, 0, 0, 0, 0, len(md))
    if inspection_ids:
        option("A-INSPECT", len(inspection_ids), inspection_ids,
               min(inspection_low, -inspection_down), -inspection_down, 0,
               -inspection_down, 0, inspection_down, int(md.machine_id.isin(inspection_ids).sum()))
    option("A-PREVENTIVE", 1, [manufacturer], -maintenance_down,
           .5*maintenance_headroom-maintenance_down, maintenance_headroom-maintenance_down,
           .25*maintenance_headroom-maintenance_down,
           maintenance_headroom, maintenance_down, len(history))
    option("A-TECH-SHIFT", 1, ["grave (22:00–06:00)"], 0, .5*tech_headroom,
           tech_headroom, .25*tech_headroom, tech_headroom, 0, len(grave))
    options = pd.DataFrame(rows)
    options["rank_base"] = options.net_usd.rank(ascending=False, method="min").astype(int)
    options["rank_half"] = options.half_net_usd.rank(ascending=False, method="min").astype(int)
    evidence = dict(
        start=start.date(), end=end.date(), days=days, machines=summary,
        manufacturer=manufacturer, maintenance_targets=maintenance_ids,
        maintenance_covered=len(set(maintenance_ids) & set(rates.index)),
        grave_tickets=len(grave), grave_wait_h=None if grave.empty else grave.wait_h.mean(),
        other_wait_h=None if others.empty else others.wait_h.mean(),
        grave_rate_coverage=int(grave.machine_id.isin(rates.index).sum()),
        inspection_targets=inspection_ids,
        inspection_covered=len(set(inspection_ids) & set(rates.index)),
    )
    return options.sort_values(["rank_base", "action_type_id"]), evidence
