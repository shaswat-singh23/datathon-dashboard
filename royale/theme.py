"""Shared presentation for The Gilded Ace's eight analytical routes."""
from base64 import b64encode
from functools import cache
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Surfaces and text. Gold is for navigation and emphasis, not for data series.
ESPRESSO, IVORY, PAPER, INK = "#29241F", "#F7F3EB", "#FFFCF7", "#332D27"
BRASS, GOLD, DEEP_GREEN = "#7F5D27", "#D3B67D", "#1F3A32"
# Distinct data series (each >= 3:1 against the ivory chart paper); pair them with labels or dashes.
PALETTE = ["#2E6B5E", "#3F6497", "#8A5A1C", "#6A4C8C", "#6B5A4A", "#23798A"]
# Red is reserved for adverse outcomes.
ADVERSE = "#A3362B"
# Story groups over the unchanged route paths.
NAV_GROUPS = [
    ("OVERVIEW", [("app.py", "Overview")]),
    ("INVESTIGATE", [("pages/1_machines.py", "Machine performance"),
                     ("pages/2_demand.py", "Floor demand"),
                     ("pages/3_downtime.py", "Availability & downtime")]),
    ("GUESTS & LOYALTY", [("pages/4_players.py", "Player outcomes"),
                          ("pages/5_comps.py", "Loyalty & comps")]),
    ("DECIDE & VALIDATE", [("pages/6_actions.py", "July investment plan"),
                           ("pages/7_model.py", "Forecast & validation")]),
]
ROUTES = [route for _, routes in NAV_GROUPS for route in routes]


def short_usd(value: float, decimals: int = 1) -> str:
    """Readable display form of a dollar amount: $248.9M, $41.3k, −$5.3k, $189.

    Display only. Pages pass the exact value alongside (``exact_usd``) wherever it is shown.
    """
    sign, size = ("−" if value < 0 else ""), abs(value)
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if size >= limit:
            return f"{sign}${size / limit:,.{decimals}f}{suffix}"
    return f"{sign}${size:,.0f}"


def exact_usd(value: float, cents: bool = False) -> str:
    """Labeled exact value for a metric's help detail."""
    sign = "−" if value < 0 else ""
    return f"Exact: {sign}${abs(value):,.{2 if cents else 0}f}"


@cache
def _artwork() -> str:
    # Streamlit sanitizes inline SVG; an image preserves the vector artwork.
    return b64encode(Path(__file__).with_name("casino.svg").read_bytes()).decode("ascii")


def _art(css_class: str) -> str:
    return (f'<div class="{css_class}" aria-hidden="true">'
            f'<img src="data:image/svg+xml;base64,{_artwork()}" alt="" /></div>')


def casino_art() -> None:
    """Home on narrow screens: the illustration after the decision, not above it."""
    st.html(_art("ga-casino-art ga-art-after"))


def apply_theme(section: str, *, compact: bool = False) -> None:
    """Called after page config on every rerun; keeps all controls native.

    Home uses the full illustrated masthead; inner pages pass ``compact=True`` for a
    short crest-and-label header so results start near the top of the page.
    """
    st.html((Path(__file__).with_name("theme.css")).read_text())
    pio.templates["gilded"] = go.layout.Template(layout=go.Layout(
        colorway=PALETTE,
        font=dict(family="'Source Sans Pro', Arial, sans-serif", color=INK, size=13),
        title=dict(font=dict(family="Georgia, serif", size=20)),
        paper_bgcolor=PAPER, plot_bgcolor=PAPER,
        xaxis=dict(gridcolor="#E9E1D5", zerolinecolor="#D5C6B0"),
        yaxis=dict(gridcolor="#E9E1D5", zerolinecolor="#D5C6B0"),
        hoverlabel=dict(bgcolor=ESPRESSO, font_color="#FFF8EC"),
        legend=dict(font=dict(size=12)),
        margin=dict(l=24, r=24, t=48, b=32),
    ))
    pio.templates.default = "plotly_white+gilded"
    with st.sidebar:
        st.html('<div class="ga-brand"><div class="ga-crest" aria-hidden="true">♠</div>'
                '<div class="ga-brand-name">The Gilded Ace</div>'
                '<div class="ga-smallcaps">LAS VEGAS · PROPERTY INTELLIGENCE</div>'
                '<div class="ga-suits" aria-hidden="true">♠ <span>♦</span> ♣ <span>♥</span></div></div>')
        for group, routes in NAV_GROUPS:
            st.html(f'<div class="ga-nav-label">{escape(group)}</div>')
            for route, label in routes:
                st.page_link(route, label=label)
        st.html('<div class="ga-sidebar-note"><span class="ga-smallcaps">THE OBSERVATION WINDOW</span>'
                '<p>January — June 2025</p><hr>'
                '<p>Luck, location, or a leak?<br>Follow the evidence.</p>'
                '<small>A fictional casino.<br>Synthetic data. Real analytical rigor.</small></div>')
    if compact:
        st.html('<header class="ga-masthead ga-masthead--compact">'
                '<div class="ga-mini-crest" aria-hidden="true">♠</div>'
                '<div class="ga-masthead-copy"><span class="ga-smallcaps">THE GILDED ACE · LAS VEGAS</span>'
                f'<div class="ga-section">{escape(section)}</div></div>'
                '<div class="ga-edition">PROPERTY REPORT <span aria-hidden="true">◆</span> JAN — JUN 2025<br>'
                'FICTIONAL CASINO · SYNTHETIC DATA</div></header>')
        return
    st.html('<header class="ga-masthead ga-masthead--home"><div class="ga-masthead-copy">'
            '<span class="ga-smallcaps">THE GILDED ACE · LAS VEGAS <span aria-hidden="true">◆</span> '
            'PROPERTY REPORT, JAN — JUN 2025</span>'
            f'<div class="ga-section">{escape(section)}</div>'
            '<div class="ga-edition">FICTIONAL CASINO · SYNTHETIC DATA</div>'
            f'</div>{_art("ga-casino-art ga-art-masthead")}</header>')
