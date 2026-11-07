"""Q2: What changed in demand across the floor over the six months, and why?

Reads only io.mart("q2_demand") (one row per zone x gaming date). Every rate is a ratio of sums.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from royale import io

st.set_page_config(page_title="Demand: The Gilded Ace", page_icon="♠", layout="wide")

BLUE = "#2a78d6"      # series 1: the selected zone / the floor
ORANGE = "#eb6834"    # series 2: comparison (rest of floor)
EVENT_FILL = "rgba(82, 81, 78, 0.12)"
CLOSURE_FILL = "rgba(235, 104, 52, 0.14)"
SEQ_SCALE = [[0, "#eef4fc"], [1, "#16447d"]]  # one hue, light to dark


def ratio(num: pd.Series, den: pd.Series) -> float:
    """Ratio of sums; NaN when the denominator sums to zero.
    Same rule as money.per_available_hour (issue #14); local until that merges."""
    d = den.sum()
    return num.sum() / d if d else float("nan")


def windows(days: pd.DataFrame, col: str) -> list[tuple[str, pd.Timestamp, pd.Timestamp]]:
    """Contiguous date runs for each distinct non-null label in `col`."""
    out = []
    lab = days[["gaming_date", col]].dropna().drop_duplicates().sort_values("gaming_date")
    for name, g in lab.groupby(col):
        dates = g["gaming_date"].sort_values()
        run_start = prev = dates.iloc[0]
        for d in dates.iloc[1:]:
            if (d - prev).days > 1:
                out.append((name, run_start, prev))
                run_start = d
            prev = d
        out.append((name, run_start, prev))
    return out


def shade(fig: go.Figure, view: pd.DataFrame) -> None:
    for name, a, b in windows(view, "events_active"):
        fig.add_vrect(x0=a - pd.Timedelta(hours=12), x1=b + pd.Timedelta(hours=12), fillcolor=EVENT_FILL,
                      line_width=0, layer="below", annotation_text=name, annotation_position="top left",
                      annotation_font_size=10, annotation_textangle=-90)
    for name, a, b in windows(view, "closures_active"):
        fig.add_vrect(x0=a - pd.Timedelta(hours=12), x1=b + pd.Timedelta(hours=12), fillcolor=CLOSURE_FILL,
                      line_width=0, layer="below", annotation_text="Walkway closed: " + name.split(" (")[0],
                      annotation_position="bottom left", annotation_font_size=10)


def style(fig: go.Figure, height: int = 320, yfmt: str = "$,.0f") -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
                      legend=dict(orientation="h", y=1.08, x=0))
    fig.update_yaxes(tickformat=yfmt, gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


st.title("What changed in demand, and why?")
st.caption("Coin-in, occupied machine-hours and zone counter entries by day, week, month, weekday, zone and event. "
           "Rates are ratios of sums over on-floor machines only.")

try:
    df = io.mart("q2_demand")
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()
df["gaming_date"] = pd.to_datetime(df["gaming_date"])

# ---- Filters: period + zone drill, in one row --------------------------------------------
dmin, dmax = df["gaming_date"].min().date(), df["gaming_date"].max().date()
c1, c2 = st.columns([3, 1])
start, end = c1.slider("Analysis period", min_value=dmin, max_value=dmax, value=(dmin, dmax), format="MMM D")
zones = df[["zone_id", "zone_name"]].drop_duplicates().sort_values("zone_name")
zone_label = dict(zip(zones["zone_id"], zones["zone_name"]))
zone = c2.selectbox("Zone drill", ["All zones"] + list(zones["zone_id"]),
                    format_func=lambda z: z if z == "All zones" else f"{zone_label[z]} ({z})")

view = df[(df["gaming_date"].dt.date >= start) & (df["gaming_date"].dt.date <= end)]
if view.empty:
    st.warning("No gaming days in that period.")
    st.stop()
scope = view if zone == "All zones" else view[view["zone_id"] == zone]
scope_name = "the whole floor" if zone == "All zones" else zone_label[zone]

daily = (scope.groupby(["gaming_date", "month", "local_weekday"], as_index=False)
         .agg(coin_in_usd=("coin_in_usd", "sum"), occupied_hours=("occupied_hours", "sum"),
              available_hours=("available_hours", "sum"), zone_entries=("zone_entries_observed", "sum"))
         .merge(view[["gaming_date", "events_active", "closures_active"]].drop_duplicates(), on="gaming_date"))
ndays = len(daily)

# ---- KPIs ------------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Coin-in per day", f"${daily['coin_in_usd'].sum() / ndays / 1e3:,.0f}k",
          help=f"Sum of coin-in over {ndays} gaming days, {scope_name}.")
