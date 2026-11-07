"""Dashboard Royale: The Gilded Ace. Home page. One page per question lives in pages/."""
import streamlit as st

from royale import config, io

st.set_page_config(page_title="The Gilded Ace: Luck, Location, or a Leak?", page_icon="♠", layout="wide")

st.title("Luck, location, or a leak?")
st.caption(
    "Management plans to replace the ten machines that earned the least between "
    "January 1 and June 30, 2025. This dashboard tests whether that is the right call."
)

try:
    floor = io.mart("property_day")
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()

months = sorted(floor["month"].unique())
start, end = st.select_slider("Analysis period", options=months, value=(months[0], months[-1]))
view = floor[(floor["month"] >= start) & (floor["month"] <= end)]

coin_in = view["coin_in_usd"].sum()
house_win = view["house_win_usd"].sum()
theo = view["theo_usd"].sum()
hold = house_win / coin_in if coin_in else float("nan")
avail = view["available_machine_hours"].sum() / (
    (view["active_machines"] * view["scheduled_seconds"] / 3600).sum()
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Coin-in", f"${coin_in / 1e6:,.1f}M")
k2.metric("House win", f"${house_win / 1e6:,.2f}M", f"{(house_win - theo) / 1e3:+,.0f}k vs theo")
k3.metric("Observed hold", f"{hold:.2%}", f"theo {theo / coin_in:.2%}" if coin_in else None)
k4.metric("Availability", f"{avail:.1%}")

st.line_chart(view.set_index("gaming_date")[["coin_in_usd"]], height=240)

st.markdown(
    """
**The six questions** (one page each, in the sidebar):
1. Which machines are *truly* underperforming once exposure, availability and luck are accounted for?
2. What changed in demand across the floor, and why?
3. How much play was lost to downtime, and when?
4. What did tracked players wager, get back and net, and how concentrated are the results?
5. What did the comp program cost, and did anything change?
6. Which actions would we fund with $100,000, and how would we know they worked?

Plus a **Model** page: a forecast tested on a time-based holdout against a simple baseline.
"""
)
st.caption(f"Window {config.WINDOW_START} to {config.WINDOW_END}. Fictional casino, synthetic data. Ratios are ratios of sums.")
