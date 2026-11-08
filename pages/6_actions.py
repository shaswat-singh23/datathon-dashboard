"""A priced July plan and the evidence behind its tradeoffs; committed mart only."""
import pandas as pd
import streamlit as st

from royale.evidence import render_evidence
from royale.filters import analysis_period, describe_period
from royale.theme import apply_theme

from royale import budget, config, io
from royale.marts.q6_actions import assess, proposed_plan

REPO = "https://github.com/shaswat-singh23/datathon-dashboard/blob/master/"
FINDING = REPO + "findings/23-july-actions.md"

st.set_page_config(page_title="Actions: The Gilded Ace", page_icon="♠", layout="wide")
apply_theme("July investment plan")
st.title("Inspect before replacing; preserve the remaining budget")
st.caption("July 1–30, 2025 · A small information purchase, with maintenance and staffing alternatives priced alongside it.")
try:
    data = io.mart("q6_actions")
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

md = data[data.record_type == "machine_day"]
catalog = data[data.record_type == "catalog"].copy()
plan = proposed_plan(data)
total = budget.plan_cost_usd(catalog, plan)
violations = budget.validate_plan(catalog, plan)
left, middle, right = st.columns(3)
left.metric("Plan cost", f"${total:,.0f}")
middle.metric("Budget preserved", f"${config.BUDGET_USD-total:,.0f}")
right.metric("Funded action types", f"{len({line.action_type_id for line in plan})} / 3")
if violations:
    st.error("The July plan breaks a budget or catalogue limit: " + "; ".join(violations))
    st.stop()
st.success("Within budget and catalogue limits.")
st.caption("Historical evidence scope; July plan fixed. The plan above uses the complete January–June record; "
           "the evidence period further down changes only the supporting rates and alternative scenarios.")

full_options, full_evidence = assess(data)
for line in plan:
    row = full_options.set_index("action_type_id").loc[line.action_type_id]
    st.markdown(f"**Fund {line.quantity} payout/configuration inspection: {', '.join(line.targets)} — ${row.cost_usd:,.0f}.** "
                f"One-day lead; execute July 2, with two hours of catalogue downtime per machine. "
                f"Estimated downtime opportunity cost: ${-row.base_theo_usd:,.0f} in theo at historical average play. "
                f"The low/high operational scenario is ${row.low_theo_usd:,.0f} to ${row.high_theo_usd:,.0f} "
                "in incremental theo. No positive revenue recovery is estimated; the outcome is a verified configuration.")
    with st.expander("Trace: funded inspection"):
        st.page_link("pages/1_machines.py", label="Machines: raw ranking, adjusted economics and payout screen")
        st.markdown(f"[Machine finding]({REPO}findings/22-machines.md) · [July plan and calculations]({FINDING})")
        st.write("Targets are current on-floor manager bottom-ten machines with full-period luck z < −3.8. "
                 "This is an inspection lead, not proof of an incorrect payout or wrongdoing. "
                 "Past payout residuals are not recoverable revenue.")
if not plan:
    st.info("No current manager bottom-ten machine passes the inspection screen. Preserve the full budget.")

st.markdown("**Measurement for the funded inspection.** Verify the paytable and meter configuration against "
            "the configured RTP and document pass/fail by July 2. During July 2–30, track availability and "
            "variance-standardized payout residuals; compare with uninspected machines on the same config "
            "and their June record. Do not treat regression to the mean as an inspection benefit. "
            "A correction, if warranted, requires a separate decision and effect estimate.")
st.write("The monetary scenarios favor preserving all funds. The proposed inspection spends a small amount "
         "to resolve a specific configuration question; its information value is not assigned a dollar return. "
         "Defer replacements: the ranking is descriptive and supplies no causal new-title uplift.")
with st.expander("Manager's ten-machine replacement baseline"):
    manager_ids = full_evidence["machines"].sort_values("raw_rank").head(10).index.tolist()
    lease = budget.line_cost_usd(catalog, budget.ActionLine("A-REPLACE-LEASE", len(manager_ids), manager_ids))
    purchase = budget.line_cost_usd(catalog, budget.ActionLine("A-REPLACE-BUY", len(manager_ids), manager_ids))
    st.write("Bottom ten by total house win on active on-floor days: " + ", ".join(manager_ids) + ".")
    st.write(f"Leasing all ten costs ${lease:,.0f}, with 16 operating days after lead time; "
             f"buying all ten costs ${purchase:,.0f}, exceeding the $100,000 budget. "
             "Neither option has a measured replacement-demand effect in these records.")