k2.metric("Occupied machine-hours per day", f"{daily['occupied_hours'].sum() / ndays:,.0f}")
k3.metric("Zone entries per day", f"{daily['zone_entries'].sum() / ndays:,.0f}",
          help="Counter crossings, not unique people. Offline counter hours are missing, not zero.")
k4.metric("Coin-in per available machine-hour", f"${ratio(daily['coin_in_usd'], daily['available_hours']):,.1f}")

# ---- Trend -----------------------------------------------------------------------------
st.subheader(f"Coin-in trend, {scope_name}")
grain = st.radio("Grain", ["Daily", "Weekly (mean per day)"], horizontal=True, label_visibility="collapsed")
if grain == "Daily":
    tr = daily[["gaming_date", "coin_in_usd"]]
    hover = "%{x|%a %b %d}: $%{y:,.0f}<extra></extra>"
else:
    tr = (daily.assign(week=daily["gaming_date"].dt.to_period("W-SUN").dt.start_time)
          .groupby("week", as_index=False).agg(coin_in_usd=("coin_in_usd", "mean"), n=("coin_in_usd", "size"))
          .rename(columns={"week": "gaming_date"}))
    hover = "Week of %{x|%b %d}: $%{y:,.0f}/day<extra></extra>"
fig = go.Figure(go.Scatter(x=tr["gaming_date"], y=tr["coin_in_usd"], mode="lines", line=dict(color=BLUE, width=2),
                           name="Coin-in", hovertemplate=hover))
shade(fig, view)
st.plotly_chart(style(fig), width="stretch")
st.caption("Gray bands: events (events table). Orange band: walkway closure (floor_walkways). "
           "Weekly points are the mean daily coin-in for the days of that week inside the period.")

# ---- Month over month ------------------------------------------------------------------
st.subheader("Month over month")
mo = (daily.groupby("month")
      .agg(days=("gaming_date", "size"), coin_in=("coin_in_usd", "sum"), occupied=("occupied_hours", "sum"),
           entries=("zone_entries", "sum"), available=("available_hours", "sum")))
mo["coin_in_per_day"] = mo["coin_in"] / mo["days"]
mo["occupied_per_day"] = mo["occupied"] / mo["days"]
mo["entries_per_day"] = mo["entries"] / mo["days"]
mo["coin_in_per_avail_hr"] = mo["coin_in"] / mo["available"]
mo["coin_in_per_day_mom"] = mo["coin_in_per_day"].pct_change()
mo["entries_per_day_mom"] = mo["entries_per_day"].pct_change()
st.dataframe(
    mo[["days", "coin_in", "coin_in_per_day", "coin_in_per_day_mom", "occupied", "occupied_per_day",
        "entries", "entries_per_day", "entries_per_day_mom", "coin_in_per_avail_hr"]],
    width="stretch",
    column_config={
        "days": st.column_config.NumberColumn("Days"),
        "coin_in": st.column_config.NumberColumn("Coin-in", format="$%,.0f"),
        "coin_in_per_day": st.column_config.NumberColumn("Coin-in / day", format="$%,.0f"),
        "coin_in_per_day_mom": st.column_config.NumberColumn("MoM (per day)", format="percent"),
        "occupied": st.column_config.NumberColumn("Occupied hrs", format="%,.0f"),
        "occupied_per_day": st.column_config.NumberColumn("Occupied hrs / day", format="%,.0f"),
        "entries": st.column_config.NumberColumn("Zone entries", format="%,.0f"),
        "entries_per_day": st.column_config.NumberColumn("Entries / day", format="%,.0f"),
        "entries_per_day_mom": st.column_config.NumberColumn("MoM (per day)", format="percent"),
        "coin_in_per_avail_hr": st.column_config.NumberColumn("Coin-in / avail. hr", format="$%.1f"),
    },
)
st.caption("Months have different lengths (Feb has 28 days), so compare the per-day columns. "
           "A period that cuts a month shows only the days inside it.")

