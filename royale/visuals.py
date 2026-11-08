"""Decision visuals built only from existing analytical outputs.

Every function here reshapes a result that another module already computed:
``q1_machines.summarize`` ranks, the ``q2_demand`` closure labels, ``q6_actions.assess``
options and ``model.score_forecasts`` errors. No financial definition is recomputed and
no forecast is fitted. Figures use the theme palette and leave styling to the template.
"""
from __future__ import annotations

import math
import re

import pandas as pd
import plotly.graph_objects as go

from royale import budget, config, money
from royale.theme import ADVERSE, BRASS, PALETTE, short_usd

# Data colors are distinct series; gold (BRASS) only marks emphasis; red (ADVERSE) only adverse outcomes.
GREEN, BLUE, OCHRE, PLUM, UMBER = PALETTE[:5]
INK = "#332D27"
RULE = "#6A5F52"     # reference lines and boundaries
MUTED = "#968A7A"    # de-emphasized series, >= 3:1 on the chart paper


def label(fig: go.Figure, title: str, x: str | None = None, y: str | None = None) -> go.Figure:
    """Accessibility labels: set a chart title and axis titles, replacing only missing or raw column-name axis titles."""
    def has(t):
        t = getattr(t, "text", t)
        return bool(t)
    def raw(t):
        # Plotly Express fills axis titles with column names such as "month" or "value".
        return bool(re.fullmatch(r"[a-z0-9_]+", getattr(t, "text", t) or ""))
    if not has(fig.layout.title):
        top = max(fig.layout.margin.t or 0, 48)
        fig.update_layout(title=dict(text=title, x=0.02, xanchor="left", font=dict(size=14)),
                          margin=dict(t=top))
    if x and (not has(fig.layout.xaxis.title) or raw(fig.layout.xaxis.title)):
        fig.update_xaxes(title=x)
    if y and (not has(fig.layout.yaxis.title) or raw(fig.layout.yaxis.title)):
        fig.update_yaxes(title=y)
    return fig


def usd(value: float) -> str:
    """Whole dollars with the sign before the symbol: −$5,330."""
    return f"{'−' if value < 0 else ''}${abs(value):,.0f}"

# ---- Machines: manager rank -> adjusted rank ------------------------------------------------


def slope_table(ranked: pd.DataFrame, picks: int = 10) -> pd.DataFrame:
    """Manager's bottom picks with both ranks, read straight from ``summarize`` output.

    A pick is emphasized when adjustment moves it out of the adjusted bottom ``picks``;
    over the full period that is exactly M-1158 and M-1118.
    """
    table = ranked.sort_values("raw_rank").head(picks)[["raw_rank", "adjusted_rank"]].copy()
    table["rank_shift"] = table.adjusted_rank - table.raw_rank
    table["leaves_bottom_ten"] = table.adjusted_rank > picks
    table.index.name = "machine_id"
    return table


SLOPE_X = ["Manager rank<br>(lowest total house win)",
           "Adjusted rank<br>(lowest expected contribution / available hour)"]


def slope_chart(table: pd.DataFrame) -> go.Figure:
    """Labeled slope chart; points are the table's ranks, rank 1 at the top (log scale)."""
    fig = go.Figure()
    for machine, row in table.iterrows():
        loud = bool(row.leaves_bottom_ten)
        fig.add_trace(go.Scatter(
            x=SLOPE_X,
            y=[row.raw_rank, row.adjusted_rank], mode="lines+markers+text", name=machine,
            text=["", f"{machine} · #{int(row.adjusted_rank)}"], textposition="middle right",
            line=dict(color=BRASS if loud else MUTED, width=3.5 if loud else 1.5),
            marker=dict(size=10 if loud else 7, color=BRASS if loud else MUTED),
            textfont=dict(color=BRASS if loud else INK, size=13 if loud else 11),
            hovertemplate=f"{machine}<br>%{{x}}: #%{{y}}<extra></extra>", showlegend=False,
        ))
    # A boundary trace, not a layout shape: shapes on log axes are easy to misplace.
    fig.add_trace(go.Scatter(x=SLOPE_X, y=[10.5, 10.5], mode="lines+text", name="Bottom-ten boundary",
                             meta="boundary", line=dict(color=RULE, dash="dash", width=1),
                             text=["Bottom ten above this line", ""], textposition="top right",
                             textfont=dict(color=RULE, size=11), hoverinfo="skip", showlegend=False))
    top = math.log10(0.8)
    fig.update_yaxes(type="log", range=[math.log10(max(table.adjusted_rank.max(), 10) * 1.4), top],
                     title="Rank among machines (1 = lowest)",
                     tickvals=[1, 2, 5, 10, 20, 50, 100, 200, 300], zeroline=False)
    fig.update_xaxes(showgrid=False)
    fig.update_layout(height=420, margin=dict(l=10, r=160, t=30, b=10))
    return label(fig, "Manager bottom ten: raw rank vs exposure-adjusted rank", "Ranking basis", "Rank (1 = lowest)")