dates = pd.to_datetime(md.gaming_date)
start, end = analysis_period("actions", dates.min().date(), dates.max().date(), label="Evidence period")
st.caption(f"Historical evidence scope: {describe_period(start, end)}, whole floor; July plan fixed.")
options, evidence = assess(data, start, end)
st.caption("This filter recalculates supporting rates and alternative scenarios. The July plan, its targets, "
           "and its prices remain based on the complete January–June record. Short windows are noisy.")
st.subheader("Tradeoffs against preserving the budget")
st.write("Maintenance and staffing: base assumes 50% of historical downtime or waiting can be removed; "
         "low/high assumes 0%/100%. These are decision scenarios, not measured intervention effects or "
         "confidence intervals. Recoveries use only operating days after lead time and historical theo "
         "per available hour. Guests switching machines can reduce the property benefit.")
cols = ["action", "targets", "cost_usd", "base_theo_usd", "low_theo_usd", "high_theo_usd", "net_usd"]
st.dataframe(options[cols], hide_index=True, width="stretch", column_config={
    "action": "Option", "targets": "Targets", "cost_usd": st.column_config.NumberColumn("Spend", format="$%.0f"),
    "base_theo_usd": st.column_config.NumberColumn("Incremental theo, base", format="$%.0f"),
    "low_theo_usd": st.column_config.NumberColumn("Theo, low", format="$%.0f"),
    "high_theo_usd": st.column_config.NumberColumn("Theo, high", format="$%.0f"),
    "net_usd": st.column_config.NumberColumn("Base theo less spend", format="$%.0f"),
})
st.caption("Incremental theo includes implementation downtime. Theo less spend excludes taxes, lease-share "
           "changes and other operating-cost changes; it is not a full-profit estimate. Inspection's low/high "
           "uses two hours at the target's 90th-percentile historical daily rate / zero displacement. "
           "Quiet-hour scheduling is not assumed to eliminate opportunity cost in the base case.")

st.subheader("If the assumed recovery halves")
st.dataframe(options[["action", "net_usd", "rank_base", "half_net_usd", "rank_half"]],
             hide_index=True, width="stretch", column_config={
                 "action": "Option", "net_usd": st.column_config.NumberColumn("Base theo less spend", format="$%.0f"),
                 "rank_base": "Base rank", "half_net_usd": st.column_config.NumberColumn("Halved recovery less spend", format="$%.0f"),
                 "rank_half": "Halved rank",
             })
changed = options[options.rank_base != options.rank_half]
st.write("The ranking is unchanged when assumed positive recovery halves." if changed.empty else
         "Ranking changes: " + "; ".join(f"{r.action}: {r.rank_base} → {r.rank_half}" for r in changed.itertuples()))
st.caption("Halving applies to the assumed 50% recovery (becoming 25%); fixed spend and implementation "
           "downtime remain. Inspection has no positive recovery to halve.")

action = st.selectbox("Action drill", options.action_type_id.tolist(),
                      format_func=lambda a: options.set_index("action_type_id").loc[a, "action"])
selected = options.set_index("action_type_id").loc[action]
st.subheader(selected.action)
st.write(f"Targets: {selected.targets}. Lead time: {int(catalog.set_index('action_type_id').loc[action, 'lead_days'])} days. "
         f"Operating days in July 1–30: {selected.operating_days}. Evidence rows: {selected.evidence_rows:,}.")
if action == "A-PREVENTIVE":
    st.write(f"Target footprint: {len(evidence['maintenance_targets'])} current {evidence['manufacturer']} machines. "
             "Manufacturer selected by full-period lost share of scheduled hours. "
             "Estimate: per current machine, selected-period lost hours/day × own theo/available hour × "
             "operating days × assumed recovery; subtract 90 minutes of downtime per current machine. "
             "All downtime is included, so even the high scenario generously counts non-fault outages as avoidable.")
    st.write("Measurement if funded: randomize service order within same-title and bank blocks, use the "
             "not-yet-serviced group as control, and compare fault events per 1,000 scheduled hours plus "
             "theo per scheduled hour during July 8–30. Manufacturer/game/location differences can explain "
             "the historical contrast; the package's effectiveness is unknown.")
    if evidence["maintenance_covered"] < len(evidence["maintenance_targets"]):
        st.warning("Some current targets have no available-hour rate in this window. Estimates omit them; the high scenario is incomplete.")