# ---- Weekday and events ----------------------------------------------------------------
left, right = st.columns(2)
plain = daily[daily["events_active"].isna()]
order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
wd = plain.groupby("local_weekday")["coin_in_usd"].mean().reindex(order)
with left:
    st.subheader("Weekday rhythm (non-event days)")
    f2 = go.Figure(go.Bar(x=wd.index, y=wd.values, marker_color=BLUE, marker_line_width=0,
                          hovertemplate="%{x}: $%{y:,.0f}/day<extra></extra>"))
    st.plotly_chart(style(f2, 280).update_layout(hovermode="closest", bargap=0.35), width="stretch")

with right:
    st.subheader("Event days vs same weekday")
    base = plain.groupby("local_weekday")["coin_in_usd"].mean()
    ev = daily[daily["events_active"].notna()].copy()
    if ev.empty or base.empty:
        st.info("No event days (or no non-event baseline) in this period.")
    else:
        ev["expected"] = ev["local_weekday"].map(base)
        et = (ev.groupby("events_active")
              .agg(days=("gaming_date", "size"), first_day=("gaming_date", "min"),
                   coin_in_per_day=("coin_in_usd", "mean"), actual=("coin_in_usd", "sum"),
                   expected=("expected", "sum")))
        et["lift"] = et["actual"] / et["expected"] - 1
        st.dataframe(et.sort_values("first_day")[["first_day", "days", "coin_in_per_day", "lift"]],
                     width="stretch",
                     column_config={"first_day": st.column_config.DateColumn("Starts", format="MMM D"),
                                    "days": "Days",
                                    "coin_in_per_day": st.column_config.NumberColumn("Coin-in / day", format="$%,.0f"),
                                    "lift": st.column_config.NumberColumn("vs same weekday", format="percent")})
        st.caption("Lift = event-day coin-in / mean coin-in of non-event days with the same weekday, minus 1. "
                   "3 to 7 days per event: treat as directional.")

# ---- Zone drill ------------------------------------------------------------------------
st.subheader("Zones: coin-in per available machine-hour")
zm = (view.groupby(["zone_id", "month"])
      .apply(lambda g: ratio(g["coin_in_usd"], g["available_hours"]), include_groups=False)
      .unstack("month"))
zm.index = [f"{zone_label[z]}" for z in zm.index]
heat = go.Figure(go.Heatmap(z=zm.values, x=list(zm.columns), y=list(zm.index), colorscale=SEQ_SCALE,
                            text=[[f"${v:,.0f}" for v in row] for row in zm.values], texttemplate="%{text}",
                            hovertemplate="%{y}, %{x}: $%{z:,.1f} per available machine-hour<extra></extra>",
                            xgap=2, ygap=2, colorbar=dict(title="$/hr", tickprefix="$")))
st.plotly_chart(style(heat, 300).update_layout(hovermode="closest"), width="stretch")

