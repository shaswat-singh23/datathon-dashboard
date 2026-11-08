"""Tracked-player outcomes: carded play only, from the committed Q4 mart."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from royale.evidence import render_evidence
from royale.filters import independent_scope_note
from royale.theme import ADVERSE, PALETTE, apply_theme

from royale import io
from royale.marts.q4_players import MONEY, QUERY, monthly_summary, outcomes

st.set_page_config(page_title="Tracked players: The Gilded Ace", page_icon="♠", layout="wide")
apply_theme("Player outcomes", compact=True)
st.title("What did tracked players wager, get back and net?")
st.caption("Fictional casino, synthetic data. Carded play only: uncarded wagers and outcomes are invisible. "
           "Coin-in includes replayed winnings; it is not cash brought to the casino.")
try:
    df = outcomes(io.mart("q4_players"))
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()
months = sorted(df.period_month.unique())
st.caption(independent_scope_note("Monthly guest scope: carded play by whole gaming month"))
start, end = st.select_slider("Analysis period (gaming months)", options=months, value=(months[0], months[-1]))
st.caption(f"Monthly guest scope: {start} to {end}, whole months.")
view = df[df.period_month.between(start, end)]
cols = st.columns(3)
for col, field, label in zip(cols, ["home_region", "age_band", "opening_tier"],
                             ["Home region", "Age band", "Opening tier"]):
    selected = col.selectbox(label, ["All"] + sorted(df[field].unique()))
    if selected != "All":
        view = view[view[field] == selected]
if view.empty:
    st.info("No tracked player records for this selection.")
    st.stop()

sums = view[MONEY].sum()
cols = st.columns(5)
for col, field, label in zip(cols, MONEY, ["Tracked wagers", "Tracked payout", "Player net", "Expected house win (theo)", "Player luck residual"]):
    col.metric(label, f"${sums[field]:,.2f}")
st.caption("Player net = payout − coin-in: positive means ahead. Theo is expected house win; "
           "player luck residual = net + theo: positive means the player did better than expected. "
           "These are gaming outcomes; comps and food/drink spending are excluded.")
st.write(f"Distinct tracked accounts in selected period: **{view.player_id.nunique():,}**. "
         "Monthly active-player counts below include only accounts with positive tracked wagers.")

monthly = monthly_summary(view)
st.subheader("Monthly outcomes and share of players ahead")
st.dataframe(monthly[["period_month", "active_players", *MONEY, "ahead_share"]], hide_index=True,
             column_config={"ahead_share": st.column_config.NumberColumn("Players ahead", format="percent")})
st.line_chart(monthly.set_index("period_month")[["ahead_share"]], y_label="Share ahead", height=240)
st.caption("Ahead means strictly positive tracked net within that gaming month, among active carded players. "
           "This does not establish whether someone won on uncarded play or on their whole trip.")

st.subheader("How concentrated are wagers and player losses?")
share_cols = [f"top_{pct}pct_{metric}_share" for metric in ["coin_in", "loss"] for pct in [1, 10]]
st.dataframe(monthly[["period_month", "active_players", "gross_player_loss_usd", *share_cols]], hide_index=True,
             column_config={col: st.column_config.NumberColumn(col, format="percent") for col in share_cols})
st.caption("Rank separately by wager amount and loss each month within the selected guest group. "
           "Loss = max(coin-in − payout, 0) per player-month; winners contribute zero loss. "
           "The denominator is gross losses, not signed net losses after winners' gains. "
           "Top groups contain ceil(active players × 1% or 10%); a blank share means zero denominator. "
           "Equal-share baseline: the selected top group would hold approximately 1% or 10% (with rounding).")

month = st.selectbox("Concentration chart month", list(monthly.period_month))
active = view[(view.period_month == month) & (view.tracked_coin_in_usd > 0)]
fig = go.Figure()
fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], name="Equal-share baseline", line=dict(dash="dash", color=PALETTE[4])))
for label, values, color, dash in [("Wagers", active.tracked_coin_in_usd, PALETTE[0], "solid"),
                              ("Gross player losses", (-active.tracked_net_usd).clip(lower=0), ADVERSE, "dot")]:
    ordered = np.sort(values.to_numpy())
    if len(ordered) and ordered.sum() > 0:
        cumulative = np.r_[0, ordered.cumsum() / ordered.sum()]
        # Sample exact cumulative points to keep the interactive chart small.
        positions = np.unique(np.linspace(0, len(ordered), min(201, len(ordered) + 1)).astype(int))
        fig.add_trace(go.Scatter(x=positions / len(ordered), y=cumulative[positions], name=label,
                                mode="lines", line=dict(color=color, dash=dash)))
fig.update_layout(xaxis_title="Cumulative share of active players, lowest to highest",
                  yaxis_title="Cumulative share of amount", height=350,
                  xaxis_tickformat=".0%", yaxis_tickformat=".0%")
st.plotly_chart(fig, width="stretch")

st.subheader("Guest-group comparison")
dimension = st.selectbox("Compare groups by", ["home_region", "age_band", "opening_tier"])
groups = view.groupby(dimension, dropna=False)
table = groups[MONEY].sum()
table["distinct_players"] = groups.player_id.nunique()
positive = view.assign(active=view.tracked_coin_in_usd > 0,
                       ahead=(view.tracked_coin_in_usd > 0) & (view.tracked_net_usd > 0)).groupby(dimension)[["active", "ahead"]].sum()
table["ahead_player_month_share"] = positive.ahead / positive.active.replace(0, np.nan)
st.dataframe(table, column_config={"ahead_player_month_share": st.column_config.NumberColumn("Ahead player-month share", format="percent")})
st.caption("Group totals cover the selected months. The ahead share here uses active player-months, "
           "so repeat visitors may contribute once in each month. It is descriptive; groups differ in exposure and play mix. "
           "These summaries are not a reason to encourage heavy losers to gamble more.")
with st.expander("Source and calculation rules"):
    render_evidence(['findings/18-player-outcomes.md'], key='4_players')
    st.markdown("**Mart:** `marts/q4_players.parquet`. **Builder:** `royale/marts/q4_players.py`. "
                "The player_period prepared table has one row per account and gaming month. "
                "The builder projects it without joins and asserts row counts, key uniqueness and both sign identities. "
                "All displayed totals sum the projected dollar fields; monthly concentration and ahead shares "
                "are recomputed after filters. No ratios are averaged across months.")
    st.code(QUERY, language="sql")
    st.markdown("**Calculations:** `monthly_summary` in the builder; top shares use "
                "`royale.money.concentration_share`. Lorenz curves independently sort wagers and nonnegative losses. "
                "Only complete gaming months can be selected because the source is monthly. "
                "[Evidence and limitations](https://github.com/shaswat-singh23/datathon-dashboard/blob/master/findings/18-player-outcomes.md).")