# ---- Demand: Back Forty vs rest of floor around the closure --------------------------------

PHASES = ("Before closure", "During closure", "After closure")
FOCUS_ZONE = "Z-B40"


def closure_window(demand: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """First and last gaming days carrying the walkway closure label, from the full mart."""
    dates = pd.to_datetime(demand.loc[demand.closures_active.notna(), "gaming_date"])
    return (dates.min(), dates.max()) if len(dates) else None


def closure_comparison(view: pd.DataFrame, window: tuple[pd.Timestamp, pd.Timestamp] | None,
                       zone: str = FOCUS_ZONE) -> tuple[pd.DataFrame, str | None]:
    """Coin-in per available machine-hour (ratio of sums) by closure phase and area.

    ``window`` is the actual closure from the full record; ``view`` is the user's selection.
    Returns the table and, when the selection cannot support a before/during/after
    comparison, the reason. The full period is never substituted silently.
    """
    columns = ["phase", "area", "days", "coin_in_usd", "available_hours", "coin_in_per_available_hour",
               "zone_entries", "covered_sensor_hours", "entries_per_covered_hour"]
    if window is None:
        return pd.DataFrame(columns=columns), "The mart records no walkway closure."
    start, end = window
    dates = pd.to_datetime(view.gaming_date)
    phase = pd.Series(PHASES[1], index=view.index)
    phase[dates < start] = PHASES[0]
    phase[dates > end] = PHASES[2]
    frame = view.assign(phase=phase, area=view.zone_id.eq(zone).map(
        {True: "Back Forty", False: "Rest of floor"}))
    usable = (frame.zone_entries_observed.notna() & frame.zone_counter_coverage_hours.notna()
              & frame.zone_counter_coverage_hours.gt(0))
    frame = frame.assign(covered=frame.zone_counter_coverage_hours.where(usable, 0),
                         entries=frame.zone_entries_observed.where(usable, 0))
    rows = []
    for (ph, area), g in frame.groupby(["phase", "area"], sort=False):
        rows.append(dict(phase=ph, area=area, days=g.gaming_date.nunique(),
                         coin_in_usd=g.coin_in_usd.sum(), available_hours=g.available_hours.sum(),
                         coin_in_per_available_hour=money.per_available_hour(g.coin_in_usd, g.available_hours),
                         zone_entries=g.entries.sum(), covered_sensor_hours=g.covered.sum(),
                         entries_per_covered_hour=money.per_available_hour(g.entries, g.covered)))
    table = pd.DataFrame(rows, columns=columns)
    if not table.empty:
        table["phase"] = pd.Categorical(table.phase, PHASES, ordered=True)
        table = table.sort_values(["phase", "area"]).reset_index(drop=True)
        table["phase"] = table.phase.astype(str)
    present = set(table.phase)
    reason = None
    if PHASES[1] not in present:
        reason = (f"The selected period has no days inside the closure ({start:%b %d}–{end:%b %d}, 2025), "
                  "so it cannot show how the Back Forty moved while the walkway was closed. "
                  "Widen the analysis period to include the closure.")
    elif not present & {PHASES[0], PHASES[2]}:
        reason = ("The selected period lies entirely inside the closure, so there is no before or after "
                  "comparison. Widen the analysis period beyond "
                  f"{start:%b %d}–{end:%b %d}.")
    elif "Back Forty" not in set(table.area):
        reason = "The selected period has no Back Forty machine-days."
    return table, reason


def closure_chart(table: pd.DataFrame) -> go.Figure:
    """Grouped bars: coin-in per available machine-hour, Back Forty vs rest of floor, by phase."""
    fig = go.Figure()
    for area, color in (("Back Forty", GREEN), ("Rest of floor", BLUE)):
        part = table[table.area == area]
        fig.add_trace(go.Bar(
            x=part.phase, y=part.coin_in_per_available_hour, name=area, marker_color=color,
            text=[f"${v:,.0f}/h" if pd.notna(v) else "n/a" for v in part.coin_in_per_available_hour],
            textposition="outside", customdata=part.days,
            hovertemplate=area + ", %{x}: $%{y:,.1f} per available machine-hour (%{customdata} days)<extra></extra>"))
    fig.update_layout(barmode="group", height=340, legend=dict(orientation="h", y=1.12, x=0),
                      margin=dict(l=10, r=10, t=40, b=10))
    fig.update_yaxes(title="Coin-in per available machine-hour ($/h)", tickformat="$,.0f")
    return label(fig, "Coin-in per available hour around the walkway closure", "Closure phase")


# ---- Actions: costs, cards and assumed-recovery scenarios ---------------------------------

CARD_ACTIONS = ("A-INSPECT", "A-PREVENTIVE", "A-TECH-SHIFT", "A-HOLD")
CARD_TITLES = {"A-INSPECT": "Inspect", "A-PREVENTIVE": "Maintenance",
               "A-TECH-SHIFT": "Technician coverage", "A-HOLD": "Preserve funds"}
SCENARIO_ACTIONS = ("A-PREVENTIVE", "A-TECH-SHIFT")
RECOVERY_LEVELS = (0.0, 0.25, 0.5, 1.0)


def cost_comparison(options: pd.DataFrame, catalog: pd.DataFrame, manager_ids: list[str]) -> pd.DataFrame:
    """Spend per option from ``assess`` plus the manager's replacement baseline via ``budget``."""
    rows = [dict(action_type_id=r.action_type_id, option=CARD_TITLES.get(r.action_type_id, r.action),
                 cost_usd=r.cost_usd, role="July option")
            for r in options.itertuples() if r.action_type_id in CARD_ACTIONS]
    for action, label in (("A-REPLACE-LEASE", "Lease 10 replacements"), ("A-REPLACE-BUY", "Buy 10 replacements")):
        line = budget.ActionLine(action, len(manager_ids), list(manager_ids))
        rows.append(dict(action_type_id=action, option=label, cost_usd=budget.line_cost_usd(catalog, line),
                         role="Manager baseline (not funded)"))
    order = {a: i for i, a in enumerate(CARD_ACTIONS + ("A-REPLACE-LEASE", "A-REPLACE-BUY"))}
    return (pd.DataFrame(rows).sort_values("action_type_id", key=lambda s: s.map(order))
            .reset_index(drop=True))


def cost_chart(costs: pd.DataFrame, budget_usd: float = config.BUDGET_USD) -> go.Figure:
    colors = {"July option": GREEN, "Manager baseline (not funded)": MUTED}
    fig = go.Figure()
    for role, part in costs.groupby("role", sort=False):
        fig.add_trace(go.Bar(y=part.option, x=part.cost_usd, orientation="h", name=role,
                             marker_color=colors[role], text=[f"${v:,.0f}" for v in part.cost_usd],
                             textposition="outside", cliponaxis=False,
                             hovertemplate="%{y}: $%{x:,.0f}<extra></extra>"))
    fig.add_vline(x=budget_usd, line_dash="dash", line_color=RULE,
                  annotation_text=f"${budget_usd:,.0f} budget", annotation_position="top")
    fig.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=costs.option.tolist())
    fig.update_xaxes(title="Catalogue cost for July 1–30 ($)", tickformat="$,.0f",
                     range=[0, max(costs.cost_usd.max(), budget_usd) * 1.22])
    fig.update_layout(height=330, legend=dict(orientation="h", y=1.15, x=0),
                      margin=dict(l=10, r=30, t=40, b=10))
    return label(fig, "July option costs vs $100,000 budget", None, "Option")