if zone != "All zones":
    z_in = view[view["zone_id"] == zone]
    z_out = view[view["zone_id"] != zone]

    def weekly(d: pd.DataFrame) -> pd.DataFrame:
        w = d.assign(week=d["gaming_date"].dt.to_period("W-SUN").dt.start_time).groupby("week")
        return pd.DataFrame({"cpah": w["coin_in_usd"].sum() / w["available_hours"].sum()})

    wz, wr = weekly(z_in), weekly(z_out)
    f3 = go.Figure()
    f3.add_scatter(x=wz.index, y=wz["cpah"], name=zone_label[zone], line=dict(color=BLUE, width=2),
                   hovertemplate="%{y:$,.1f}")
    f3.add_scatter(x=wr.index, y=wr["cpah"], name="Rest of floor", line=dict(color=ORANGE, width=2),
                   hovertemplate="%{y:$,.1f}")
    for s, color in ((wz, BLUE), (wr, ORANGE)):
        f3.add_annotation(x=s.index[-1], y=s["cpah"].iloc[-1], xanchor="left", showarrow=False,
                          text=f" {zone_label[zone] if s is wz else 'Rest of floor'}", font=dict(size=11))
    shade(f3, view)
    st.markdown(f"**{zone_label[zone]} vs rest of floor**, weekly coin-in per available machine-hour")
    st.plotly_chart(style(f3, 300, "$,.0f"), width="stretch")

    zk1, zk2, zk3 = st.columns(3)
    zk1.metric("Occupancy (occupied / available hrs)", f"{ratio(z_in['occupied_hours'], z_in['available_hours']):.1%}")
    zk2.metric("Coin-in per occupied hour", f"${ratio(z_in['coin_in_usd'], z_in['occupied_hours']):,.0f}",
               help="Spend intensity once a guest sits down. Flat while occupancy falls = fewer guests, same bets.")
    zk3.metric("Zone entries per day", f"{z_in['zone_entries_observed'].sum() / z_in['gaming_date'].nunique():,.0f}")
else:
    st.caption("Pick a zone in **Zone drill** above to compare it with the rest of the floor week by week.")

# ---- Context ---------------------------------------------------------------------------
st.subheader("Context: weather and Las Vegas visitors")
st.caption("This section always compares public context with whole-floor coin-in; the zone drill above "
           "applies to the floor analysis only. The analysis period applies here too.")
st.info("NOAA airport weather uses calendar dates, matched to the same gaming-date label. "
        "Casino days run 06:00–06:00 local, so these are overlapping, not identical windows. "
        "LVCVA visitors describe all Las Vegas, not this casino's guests. The tourism series was "
        "published after 2025 (revision August 20, 2026). These are retrospective associations, "
        "not causal effects or forecast inputs; future actual weather is also unavailable to a forecast.")
try:
    context = io.mart("q2_context")
except FileNotFoundError as err:
    st.warning(str(err))
