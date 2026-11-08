"""Q5: loyalty cost and changes, read exclusively from the committed monthly mart."""
import pandas as pd
import plotly.express as px
import streamlit as st

from royale.evidence import render_evidence
from royale.filters import independent_scope_note
from royale.theme import apply_theme

from royale import io, money

st.set_page_config(page_title="Comps: The Gilded Ace", page_icon="♠", layout="wide")
apply_theme("Loyalty & comps", compact=True)
st.title("What did the loyalty program cost, and what changed?")
st.caption("Monthly tracked guest activity and property totals. Comp cost is already inside POS cost of goods; do not subtract it again. Face value is menu value, not cash revenue.")

mart = io.mart("q5_comps")
months = sorted(mart.month.unique())
st.caption(independent_scope_note("Monthly guest scope: tracked guests and property totals by whole month"))
a, b = st.select_slider("Period (whole months)", options=months, value=(months[0], months[-1]))
st.caption(f"Monthly guest scope: {a} to {b}, whole months.")
window = mart[mart.month.between(a, b)]
tracked = window[window.population.eq("tracked")]
property_totals = window[window.population.eq("property")]
tiers = st.multiselect("Opening tier", sorted(tracked.opening_tier.dropna().unique()))
regions = st.multiselect("Home region", sorted(tracked.home_region.dropna().unique()))
selected = tracked
if tiers:
    selected = selected[selected.opening_tier.isin(tiers)]
if regions:
    selected = selected[selected.home_region.isin(regions)]
if selected.empty:
    st.info("No tracked activity matches these filters.")
    st.stop()

value_cols = ["comp_cost_usd", "comp_face_value_usd", "theo_usd", "points_earned", "points_redeemed"]
monthly = selected.groupby("month", as_index=False)[value_cols].sum()
monthly["comp_reinvestment"] = monthly.apply(
    lambda r: money.comp_reinvestment([r.comp_cost_usd], [r.theo_usd]), axis=1)
monthly["points_per_face_dollar"] = monthly.apply(
    lambda r: r.points_redeemed / r.comp_face_value_usd if r.comp_face_value_usd else float("nan"), axis=1)
ratio = money.comp_reinvestment(selected.comp_cost_usd, selected.theo_usd)
c1, c2, c3 = st.columns(3)
c1.metric("Tracked comp economic cost", f"${selected.comp_cost_usd.sum():,.2f}")
c2.metric("Tracked comp menu value", f"${selected.comp_face_value_usd.sum():,.2f}")
c3.metric("Tracked cost / tracked theo", "Undefined" if ratio is None else f"{ratio:.2%}")

st.subheader("Monthly cost and reinvestment")
long = monthly.melt(id_vars="month", value_vars=["comp_cost_usd", "comp_face_value_usd"], var_name="Measure", value_name="USD")
st.plotly_chart(px.bar(long, x="month", y="USD", color="Measure", barmode="group"), width="stretch")
st.plotly_chart(px.line(monthly, x="month", y="comp_reinvestment", markers=True,
                        labels={"comp_reinvestment": "Comp cost / tracked theo"}), width="stretch")
st.dataframe(monthly, hide_index=True, width="stretch")

st.subheader("Did redemption intensity change?")
st.plotly_chart(px.line(monthly, x="month", y=["points_earned", "points_redeemed"], markers=True), width="stretch")
st.plotly_chart(px.line(monthly, x="month", y="points_per_face_dollar", markers=True,
                        labels={"points_per_face_dollar": "Points redeemed / comp menu dollar"}), width="stretch")
st.caption("Use the first selected month as a simple constant-intensity baseline. Points per menu dollar separates redemption intensity from comp volume. A break is descriptive evidence, not proof of a policy change; guest mix, item mix and accounting timing remain alternatives.")
first = monthly.iloc[0].points_per_face_dollar
monthly_baseline = monthly[["month", "points_redeemed"]].copy()
monthly_baseline["constant_first_month_baseline"] = monthly.comp_face_value_usd * first
st.dataframe(monthly_baseline, hide_index=True, width="stretch")

st.subheader("Guest groups")
groups = selected.groupby(["opening_tier", "home_region"], as_index=False)[value_cols].sum()
groups["comp_reinvestment"] = groups.apply(lambda r: money.comp_reinvestment([r.comp_cost_usd], [r.theo_usd]), axis=1)
st.dataframe(groups, hide_index=True, width="stretch")
st.caption("Opening tier is used rather than end-of-period tier. Guest ratios describe carded activity only; property theo includes all play.")

st.subheader("Reconciliation to property totals")
# Reconcile the complete tracked population, independently of the guest drill.
recon = tracked.groupby("month", as_index=False)[["comp_cost_usd", "comp_face_value_usd"]].sum().merge(
    property_totals[["month", "comp_cost_usd", "comp_face_value_usd"]], on="month", suffixes=("_tracked", "_property"), validate="one_to_one")
recon["cost_gap_usd"] = (recon.comp_cost_usd_tracked - recon.comp_cost_usd_property).round(2)
st.write(f"All guest groups in the selected period: tracked cost minus property cost = ${recon.cost_gap_usd.sum():,.2f}.")
st.caption("Reconciliation uses all tiers and regions, even while the charts show a selected guest group. A nonzero gap needs investigation; it is not allocated to guest groups.")
st.dataframe(recon, hide_index=True, width="stretch")
property_monthly = property_totals[["month", "comp_cost_usd", "comp_face_value_usd", "theo_usd"]].copy()
property_monthly["comp_reinvestment"] = property_monthly.apply(lambda r: money.comp_reinvestment([r.comp_cost_usd], [r.theo_usd]), axis=1)
st.dataframe(property_monthly, hide_index=True, width="stretch")

with st.expander("Source"):
    render_evidence(['findings/19-comps.md'], key='5_comps')
    st.markdown("Mart: `q5_comps`; builder: `royale/marts/q5_comps.py`. Tracked monthly measures sum `player_period` by `period_month`, `opening_tier`, `home_region`; property totals sum `property_day` by gaming-date month. These are separate populations, combined with UNION ALL, with no raw-row join. Reconciliation joins one monthly aggregate per population (one-to-one). Points are available only for tracked guests. Filters select whole months because player_period has monthly grain.")
    st.code("SELECT period_month, opening_tier, home_region, SUM(comp_cost_usd), SUM(comp_face_value_usd), SUM(theo_usd), SUM(points_earned), SUM(points_redeemed) FROM player_period GROUP BY ALL")
    st.markdown("All reinvestment ratios use `royale.money.comp_reinvestment`: sum(cost) / sum(theo), undefined at zero theo. See `findings/19-comps.md` for the full-window evidence, baseline and limitations.")
