"""Shared daily investigation filters: one period and one bank that survive page changes.

Streamlit removes a widget's state when its page is not rendered, so the shared
values live under private session keys and each page's widgets are seeded from
them. Only pages whose rows are daily machine-days call these helpers. Monthly
guest pages and the May-June model holdout keep their own, labelled scopes.
"""
from datetime import date

import streamlit as st

PRESETS = ("Full period", "Q1", "Q2", "Custom")
# Calendar quarters of the 2025 case, never relative to today.
QUARTERS = {"Q1": (date(2025, 1, 1), date(2025, 3, 31)), "Q2": (date(2025, 4, 1), date(2025, 6, 30))}
DEFAULT_PRESET = "Full period"
ALL_BANKS = "All banks"
PERIOD_STATE = "_shared_analysis_period"
PRESET_STATE = "_shared_period_preset"
BANK_STATE = "_shared_bank"


def preset_range(preset: str, minimum: date, maximum: date):
    """Dates for a preset within the data's bounds; None when the preset has no data here."""
    if preset == "Full period":
        return minimum, maximum
    if preset not in QUARTERS:
        return None
    start, end = QUARTERS[preset]
    start, end = max(start, minimum), min(end, maximum)
    return (start, end) if start <= end else None


def matching_preset(period, minimum: date, maximum: date) -> str:
    for preset in PRESETS[:-1]:
        if preset_range(preset, minimum, maximum) == tuple(period):
            return preset
    return "Custom"


def describe_period(start: date, end: date) -> str:
    days = (end - start).days + 1
    return f"{start:%b %d, %Y}–{end:%b %d, %Y} ({days} day{'s' if days != 1 else ''})"


def _fits(period, minimum, maximum) -> bool:
    return period is not None and minimum <= period[0] <= period[1] <= maximum


def analysis_period(key: str, minimum: date, maximum: date, label: str = "Analysis period") -> tuple[date, date]:
    """Preset + range slider seeded from, and written back to, the shared daily period.

    A shared range outside this page's dates is not clamped or rounded; the page
    shows its full range and says so.
    """
    state = st.session_state
    preset_key, range_key = f"{key}_period_preset", f"{key}_period_range"
    shared = state.get(PERIOD_STATE)
    if shared is not None and not _fits(shared, minimum, maximum):
        st.caption(f"The shared period ({describe_period(*shared)}) is outside this page's data "
                   f"({describe_period(minimum, maximum)}); showing this page's full range instead.")
        shared = None
    if shared is None:
        shared = (minimum, maximum)
    # Seed widgets from the shared values on every run; callbacks keep them in step.
    state[range_key] = tuple(shared)
    # An explicit Custom choice stays Custom even when its range equals a preset.
    state[preset_key] = ("Custom" if state.get(PRESET_STATE) == "Custom"
                         else matching_preset(shared, minimum, maximum))

    def on_preset():
        choice = state[preset_key]
        state[PRESET_STATE] = choice
        dates = preset_range(choice, minimum, maximum)
        if dates is not None:
            state[PERIOD_STATE] = dates

    def on_range():
        state[PERIOD_STATE] = tuple(state[range_key])
        state[PRESET_STATE] = matching_preset(state[range_key], minimum, maximum)

    available = [p for p in PRESETS if p == "Custom" or preset_range(p, minimum, maximum) is not None]
    st.radio("Period preset", available, key=preset_key, on_change=on_preset, horizontal=True,
             help="Q1 = Jan 1–Mar 31 2025, Q2 = Apr 1–Jun 30 2025. Custom keeps the range set below.")
    start, end = st.slider(label, min_value=minimum, max_value=maximum, key=range_key,
                           on_change=on_range, format="MMM D, YYYY")
    return start, end


def bank_drill(key: str, banks, label: str = "Bank drill") -> str:
    """Bank selection shared by Home and Machines, where a bank means the same machines."""
    state = st.session_state
    options = [ALL_BANKS] + sorted(banks)
    widget_key = f"{key}_bank"
    shared = state.get(BANK_STATE, ALL_BANKS)
    if shared not in options:
        st.caption(f"The shared bank {shared} has no rows on this page; showing all banks.")
        shared = ALL_BANKS
    state[widget_key] = shared

    def on_bank():
        state[BANK_STATE] = state[widget_key]

    return st.selectbox(label, options, key=widget_key, on_change=on_bank)


def reset_button(key: str) -> None:
    """Restore the documented default: full period and all banks. Fixed plans are unaffected."""
    def reset():
        for name in (PERIOD_STATE, PRESET_STATE, BANK_STATE):
            st.session_state.pop(name, None)

    st.button("Reset filters", key=f"{key}_reset", on_click=reset,
              help="Back to the full January–June period and all banks.")


def independent_scope_note(scope: str) -> str:
    """Name a page's own scope and say plainly that the shared daily period is not applied."""
    shared = st.session_state.get(PERIOD_STATE)
    active = f" (currently {describe_period(*shared)})" if shared else ""
    return (f"{scope}. The shared daily analysis period{active} is not applied here and is not "
            "rounded or clamped to fit; set this page's period below.")
