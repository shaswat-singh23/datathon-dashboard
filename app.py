"""The manager's decision, followed by its evidence and investigation routes."""
import pandas as pd
import streamlit as st

from royale import config, io
from royale.evidence import render_evidence
from royale.filters import analysis_period, bank_drill, describe_period, reset_button
from royale.theme import apply_theme
from royale.marts.q1_machines import summarize
from royale.overview import (EVIDENCE_CARDS, checked_by, july_decision, period_totals, rank_stability,
                             select_machine_days)

st.set_page_config(page_title="The Gilded Ace: Luck, Location, or a Leak?", page_icon="♠", layout="wide")
apply_theme("Executive overview")
st.title("Investigate before replacing.")
st.caption("Should we replace the ten lowest-earning machines? · The Gilded Ace, January–June 2025 · "
           "Fictional casino, synthetic data.")

try:
    machines = io.mart("q1_machines")
    actions = io.mart("q6_actions")
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()

# ---- The fixed July decision: never reads the historical filters below ----------------
decision = july_decision(actions)
if decision["violations"]:
    st.error("July plan needs review: " + "; ".join(decision["violations"]))
    st.stop()
cost, retained, targets = decision["cost"], decision["retained"], decision["targets"]
st.subheader("Fixed July plan · July 1–30, 2025")
d1, d2, d3 = st.columns(3)
d1.metric("Inspection budget", f"${cost:,.0f}", help="Fixed July plan, priced with royale.budget from the catalogue.")
d2.metric("Budget retained", f"${retained:,.0f}",
          help=f"Unspent part of the ${config.BUDGET_USD:,.0f} July budget. Not measured savings or profit.")
count = decision["inspections"]
d3.metric("Configuration inspection" if count == 1 else "Configuration inspections",
          "One" if count == 1 else f"{count}", ", ".join(targets) if targets else None, delta_color="off", delta_arrow="off",
          help="Payout/configuration check on the targets frozen from the complete January–June record.")
st.info("Fixed July plan: defer blanket replacement. "
        + (f"Inspect payout/configuration on {', '.join(targets)} for ${cost:,.0f}; "
           if targets else "No current machine meets the full-period inspection rule; ")
        + f"retain ${retained:,.0f} of the July budget. Budget retained is not measured savings. "
        "The inspection is an information purchase; revenue uplift is unproven. "
        "Within budget and catalogue limits.")
with st.expander("How the fixed July plan is calculated"):
    st.write("Targets, quantities and prices come from the complete January–June record and the action catalogue: "
             "manager bottom-ten machines still on the floor whose full-period payout luck z is below −3.8. "
             "`royale.budget` prices each line as quantity × (unit cost + recurring per day × operating days after "
             "lead time) and checks the $100,000 limit, quantity limits and incompatibility groups. "
             "The historical filters further down never retarget or reprice this plan. "
             "Actions contains the downtime cost, alternatives and measurement plan.")

st.subheader("Evidence · Full January–June case")
for column, card in zip(st.columns(3), EVIDENCE_CARDS):
    with column.container(border=True):
        st.markdown(f"**{card['title']}**")
        st.caption("Full January–June case")
        st.write(card["body"])
        st.caption(f"Caveat: {card['caveat']}")
        st.caption("Checked by: " + " · ".join(f"`{name.split('/')[-1]}` {checked_by(name)}"
                                               for name in card["findings"]))
        st.page_link(card["page"], label=card["link"])

st.markdown("**Recommended path**")
path = st.columns(4)
for column, (route, label) in zip(path, [("pages/1_machines.py", "1 · Machines"), ("pages/2_demand.py", "2 · Demand"),
                                          ("pages/6_actions.py", "3 · Actions"), ("pages/7_model.py", "4 · Model")]):
    column.page_link(route, label=label)

# ---- Filtered exploration ---------------------------------------------------------------
st.header("Explore the historical data")
st.caption("Daily on-floor machine-days. The period carries over to Machines, Demand, Downtime and the Actions "
           "evidence; the bank carries over to Machines. Neither changes the fixed July plan or the evidence above.")
dates = pd.to_datetime(machines.gaming_date)
start, end = analysis_period("home", dates.min().date(), dates.max().date())
f1, f2 = st.columns([3, 1])
with f1:
    bank = bank_drill("home", machines.bank_id.dropna().unique().tolist())
with f2:
    reset_button("home")
selected = select_machine_days(machines, start, end, bank)
scope = f"Historical scope: {bank}, {describe_period(start, end)}"
if selected.empty:
    st.caption(scope)
    st.info("No on-floor machine-days in this selection. Widen the period or choose another bank.")