elif action == "A-TECH-SHIFT":
    if evidence["grave_wait_h"] is None:
        st.info("No grave-shift faults in this evidence window. Zero estimated recovery reflects missing events, not evidence of no benefit.")
    else:
        comparator = evidence['other_wait_h']
        st.write(f"Grave mean wait: {evidence['grave_wait_h']:.2f} hours across {evidence['grave_tickets']} faults. "
                 + (f"Other shifts: {comparator:.2f} hours." if comparator is not None else "No other-shift faults in this window."))
    st.write("Estimate: sum(grave fault wait hours × that machine's theo/available hour), divided by selected "
             "calendar days, multiplied by operating days and assumed recovery. Repair time is not removed. "
             "Measurement if funded: during July 8–30, randomize extra coverage across grave shifts; compare "
             "wait time per fault, fault downtime per scheduled hour and property theo with uncovered grave "
             "shifts, blocked by weekday. Fault severity and shift demand can confound historical wait differences.")
    if evidence["grave_rate_coverage"] < evidence["grave_tickets"]:
        st.warning("Some faulted machines have no available-hour rate in this window. Estimates omit them; the high scenario is incomplete.")
elif action == "A-INSPECT":
    st.dataframe(evidence["machines"].reindex(evidence["inspection_targets"])
                 [["days", "raw_rank", "luck_z", "theo_per_h"]], width="stretch")
    st.caption("Ranks and z here use the selected period. Target selection uses the full-period screen. "
               "Repeated period searches do not preserve the original screen's approximate error calibration.")
else:
    st.write("Baseline: spend $0; incremental theo $0; preserve the full $100,000. "
             "Measurement: retain the June monitoring process through July 30 and revisit spending only "
             "after the inspection or a controlled pilot identifies an actionable mechanism.")

with st.expander("Trace: selected option"):
    if action in {"A-PREVENTIVE", "A-TECH-SHIFT"}:
        st.page_link("pages/3_downtime.py", label="Downtime: availability, manufacturers and repair response")
        st.markdown(f"[Downtime finding]({REPO}findings/17-downtime.md)")
    else:
        st.page_link("pages/1_machines.py", label="Machines: manager baseline and payout screen")
        st.markdown(f"[Machine finding]({REPO}findings/22-machines.md)")
    st.markdown(f"[July plan: sources, calculations and limitations]({FINDING})")

with st.expander("Source"):
    render_evidence(['findings/23-july-actions.md', 'findings/17-downtime.md', 'findings/22-machines.md'], key='6_actions')
    st.markdown("""**Mart:** `marts/q6_actions.parquet`, built with
`uv run python -m royale.build q6_actions`. This page reads only that committed mart.

Machine-days reuse the Q1 placement-at-gaming-day-start query, excluding inactive and
off-floor rows. Theo and payout z use `royale.money`; rates are ratios of sums.
Fault tickets reuse Q3's gaming-day and local-shift attribution. Catalogue prices,
lead days, downtime and limits come from `action_catalog`; all pricing and plan
validation go through `royale.budget`. The audits below check row counts before
and after joins; the operation fault filter is applied afterward.

Inspection selects only current manager bottom-ten machines with full-period z < −3.8.
It books no positive uplift. Maintenance covers the latest on-floor footprint of the
manufacturer with the highest historical downtime share. Staffing covers grave-shift
waiting only. No later-published context is used. No incremental comp cost is proposed.
The scenarios assume historical demand persists, ignore property substitution and
do not establish treatment effects. Source findings await independent review.
""")
    st.dataframe(data.loc[data.record_type == "audit", ["audit_table", "rows_before", "rows_after", "excluded_off_floor"]],
                 hide_index=True, width="stretch")
    st.markdown(f"[Plan finding and reproducible checks]({FINDING})")
