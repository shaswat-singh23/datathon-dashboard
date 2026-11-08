"""Shared presentation for The Gilded Ace's eight analytical routes."""
from base64 import b64encode
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

PALETTE = ["#35665D", "#A47734", "#844C57", "#697A91", "#66584C", "#9B6747"]
ROUTES = [
    ("app.py", "Overview"),
    ("pages/1_machines.py", "Machine performance"),
    ("pages/2_demand.py", "Floor demand"),
    ("pages/3_downtime.py", "Availability & downtime"),
    ("pages/4_players.py", "Player outcomes"),
    ("pages/5_comps.py", "Loyalty & comps"),
    ("pages/6_actions.py", "July investment plan"),
    ("pages/7_model.py", "Forecast & validation"),
]


def apply_theme(section: str) -> None:
    """Called after page config on every rerun; keeps all controls native."""
    st.html((Path(__file__).with_name("theme.css")).read_text())
    pio.templates["gilded"] = go.layout.Template(layout=go.Layout(
        colorway=PALETTE,
        font=dict(family="Arial, sans-serif", color="#332D27", size=13),
        title=dict(font=dict(family="Georgia, serif", size=22)),
        paper_bgcolor="#FFFCF7", plot_bgcolor="#FFFCF7",
        xaxis=dict(gridcolor="#E9E1D5", zerolinecolor="#D5C6B0"),
        yaxis=dict(gridcolor="#E9E1D5", zerolinecolor="#D5C6B0"),
        hoverlabel=dict(bgcolor="#29241F", font_color="#FFF8EC"),
        margin=dict(l=24, r=24, t=48, b=32),
    ))
    pio.templates.default = "plotly_white+gilded"
    with st.sidebar:
        st.html('<div class="ga-brand"><div class="ga-crest" aria-hidden="true">♠</div>'
                '<div class="ga-brand-name">The Gilded Ace</div>'
                '<div class="ga-smallcaps">LAS VEGAS · PROPERTY INTELLIGENCE</div>'
                '<div class="ga-suits" aria-hidden="true">♠ <span>♦</span> ♣ <span>♥</span></div></div>')
        st.html('<div class="ga-nav-label">THE PROPERTY REPORT</div>')
        for route, label in ROUTES:
            st.page_link(route, label=label)
        st.html('<div class="ga-sidebar-note"><span class="ga-smallcaps">THE OBSERVATION WINDOW</span>'
                '<p>January — June 2025</p><hr>'
                '<p>Luck, location, or a leak?<br>Follow the evidence.</p>'
                '<small>A fictional casino.<br>Synthetic data. Real analytical rigor.</small></div>')
    # Streamlit sanitizes inline SVG; an image preserves the vector artwork.
    artwork = b64encode(Path(__file__).with_name("casino.svg").read_bytes()).decode("ascii")
    st.html('<div class="ga-masthead"><div class="ga-masthead-copy">'
            '<span class="ga-smallcaps">THE GILDED ACE · LAS VEGAS</span>'
            f'<div class="ga-section">{escape(section)}</div>'
            '<div class="ga-edition">PROPERTY REPORT <span aria-hidden="true">◆</span> JAN — JUN 2025</div>'
            '</div><div class="ga-casino-art" aria-hidden="true">'
            f'<img src="data:image/svg+xml;base64,{artwork}" alt="" /></div></div>')
