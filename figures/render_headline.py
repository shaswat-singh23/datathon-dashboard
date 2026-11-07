"""Render the existing demand finding from committed marts; no raw data required."""
from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go

from royale import io, money


def render(destination: Path) -> None:
    data = io.mart("q2_demand")
    dates = pd.to_datetime(data.gaming_date)
    windows = [
        ("Before", "2025-01-27", "2025-03-02", "Jan 27–Mar 2"),
        ("During closure", "2025-03-03", "2025-04-06", "Mar 3–Apr 6"),
        ("After", "2025-04-07", "2025-05-11", "Apr 7–May 11"),
    ]
    expected = {"Back Forty": [135.5, 96.3, 125.9], "Rest of floor": [206.1, 210.7, 197.4]}
    chart = go.Figure()
    for label, color in [("Back Forty", "#234f3b"), ("Rest of floor", "#b4592a")]:
        values = []
        for _, start, end, _ in windows:
            period = data[dates.between(start, end)]
            assert period.gaming_date.nunique() == 35
            group = period[period.zone_id.eq("Z-B40") == (label == "Back Forty")]
            values.append(money.per_available_hour(group.coin_in_usd, group.available_hours))
        assert [round(value, 1) for value in values] == expected[label], label
        chart.add_scatter(
            x=[0, 1, 2], y=values, name=label, mode="lines+markers+text",
            line={"color": color, "width": 4}, marker={"size": 12},
            text=[f"${value:.1f}" for value in values], textposition="top center",
            textfont={"size": 24, "color": color}, cliponaxis=False,
        )
        print(label, [round(value, 1) for value in values])
    chart.add_vrect(x0=0.6, x1=1.4, fillcolor="#f2e6d8", line_width=0, layer="below")
    chart.update_layout(
        width=1312, height=590, paper_bgcolor="#f3f3ee", plot_bgcolor="#f3f3ee",
        font={"family": "Arial, sans-serif", "size": 18, "color": "#1f3a2e"},
        margin={"l": 94, "r": 60, "t": 65, "b": 75},
        legend={"orientation": "h", "x": 0, "y": 1.16, "font": {"size": 20}},
        xaxis={"tickmode": "array", "tickvals": [0, 1, 2], "range": [-0.15, 2.15],
               "ticktext": [f"{phase}<br>{dates}" for phase, _, _, dates in windows],
               "showgrid": False, "zeroline": False},
        yaxis={"range": [0, 245], "dtick": 50, "tickprefix": "$", "gridcolor": "#d9dfd7",
               "zerolinecolor": "#9cae9f", "title": {"text": "Coin-in / available machine-hour"}},
    )
    plot = chart.to_html(full_html=False, include_plotlyjs=True, config={"displayModeBar": False})
    destination.write_text("""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Back Forty demand comparison</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f3f3ee;color:#1f3a2e;
font-family:Arial,sans-serif}main{width:1440px;padding:44px 64px 30px}
.eyebrow{font-size:16px;letter-spacing:1.4px;font-weight:bold;color:#596d5f}
h1{font-size:39px;line-height:1.17;margin:14px 0 10px}p{margin:0;font-size:20px;line-height:1.5}
footer{border-top:1px solid #cbd5c9;padding-top:16px;font-size:16px;line-height:1.6}
.status{color:#805026;font-size:16px;margin-top:8px}</style>
<main><div class="eyebrow">THE GILDED ACE · DEMAND / LOCATION</div>
<h1>Back Forty demand fell during the walkway closure</h1>
<p>The rest of the floor provides a comparison for the same three windows.</p>
<p class="status">Provisional · Source finding awaits independent review</p>
""" + plot + """<footer>
Gaming dates in 2025 · Each window: 35 days · Rates = total coin-in / total available machine-hours<br>
Descriptive association; machine mix, renovation and seasonality remain alternative explanations.<br>
Source: findings/16-demand-changes.md · marts/q2_demand.parquet · Synthetic casino data
</footer></main></html>""", encoding="utf-8")


if __name__ == "__main__":
    render(Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/26-headline.html"))
