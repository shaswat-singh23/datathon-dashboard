"""The manager's decision, followed by its evidence and investigation routes."""
import pandas as pd
import streamlit as st

from royale import budget, config, io
from royale.evidence import render_evidence
from royale.marts.q1_machines import summarize
from royale.marts.q6_actions import proposed_plan
from royale.overview import period_totals, rank_stability, select_machine_days

st.set_page_config(page_title="The Gilded Ace: Luck, Location, or a Leak?", page_icon="♠", layout="wide")
st.title("Should we replace the ten lowest-earning machines?")
st.caption("The Gilded Ace · January–June 2025 · Fictional casino, synthetic data.")

try:
    machines = io.mart("q1_machines")
    actions = io.mart("q6_actions")
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()

catalog = actions.loc[actions.record_type == "catalog"]
plan = proposed_plan(actions)
violations = budget.validate_plan(catalog, plan)
if violations:
    st.error("July plan needs review: " + "; ".join(violations))
    st.stop()
cost = budget.plan_cost_usd(catalog, plan)
targets = [target for line in plan for target in line.targets]
st.info("Defer blanket replacement. Low realized earnings alone do not show that a new machine would help. "
        + (f"Inspect payout/configuration on {', '.join(targets)} for ${cost:,.0f}; "
           if targets else "No current machine meets the full-period inspection rule; ")
        + f"preserve ${config.BUDGET_USD - cost:,.0f} of the July budget. "
        "Inspection buys information; no positive revenue recovery is estimated.")
st.caption("July 1–30 plan: fixed targets and catalogue prices from the complete January–June record. "
           "The evidence filters below recalculate historical comparisons; they do not retarget this plan. "
           "Actions contains the downtime cost, alternative scenarios and measurement plan.")
links = st.columns(3)
links[0].page_link("pages/1_machines.py", label="Investigate machines, location and payouts")
links[1].page_link("pages/6_actions.py", label="Review July prices, uncertainty and measurement")
links[2].page_link("pages/7_model.py", label="Inspect model validation and baselines")

dates = pd.to_datetime(machines.gaming_date)
start, end = st.slider("Analysis period", min_value=dates.min().date(), max_value=dates.max().date(),
                       value=(dates.min().date(), dates.max().date()))
bank = st.selectbox("Bank drill", ["All banks"] + sorted(machines.bank_id.dropna().unique().tolist()))
selected = select_machine_days(machines, start, end, bank)
if selected.empty:
    st.info("No on-floor machine-days in this selection. Widen the period or choose another bank.")
else:
    totals = period_totals(selected)
    st.caption(f"Historical scope: {bank}, {start:%b %d}–{end:%b %d}, "
               f"{selected.machine_id.nunique()} machines and {len(selected):,} on-floor machine-days. "
               "Every historical KPI, chart and rank below uses this selection. "
               "Filters on other pages are independent; set them again when following a link.")
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
