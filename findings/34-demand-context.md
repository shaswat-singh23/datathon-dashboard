# Public context and floor demand, January–June 2025
- Issue: #34 | Author: Sahith (Codex) | Time: 13:36 America/Chicago
- Claim: Full-period floor coin-in has weak daily associations with airport maximum temperature (Pearson r = -0.032400) and precipitation (-0.153200). Monthly mean coin-in correlates +0.486678 with Las Vegas visitors per calendar day, but there are only six monthly pairs. These associations do not establish why demand changed.
- Evidence: `uv run python -m royale.build q2_context` produces 181 rows, 15 columns, 15,878 bytes. Inputs have 181 property dates, 181 weather dates, and six tourism months; left joins retain 181 unique property dates with no missing weather or tourism values. Coin-in before and after is $248,905,219.25. The page's correlation table reproduces the results below.
- So what: Public context can frame a demand investigation, but does not justify a machine replacement or a causal intervention.
- Checked by: Kyle (Claude Code, Fable 5.1), 2026-11-07 16:25

| Context | Independent pairs | Raw Pearson r | Weekday-adjusted r |
|---|---:|---:|---:|
| NOAA daily maximum temperature, °C | 181 days | -0.032400 | -0.069087 |
| NOAA daily precipitation, mm | 181 days | -0.153200 | -0.217324 |
| LVCVA visitors / calendar day | 6 months | +0.486678 | not estimated |

Simple baseline / alternative explanation: subtract the selected-period mean for each weekday from both daily coin-in and weather before correlating residuals. This controls only the weekday rhythm; it does not control seasonal trends, events, downtime or serial dependence. Monthly visitor counts are divided by calendar days, compared with monthly mean daily coin-in, and counted once per month (not 181 independent observations). No significance or causal claim is made.

NOAA weather is the Las Vegas airport station USW00023169, matched by calendar date to the same gaming-date label. A gaming day runs 06:00–06:00 local; daily weather cannot be exactly reallocated to that interval. Quality-flagged values are omitted, missing values remain missing, and trace precipitation retains its source numeric value and measurement flag. Airport weather may not represent conditions at the property.

LVCVA covers all Las Vegas visitors, not this fictional casino's guests. Its August 20, 2026 revised series was published after 2025 and is retrospective context only. Neither it nor future observed weather feeds a forecast. Synthetic casino activity and real public context need not share a causal mechanism. A partial-month selection compares only the selected casino days with the full calendar-month visitor intensity; fewer than three months suppresses the correlation.

Reproduce numeric checks after building:
```python
from royale import io
x = io.mart('q2_context')
p = io.table('property_day')
assert len(x) == len(p) == x.gaming_date.nunique() == 181
assert abs(x.coin_in_usd.sum() - float(p.coin_in_usd.sum())) < 1e-6
for col in ['tmax_c', 'prcp_mm']:
    pairs = x[['coin_in_usd', col, 'local_weekday']].dropna()
    residual = pairs[['coin_in_usd', col]] - pairs.groupby('local_weekday')[['coin_in_usd', col]].transform('mean')
    print(col, len(pairs), pairs.coin_in_usd.corr(pairs[col]), residual.coin_in_usd.corr(residual[col]))
m = x.groupby('month')[['coin_in_usd', 'visitors_per_calendar_day']].mean().dropna()
print(len(m), m.coin_in_usd.corr(m.visitors_per_calendar_day))
```

Verification: `uv run pytest -q`: 45 passed. Streamlit AppTest loads the full page without exceptions, changes the zone drill, selects Feb 1–15 (15 daily pairs and one monthly pair, monthly r suppressed), and switches through all three overlays. An in-memory duplicate weather date causes the builder to reject the join. Only committed marts are read by the page.