else:
    context["gaming_date"] = pd.to_datetime(context["gaming_date"])
    context = context[context["gaming_date"].dt.date.between(start, end)].copy()
    if context.empty:
        st.info("No public context in this period.")
    else:
        metric = st.selectbox("Context overlay", ["tmax_c", "prcp_mm", "visitors_per_calendar_day"],
                              format_func=lambda x: {"tmax_c": "NOAA maximum temperature (°C)",
                                  "prcp_mm": "NOAA precipitation (mm)",
                                  "visitors_per_calendar_day": "LVCVA visitors / calendar day (monthly mean)"}[x])
        cf = go.Figure()
        cf.add_scatter(x=context["gaming_date"], y=context["coin_in_usd"], name="Whole-floor coin-in",
                       line=dict(color=BLUE), hovertemplate="$%{y:,.0f}")
        cf.add_scatter(x=context["gaming_date"], y=context[metric], name=metric,
                       yaxis="y2", line=dict(color=ORANGE), connectgaps=False)
        cf = style(cf, 340)
        cf.update_layout(yaxis=dict(title="Coin-in ($)"),
                         yaxis2=dict(title={"tmax_c": "Temperature (°C)", "prcp_mm": "Rain (mm)",
                             "visitors_per_calendar_day": "Visitors / day"}[metric],
                             overlaying="y", side="right", showgrid=False))
        st.plotly_chart(cf, width="stretch")

        rows = []
        # Daily weather correlations vs a simple same-weekday baseline adjustment.
        for col, label in [("tmax_c", "Maximum temperature"), ("prcp_mm", "Precipitation")]:
            pairs = context[["coin_in_usd", col, "local_weekday"]].dropna().copy()
            residual = pairs[["coin_in_usd", col]] - pairs.groupby("local_weekday")[["coin_in_usd", col]].transform("mean")
            rows.append({"Context": label, "Unit": "paired days", "N": len(pairs),
                         "Pearson r": pairs["coin_in_usd"].corr(pairs[col]) if len(pairs) >= 3 else float("nan"),
                         "r after weekday adjustment": residual["coin_in_usd"].corr(residual[col]) if len(pairs) >= 3 else float("nan")})
        # One pair per month: repeated daily tourism values are not independent observations.
        monthly = context.groupby("month")[["coin_in_usd", "visitors_per_calendar_day"]].mean().dropna()
        rows.append({"Context": "Las Vegas visitors / day", "Unit": "months", "N": len(monthly),
                     "Pearson r": monthly["coin_in_usd"].corr(monthly["visitors_per_calendar_day"]) if len(monthly) >= 3 else float("nan"),
                     "r after weekday adjustment": float("nan")})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption("Pearson r uses complete pairs; fewer than 3 pairs or constant values give no estimate. "
                   "Weather adjustment subtracts each weekday's selected-period mean from both series "
                   "(a simple weekday baseline). Tourism correlates monthly mean coin-in with monthly "
                   "visitors / calendar day, with at most six independent months; partial months use only "
                   "selected casino days. No p-values or causal claims: seasonality, events and serial "
                   "dependence can explain correlations. Missing/quality-flagged weather stays missing; "
                   "NOAA trace rain retains its source numeric value, not an exact zero-rain claim.")
        with st.expander("Context Source"):
            st.markdown("`marts/q2_context.parquet`, built with `uv run python -m royale.build q2_context`. "
                        "Left joins: property_day.gaming_date = weather_daily.source_date; "
                        "gaming month = city_visitation_monthly.month. Monthly visitor counts are divided "
                        "by calendar days in the month, then repeated for display only. "
                        "Duplicate join keys are rejected; all property dates are retained. "
                        "See `findings/34-demand-context.md` for full-period correlations and checks.")
            for col, label in [("weather_source_url", "NOAA GHCN-Daily, USW00023169"),
                               ("tourism_source_url", "LVCVA revised 2025 tourism indicators")]:
                for url in context[col].dropna().unique():
                    st.markdown(f"[{label}]({url})")

# ---- Source ----------------------------------------------------------------------------
with st.expander("Source"):
    st.markdown(
        """
**Mart:** `marts/q2_demand.parquet`, built by `royale/marts/q2_demand.py` (`uv run python -m royale.build q2_demand`).
One row per zone x gaming date (7 x 181 = 1,267 rows). Daily floor totals reconcile exactly with `property_day`
(coin-in, available machine-hours, total zone entries).

| Number on this page | Computed as |
|---|---|
| Coin-in, occupied hours, available hours | `SUM(coin_in_usd)`, `SUM(occupied_hours)`, `SUM(available_hours)` from `prepared_daily_view WHERE location_id IS NOT NULL`, grouped by zone and day |
| Zone entries | `zone_entries_observed`, taken once per zone-day (it repeats on every machine row), summed over zones |
| Per day | period sum / number of gaming days |
| Coin-in per available machine-hour | `SUM(coin_in_usd) / SUM(available_hours)` (ratio of sums) |
| Occupancy | `SUM(occupied_hours) / SUM(available_hours)` |
| Event windows | `property_day.events_active` (from the `events` table) |
| Walkway closure | `floor_walkways.closed_from_utc / closed_to_utc` overlapped with `calendar_day` gaming-day bounds |
| Event lift | event-day coin-in / mean coin-in of non-event days with the same weekday in the period, minus 1 |

**Limitations.** Zone entries are sensor crossings, not unique people; offline counter hours are missing, not zero
(coverage is in `zone_counter_coverage_hours`). Event comparisons rest on 3 to 7 days each.
The separate Context section uses `q2_context`; see its source expander and retrospective-use caveats.
"""
    )
