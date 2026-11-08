"""Q3: How much play was lost to downtime, and when?

Reads only io.mart("q3_downtime"): on-floor machine-days (record_type == "machine_day") and
operations tickets (record_type == "ticket"). Every rate is a ratio of sums.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from royale.evidence import render_evidence
from royale.filters import analysis_period, describe_period
from royale.theme import ADVERSE, PALETTE, apply_theme

from royale import io

st.set_page_config(page_title="Downtime: The Gilded Ace", page_icon="♠", layout="wide")
apply_theme("Availability & downtime", compact=True)

LOST = ADVERSE        # lost machine-hours: an adverse outcome
PRIMARY = PALETTE[0]  # series 1
COMPARE = PALETTE[2]  # series 2 (only where a second part is needed)
SHIFTS = ["day", "swing", "grave"]
SHIFT_LABEL = {"day": "Day (06-14)", "swing": "Swing (14-22)", "grave": "Grave (22-06)"}


def ratio(num: pd.Series, den: pd.Series) -> float:
    """Ratio of sums; NaN when the denominator sums to zero.
    Same rule as money.availability / money.per_available_hour (issue #14); local until that merges."""
    d = den.sum()
    return num.sum() / d if d else float("nan")


def style(fig: go.Figure, height: int = 300, yfmt: str = ",.0f") -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", hovermode="closest",
                      legend=dict(orientation="h", y=1.1, x=0))
    fig.update_yaxes(tickformat=yfmt, gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


def group_table(md: pd.DataFrame, key: str) -> pd.DataFrame:
    g = md.groupby(key).agg(machines=("machine_id", "nunique"), scheduled_h=("scheduled_h", "sum"),
                            lost_h=("lost_h", "sum"), lost_coin_in=("lost_coin_in_usd", "sum"),
                            lost_theo=("lost_theo_usd", "sum"))
    g["lost_share"] = g["lost_h"] / g["scheduled_h"]
    g["lost_h_per_machine"] = g["lost_h"] / g["machines"]
    return g


TABLE_COLS = {
    "machines": st.column_config.NumberColumn("Machines"),
    "scheduled_h": st.column_config.NumberColumn("Scheduled hrs", format="%,.0f"),
    "lost_h": st.column_config.NumberColumn("Lost hrs", format="%,.0f"),
    "lost_share": st.column_config.NumberColumn("Lost share", format="percent"),
    "lost_h_per_machine": st.column_config.NumberColumn("Lost hrs / machine", format="%,.1f"),
    "lost_coin_in": st.column_config.NumberColumn("Est. lost coin-in", format="$%,.0f"),
    "lost_theo": st.column_config.NumberColumn("Est. lost theo", format="$%,.0f"),
}

st.title("How much play was lost to downtime, and when?")
st.caption("Lost machine-hours (scheduled minus available), what that play was likely worth, and how fast "
           "faults were repaired. On-floor machines only; ratios are ratios of sums.")

try:
    df = io.mart("q3_downtime")
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()
df["gaming_date"] = pd.to_datetime(df["gaming_date"])
df["month"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m")

# ---- Filters: period + zone drill ------------------------------------------------------
dmin, dmax = df["gaming_date"].min().date(), df["gaming_date"].max().date()
c1, c2 = st.columns([3, 1])
with c1:
    start, end = analysis_period("downtime", dmin, dmax)
zones = (df[df["zone_id"].notna()][["zone_id", "zone_name"]].drop_duplicates().sort_values("zone_name"))
zone_label = dict(zip(zones["zone_id"], zones["zone_name"]))
zone = c2.selectbox("Zone drill", ["All zones"] + list(zones["zone_id"]),
                    format_func=lambda z: z if z == "All zones" else f"{zone_label[z]} ({z})")

in_period = (df["gaming_date"].dt.date >= start) & (df["gaming_date"].dt.date <= end)
view = df[in_period] if zone == "All zones" else df[in_period & (df["zone_id"] == zone)]
md = view[view["record_type"] == "machine_day"]
tk = view[view["record_type"] == "ticket"]
faults = tk[tk["event_type"] == "fault_repair"]
scope_name = "the whole floor" if zone == "All zones" else zone_label[zone]
st.caption(f"Scope: {scope_name}, {describe_period(start, end)}. The daily period is shared with "
           "Home, Machines, Demand, Downtime and the Actions evidence; the zone drill is this page's own.")
if md.empty:
    st.warning("No machine-days in that period.")
    st.stop()

# ---- KPIs ------------------------------------------------------------------------------
lost_h = md["lost_h"].sum()
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Lost machine-hours", f"{lost_h:,.0f}",
          help="SUM(scheduled_h - available_h). Scheduled hours come from calendar_day (Mar 8 = 23 h).")
k2.metric("Share of scheduled hours", f"{ratio(md['lost_h'], md['scheduled_h']):.2%}")
k3.metric("Est. lost coin-in", f"${md['lost_coin_in_usd'].sum() / 1e3:,.0f}k",
          help="Lost hours x the same machine's coin-in per available hour in the same month. See Method below.")
k4.metric("Est. lost theo (house)", f"${md['lost_theo_usd'].sum() / 1e3:,.1f}k",
          help="Same method with theo (coin-in x (1 - configured RTP)): the expected house win given up.")
k5.metric("Fault tickets", f"{len(faults):,}",
          help=f"fault_repair tickets opened in the period, {scope_name}. "
               f"Median response {faults['response_h'].median():.1f} h." if len(faults) else None)

# ---- When it happened ------------------------------------------------------------------
st.subheader(f"When it happened: lost machine-hours per day, {scope_name}")
daily = md.groupby("gaming_date", as_index=False).agg(lost_h=("lost_h", "sum"))
fig = go.Figure(go.Bar(x=daily["gaming_date"], y=daily["lost_h"], marker_color=LOST, marker_line_width=0,
                       hovertemplate="%{x|%a %b %d}: %{y:,.1f} lost hrs<extra></extra>"))
st.plotly_chart(style(fig, 260).update_layout(bargap=0.15), width="stretch")

# ---- By month and manufacturer ---------------------------------------------------------
left, right = st.columns(2)
with left:
    st.subheader("By month")
    mo = group_table(md, "month")
    f2 = go.Figure(go.Bar(x=mo.index, y=mo["lost_h"], marker_color=LOST, marker_line_width=0,
                          customdata=mo[["lost_share", "lost_coin_in"]],
                          hovertemplate="%{x}: %{y:,.0f} lost hrs (%{customdata[0]:.2%} of scheduled), "
                                        "est. lost coin-in $%{customdata[1]:,.0f}<extra></extra>"))
    st.plotly_chart(style(f2, 260).update_layout(bargap=0.35), width="stretch")
    st.caption("A period that cuts a month shows only the days inside it.")
with right:
    st.subheader("By manufacturer")
    mf = group_table(md, "manufacturer").sort_values("lost_share")
    f3 = go.Figure(go.Bar(y=mf.index, x=mf["lost_share"], orientation="h", marker_color=LOST,
                          marker_line_width=0, text=[f"{v:.2%}" for v in mf["lost_share"]],
                          textposition="outside", cliponaxis=False,
                          customdata=mf[["lost_h", "machines", "lost_h_per_machine"]],
                          hovertemplate="%{y}: %{x:.2%} of scheduled hours lost<br>%{customdata[0]:,.0f} hrs "
                                        "across %{customdata[1]} machines (%{customdata[2]:.1f} per machine)"
                                        "<extra></extra>"))
    f3.update_xaxes(tickformat=".1%", showgrid=True, gridcolor="rgba(0,0,0,0.08)")
    st.plotly_chart(style(f3, 260).update_layout(bargap=0.35), width="stretch")
    st.caption("Share of scheduled hours lost, so fleet size does not drive the ranking.")

with st.expander("Month and manufacturer tables", expanded=False):
    st.dataframe(mo, width="stretch", column_config=TABLE_COLS)
    st.dataframe(mf.sort_values("lost_share", ascending=False), width="stretch", column_config=TABLE_COLS)

# ---- Banks (drill) ---------------------------------------------------------------------
st.subheader(f"Banks in {scope_name}, ranked by share of scheduled hours lost")
bk = group_table(md, "bank_id")
bk = bk.join(md.groupby("bank_id")["zone_name"].agg(lambda s: s.mode().iat[0]).rename("zone"))
bk = bk.sort_values("lost_share", ascending=False)
st.dataframe(bk[["zone", "machines", "lost_h", "lost_share", "lost_h_per_machine", "lost_coin_in", "lost_theo"]],
             width="stretch", height=280, column_config={"zone": "Zone", **TABLE_COLS})

st.caption("Uncertainty: lost hours are measured, but lost coin-in and theo are estimates with no interval "
           "(they assume a machine plays at its own monthly rate when up), and a bank or machine with few "
           "scheduled hours moves a lot on one outage.")
st.markdown("**Machines with the most lost hours**")
mc = group_table(md, ["machine_id", "manufacturer"]).reset_index()
nf = faults.groupby("machine_id").size().rename("fault_tickets")
mc = mc.merge(nf, on="machine_id", how="left").fillna({"fault_tickets": 0})
st.dataframe(mc.sort_values("lost_h", ascending=False).head(15)
             [["machine_id", "manufacturer", "fault_tickets", "lost_h", "lost_share", "lost_coin_in", "lost_theo"]],
             width="stretch", hide_index=True,
             column_config={"machine_id": "Machine", "manufacturer": "Manufacturer",
                            "fault_tickets": st.column_config.NumberColumn("Fault tickets", format="%d"),
                            **TABLE_COLS})

# ---- Repair response -------------------------------------------------------------------
st.subheader("Repair response: how long a faulted machine stayed down")
if faults.empty:
    st.info("No fault tickets in this period and zone.")
else:
    left, right = st.columns(2)
    with left:
        st.markdown("**Mean hours by shift the fault opened**: waiting for a tech, then fixing")
        sh = faults.groupby("shift").agg(n=("operation_id", "count"), wait=("wait_h", "mean"),
                                         fix=("fix_h", "mean"), median=("response_h", "median")).reindex(SHIFTS)
        sh = sh.dropna(subset=["n"])
        labels = [SHIFT_LABEL[s] for s in sh.index]
        f4 = go.Figure()
        f4.add_bar(x=labels, y=sh["wait"], name="Wait for tech", marker_color=COMPARE, marker_line_width=0,
                   customdata=sh["n"], hovertemplate="%{x}: wait %{y:.2f} h (n=%{customdata:,})<extra></extra>")
        f4.add_bar(x=labels, y=sh["fix"], name="Fix", marker_color=PRIMARY, marker_line_width=0,
                   customdata=sh["n"], hovertemplate="%{x}: fix %{y:.2f} h (n=%{customdata:,})<extra></extra>")
        st.plotly_chart(style(f4, 280, ".1f").update_layout(barmode="stack", bargap=0.4), width="stretch")
        st.caption("Wait = opened_at to work_started_at; fix = work_started_at to available_at. "
                   "Shift from local open hour (shift_roster boundaries: day 06-14, swing 14-22, grave 22-06).")
    with right:
        st.markdown("**Median response hours by local hour the fault opened**")
        hr = (faults.groupby("opened_hour_local").agg(median=("response_h", "median"), n=("operation_id", "count"))
              .reindex(range(24)))
        f5 = go.Figure(go.Scatter(x=hr.index, y=hr["median"], mode="lines+markers",
                                  line=dict(color=PRIMARY, width=2), marker=dict(size=8), customdata=hr["n"],
                                  hovertemplate="%{x}:00: median %{y:.1f} h (n=%{customdata})<extra></extra>"))
        f5.update_xaxes(tickmode="array", tickvals=list(range(0, 24, 3)),
                        ticktext=[f"{h:02d}:00" for h in range(0, 24, 3)])
        st.plotly_chart(style(f5, 280, ".1f"), width="stretch")
        st.caption("Hours with few tickets (hover for n) are noisy.")
    st.dataframe(sh.rename(index=SHIFT_LABEL), width="stretch",
                 column_config={"n": st.column_config.NumberColumn("Tickets", format="%d"),
                                "wait": st.column_config.NumberColumn("Mean wait h", format="%.2f"),
                                "fix": st.column_config.NumberColumn("Mean fix h", format="%.2f"),
                                "median": st.column_config.NumberColumn("Median response h", format="%.2f")})

# ---- Method ----------------------------------------------------------------------------
st.info(
    "**Method for estimated lost coin-in.** Lost hours x that machine's coin-in per available hour in the same "
    "calendar month (ratio of sums). **Assumption:** an hour lost to downtime would have drawn the same coin-in as "
    "the machine's average available hour that month. Faults that hit busy evenings make this an underestimate; "
    "faults overnight make it an overestimate. Guests may also move to a nearby machine, so not all of it is lost "
    "to the floor. Lost theo uses the same method and is what the house actually gives up in expectation."
)

# ---- Source ----------------------------------------------------------------------------
with st.expander("Source"):
    render_evidence(['findings/17-downtime.md'], key='3_downtime')
    st.markdown(
        """
**Mart:** `marts/q3_downtime.parquet`, built by `royale/marts/q3_downtime.py`
(`uv run python -m royale.build q3_downtime`). Two record types: `machine_day` (55,092 on-floor machine-days;
the 1,018 off-floor rows with null `location_id` are excluded) and `ticket` (all 1,226 `operations` rows).
The build asserts both row counts survive the joins.

| Number on this page | Computed as |
|---|---|
| Lost machine-hours | `SUM(calendar_day.scheduled_seconds - machine_day.available_seconds) / 3600` over on-floor machine-days |
| Share of scheduled hours | `SUM(lost_h) / SUM(scheduled_h)` (ratio of sums) |
| Est. lost coin-in | `lost_h x SUM(coin_in) / SUM(available_h)` with the rate per machine x calendar month |
| Est. lost theo | same, with `machine_day.theo_cents` (coin-in x (1 - configured RTP)) |
| Zone, bank | `floor_locations` joined on `machine_day.location_id` (placement at day start), so moved machines count where they were |
| Manufacturer | `machines.manufacturer` |
| Fault tickets | `operations WHERE event_type = 'fault_repair'`, dated by the gaming day containing `opened_at_utc` |
| Wait / fix / response | `work_started_at - opened_at`, `available_at - work_started_at`, `available_at - opened_at` |
| Shift, hour | `hour(opened_at_local)`, bucketed at shift_roster boundaries |

**Limitations.** Lost coin-in is an estimate under the assumption above, not observed play. Downtime includes
moves and installs as well as faults (`available_seconds` subtracts all of them). Response times are means and
medians over tickets; a few long repairs pull the means up. Slot-tech staffing per shift is in `shift_roster`
but not joined here.
"""
    )