def recovery_scenarios(options: pd.DataFrame, levels=RECOVERY_LEVELS) -> pd.DataFrame:
    """Assumed-recovery scenarios for maintenance and staffing only.

    Uses ``assess`` outputs: incremental theo = recovery × headroom − implementation
    downtime theo, so 50% equals the base case, 25% the halved case and 0% leaves the
    implementation cost and downtime in place. Inspection is excluded by design.
    """
    rows = []
    for r in options[options.action_type_id.isin(SCENARIO_ACTIONS)].itertuples():
        for level in levels:
            theo = level * r.recovery_headroom_usd - r.implementation_theo_usd
            rows.append(dict(action_type_id=r.action_type_id, option=CARD_TITLES[r.action_type_id],
                             assumed_recovery=level, spend_usd=r.cost_usd,
                             implementation_theo_usd=r.implementation_theo_usd,
                             recovery_headroom_usd=r.recovery_headroom_usd,
                             incremental_theo_usd=theo, theo_less_spend_usd=theo - r.cost_usd))
    return pd.DataFrame(rows)


def scenario_chart(scenarios: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    # Both options start near the same 0% value; label them on opposite sides so they never collide.
    for (action, part), color, dash, side in zip(scenarios.groupby("option", sort=False), (BLUE, PLUM),
                                                 ("solid", "dash"), ("top", "bottom")):
        where = [f"{side} right" if level == 0 else f"{side} center" for level in part.assumed_recovery]
        fig.add_trace(go.Scatter(
            x=part.assumed_recovery, y=part.theo_less_spend_usd, mode="lines+markers+text", name=action,
            line=dict(color=color, width=2.5, dash=dash), text=[usd(v) for v in part.theo_less_spend_usd],
            textposition=where, hovertemplate=action + ", %{x:.0%} recovery: $%{y:,.0f}<extra></extra>"))
    fig.add_hline(y=0, line_dash="dash", line_color=GREEN,
                  annotation_text="Preserve funds: $0", annotation_position="bottom right")
    fig.update_xaxes(title="Assumed recovery of historical<br>downtime/waiting (scenario)", tickformat=".0%",
                     tickvals=list(RECOVERY_LEVELS))
    fig.update_yaxes(title="Incremental theo less spend ($)", tickformat="$,.0f")
    fig.update_layout(height=340, legend=dict(orientation="h", y=1.12, x=0), margin=dict(l=10, r=10, t=40, b=10))
    return label(fig, "Incremental theo less spend by assumed recovery")


def action_cards(options: pd.DataFrame, catalog: pd.DataFrame, evidence: dict,
                 plan: list[budget.ActionLine], budget_usd: float = config.BUDGET_USD) -> list[dict]:
    """Four short decision cards, all numbers taken from ``assess`` and the catalogue."""
    cat = catalog.set_index("action_type_id")
    funded = {line.action_type_id for line in plan}
    spent = budget.plan_cost_usd(catalog, plan)
    opts = options.set_index("action_type_id")
    cards = []
    for action in CARD_ACTIONS:
        if action not in opts.index:
            continue
        row = opts.loc[action]
        minutes = float(cat.loc[action, "downtime_minutes"])
        machines = {"A-INSPECT": len(evidence.get("inspection_targets", [])),
                    "A-PREVENTIVE": len(evidence.get("maintenance_targets", []))}.get(action, 0)
        downtime = (f"{minutes / 60 * machines:,.1f} machine-hours ({minutes:.0f} min × {machines} machines); "
                    f"${row.implementation_theo_usd:,.0f} theo at historical play" if machines else "None scheduled")
        if action == "A-INSPECT":
            benefit = "Information only: a verified paytable/configuration. No revenue is assumed."
            decision = "Fund" if action in funded else "Not funded"
        elif action == "A-HOLD":
            benefit = "Keeps cash for a decision backed by inspection or pilot results."
            downtime = "None"
            decision = f"Preserve ${budget_usd - spent:,.0f}"
        else:
            benefit = (f"Scenario only: ${row.recovery_headroom_usd:,.0f} theo if 100% of historical "
                       f"{'downtime' if action == 'A-PREVENTIVE' else 'grave-shift waiting'} is recovered; "
                       "$0 at 0%.")
            decision = "Not funded: spend exceeds even the 100% scenario"
            if row.high_net_usd > 0:
                decision = "Not funded: positive only under optimistic recovery"
        cards.append(dict(action_type_id=action, title=CARD_TITLES[action], spend_usd=float(row.cost_usd),
                          lead_days=int(cat.loc[action, "lead_days"]), downtime=downtime,
                          benefit=benefit, decision=decision))
    return cards


# ---- Model: frozen-forecast error and fit -------------------------------------------------


def mae_table(full_scores: pd.Series, labels: dict) -> pd.DataFrame:
    """``score_forecasts`` output as a chart-ready table, with change vs the constant baseline."""
    baseline = full_scores["constant"]
    table = pd.DataFrame({"kind": full_scores.index, "model": [labels[k] for k in full_scores.index],
                          "mae_usd": full_scores.to_numpy()})
    table["vs_constant"] = (baseline - table.mae_usd) / baseline if baseline else float("nan")
    return table


def mae_chart(table: pd.DataFrame) -> go.Figure:
    best = table.mae_usd.idxmin()
    colors = [GREEN if i == best else MUTED for i in table.index]
    fig = go.Figure(go.Bar(y=table.model, x=table.mae_usd, orientation="h", marker_color=colors,
                           text=[f"{short_usd(v)}/day" for v in table.mae_usd], textposition="outside",
                           cliponaxis=False, hovertemplate="%{y}: $%{x:,.0f} MAE per day<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Holdout MAE, May 1–June 30<br>(USD/day; lower is better)",
                     tickformat="$,.0f", range=[0, table.mae_usd.max() * 1.4])
    fig.update_layout(height=260, margin=dict(l=10, r=30, t=20, b=10), showlegend=False)
    return label(fig, "Holdout MAE by model, May–June", None, "Model")


def forecast_chart(view: pd.DataFrame, kinds, labels: dict) -> go.Figure:
    """Actual coin-in against frozen predictions already stored in the mart."""
    colors = dict(zip(("constant", "weekday", "weekday_trend"), (MUTED, GREEN, PLUM)))
    fig = go.Figure(go.Scatter(x=view.gaming_date, y=view.coin_in_usd, name="Actual coin-in",
                               line=dict(color=INK, width=2)))
    for kind in kinds:
        fig.add_trace(go.Scatter(x=view.gaming_date, y=view[f"{kind}_prediction_usd"], name=labels[kind],
                                 line=dict(color=colors.get(kind, BLUE), dash="solid" if kind == "weekday" else "dot")))
    fig.update_layout(height=380, yaxis_title="Daily coin-in (USD)", hovermode="x unified",
                      yaxis_tickformat="$,.0f", legend=dict(orientation="h", y=1.12, x=0))
    return label(fig, "Actual vs predicted daily coin-in (holdout)", "Gaming date")


def planning_chart(planning: pd.DataFrame) -> go.Figure:
    """Gain in demand share vs uniform allocation, with the week-bootstrap interval.

    Each value is printed in its row label rather than at the bar end, so labels never
    overlap the error bars at any width; negative gains use the adverse color.
    """
    gain, low, high = planning.gain_pp, planning.gain_low_pp, planning.gain_high_pp
    fig = go.Figure(go.Bar(
        y=planning.model, x=gain, orientation="h", name="Gain vs uniform",
        marker_color=[GREEN if v > 0 else ADVERSE for v in gain],
        error_x=dict(type="data", symmetric=False, array=high - gain, arrayminus=gain - low,
                     color=INK, thickness=1.5, width=6),
        hovertemplate="%{y}: %{x:+.2f} percentage points<extra></extra>"))
    fig.add_vline(x=0, line_color=INK)
    fig.update_yaxes(autorange="reversed", tickvals=list(planning.model),
                     ticktext=[f"{m}  <b>{v:+.1f} pp</b>" for m, v in zip(planning.model, gain)])
    # A left-aligned chart title instead of an axis title: it stays readable when long row labels
    # leave only a narrow plot area on phones.
    fig.update_xaxes(title=None, zeroline=False, ticksuffix=" pp")
    fig.update_layout(height=280, margin=dict(l=10, r=20, t=56, b=10), showlegend=False,
                      title=dict(text="Review-day demand share vs uniform allocation<br>"
                                      "(percentage points; whiskers: week bootstrap)",
                                 x=0.02, xanchor="left", xref="container",
                                 font=dict(family="Georgia, serif", color=INK, size=14, weight="normal")))
    return label(fig, "Review-day demand share vs uniform allocation", "Gain vs uniform (percentage points)", "Model")