else:
    totals = period_totals(selected)
    st.caption(f"{scope}; {selected.machine_id.nunique()} machines and {len(selected):,} on-floor machine-days. "
               "Every historical KPI, chart and rank below uses this selection.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Coin-in", f"${totals['coin_in']:,.0f}")
    k2.metric("House win", f"${totals['house_win']:,.0f}",
              f"${totals['house_win'] - totals['theo']:+,.0f} vs theo")
    k3.metric("Observed hold", "Undefined" if totals["hold"] is None else f"{totals['hold']:.2%}")
    k4.metric("Availability", "Undefined" if totals["availability"] is None else f"{totals['availability']:.2%}")
    if totals["available_hours"] > 0:
        ranked = summarize(selected)
        raw = ranked.sort_values("raw_rank").head(10)
        # An undefined economic rate is not evidence of bottom-ten underperformance.
        adjusted = ranked.loc[ranked.adjusted_per_hour.notna()].head(10)
        overlap = len(set(raw.index) & set(adjusted.index))
        st.metric("Manager picks surviving adjustment", f"{overlap} / {len(raw)}")
        st.caption(f"Manager baseline: lowest total house win on active on-floor days. "
                   f"Adjusted list: lowest (theo − supplied costs) / available hour among "
                   f"{ranked.adjusted_per_hour.notna().sum()} machines with defined rates; "
                   f"showing the lowest {len(adjusted)}. Ranks recalculate within this period and bank; "
                   "a small bank can contain fewer than ten machines. Undefined rates are excluded.")
        st.subheader("The manager's picks after adjustment")
        st.dataframe(raw[["raw_rank", "adjusted_rank", "game", "zone", "house_win", "adjusted_per_hour",
                          "active_days", "availability", "luck_z"]], width="stretch", column_config={
            "raw_rank": "Manager rank", "adjusted_rank": "Adjusted rank", "game": "Game", "zone": "Zone(s)",
            "house_win": st.column_config.NumberColumn("House win", format="$%.0f"),
            "adjusted_per_hour": st.column_config.NumberColumn("Expected contribution / available hour", format="$%.2f"),
            "active_days": "On-floor days", "availability": st.column_config.NumberColumn("Availability", format="percent"),
            "luck_z": st.column_config.NumberColumn("House luck z", format="%.2f"),
        })
        with st.expander("How stable are these adjusted ranks?"):
            stability = rank_stability(selected, raw.index)
            if stability.empty:
                st.info("Select at least three complete calendar months to compare month-removal ranks.")
            else:
                st.dataframe(stability, width="stretch", column_config={
                    "full_adjusted_rank": "Selected-period rank", "lowest_rank": "Lowest rank after deletion",
                    "highest_rank": "Highest rank after deletion", "bottom_ten_runs": "Runs in bottom ten",
                    "testable_runs": "Runs with available hours", "complete_months": "Complete months deleted in turn",
                })
                st.caption("Remove one complete calendar month at a time, recompute expected contribution / "
                           "available hour, and rank against the remaining machines in this bank selection. "
                           "Any partial boundary months stay in each run. Smaller ranks mean weaker economics. "
                           "The range and bottom-ten counts describe sensitivity to evidence windows; "
                           "overlapping runs are not independent, confidence intervals or probabilities. "
                           "No available hours means no rank in that run. This does not measure replacement uplift.")
    else:
        st.metric("Manager picks surviving adjustment", "Undefined")
        st.info("No available machine-hours in this selection; adjusted economic ranks are undefined.")
    st.warning("These ranks are descriptive screening priorities. They do not establish that a machine is defective "
               "or estimate replacement uplift. Short periods are noisy; change the period to check stability. "
               "Adjusted contribution removes payout luck but retains realized supplied costs. "
               "Machines tests competing location and payout explanations; flags can overlap.")
    daily = selected.groupby("gaming_date").coin_in_cents.sum()
    st.line_chart((daily / 100).rename("Coin-in (USD)"), height=220)

with st.expander("Source"):
    st.markdown("**Historical mart:** `marts/q1_machines.parquet`, active on-floor machine-days with dated placements; "
                "`royale/marts/q1_machines.py` supplies the same period-specific rankings as Machines. "
                "Money and exposure ratios use `royale.money`: sums of dollars or seconds before division. "
                "Scheduled exposure uses each gaming day's calendar seconds, including March 8's 23 hours. "
                "The contribution rate subtracts supplied lease, service, power and repair costs once. "
                "**July plan:** `marts/q6_actions.parquet`, `proposed_plan`, and `royale.budget` price and validate "
                "the fixed full-period inspection targets, quantities, incompatibilities and $100,000 limit.")
    st.markdown("**Rank sensitivity:** `royale.overview.rank_stability` removes each complete month in turn "
                "when at least three are selected, reranking the remaining summed theo less supplied costs "
                "per available hour. Machine ID breaks rate ties. This window check does not model "
                "unobserved demand or give confidence intervals.")
    if not selected.empty:
        st.write(f"Selected exposure: {totals['available_hours']:,.2f} available machine-hours / "
                 f"{totals['scheduled_hours']:,.2f} scheduled machine-hours.")
    render_evidence(["findings/22-machines.md", "findings/23-july-actions.md"], key="home")

st.caption("Explore Demand, Downtime, Players and Comps in the sidebar for the remaining questions. "
           "Carded player outcomes cover tracked play only. No recommendation encourages heavy losers to play more.")
