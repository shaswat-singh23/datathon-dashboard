# Tracked-player outcomes and concentration
- Issue: #18 | Author: dandelino-del (Codex) | Time: 12:56 America/Chicago, 2026-11-07
- Claim: Monthly top-10% active carded players account for 39.01–39.99% of wagers and 39.29–40.58% of gross player losses. Monthly shares ahead range from 15.78% to 16.81%.
- Evidence: `DATA_DIR=/path/to/organizer/data uv run python -m royale.build q4_players`, followed by the reproduction command below. Source is organizer release 0.9.0-draft, player_period (downloaded 2026-11-07).
- So what: Tracked activity is concentrated compared with an equal-share baseline. Report the winners alongside losses. Use these summaries to understand exposure and outcomes, not to encourage heavy losers to gamble more.
- Checked by: Kyle (Claude Code, Fable 5.1), 2026-11-07 16:26

## Totals and baseline

Jan–Jun tracked wagers: **$163,804,869.65**; payouts: **$148,219,409.05**; player net: **−$15,585,460.60**. Expected house win (theo): **$15,485,020.9805**; player luck residual (net + theo): **−$100,439.6195**. Net = payout − coin-in, so positive means the player is ahead. These signs match the organizer's [data dictionary](https://github.com/tamu-datathon-org/dashboard-royale/blob/main/reference/DATA_DICTIONARY.md#player_period).

Equal-share baseline: a top group containing ceil(n × 1% or 10%) players holds ceil(n × fraction) / n of the amount if all active players wager or lose equally, approximately 1% and 10%. Observed wager shares are about 7–8 times that baseline for the top 1%, and about 4 times for the top 10%. These are descriptive comparisons, not causal effects or predictions.

| Gaming month | Active players | Ahead | Top 1% wagers | Top 10% wagers | Top 1% gross loss | Top 10% gross loss |
|---|---:|---:|---:|---:|---:|---:|
| 2025-01 | 21,687 | 16.49% | 7.69% | 39.99% | 7.98% | 40.58% |
| 2025-02 | 21,158 | 16.40% | 7.63% | 39.01% | 7.60% | 39.29% |
| 2025-03 | 23,141 | 16.22% | 7.70% | 39.79% | 7.91% | 39.89% |
| 2025-04 | 21,554 | 16.73% | 7.83% | 39.71% | 7.95% | 40.39% |
| 2025-05 | 22,856 | 16.81% | 7.67% | 39.50% | 7.90% | 40.14% |
| 2025-06 | 20,577 | 15.78% | 7.42% | 39.15% | 7.56% | 39.59% |

## Definitions, alternative and limits

Active means positive tracked coin-in in the month; ledger-only accounts are excluded from concentration and ahead-share denominators. Ahead means strictly positive tracked net. Wagers and losses are ranked independently within each month and filtered guest group; the top groups need not be the same players. Each population includes winners and break-even players.

Gross loss = max(−tracked net, 0) for each player-month. Winners have zero loss, which permits a monotonic Lorenz curve. The alternative signed-loss denominator (sum of coin-in − payout, offset by winners' gains) produces top-10% loss shares of 60.30%, 57.06%, 59.98%, 61.16%, 60.51%, 57.61% from Jan through Jun. Thus the denominator materially affects the displayed share; the page explicitly labels gross loss. Both definitions show concentration relative to equal shares. Neither identifies a persistent high-loss cohort across months.

Uncarded play is invisible. Coin-in includes replayed winnings and is not cash spent. The player net excludes comps and POS activity, and does not measure a whole trip. Opening tier, region and age comparisons are descriptive and have different play exposure/mix; no causal group differences are claimed. No sampling confidence interval is claimed for this complete synthetic recorded window. Monthly summaries cannot support partial-day or partial-month filters.

## Integrity and implementation

The builder projects player_period without joins: **148,893 rows before and after**, unique by player_id + period_month. It checks both sign identities against source columns. The mart stores wagers, payout and theo; net and residual are reconstructed from the checked identities to avoid redundant stored columns. All five resulting monetary totals reconcile to source sums within **$0.000001**. Missing demographics are retained as Unknown. The committed mart is **4,095,807 bytes**, below 5 MB.

The page reads only `io.mart('q4_players')`. Monthly shares are computed after applying gaming-month, home-region, age-band and opening-tier filters. It includes five KPIs, monthly outcomes and ahead shares, independent top-1%/10% shares, an interactive Lorenz chart with equal-share baseline, group comparisons, and a Source expander with the raw projection query and formulas.

## Reproduce the result and independent checks

Run from the repo root with DATA_DIR pointing at the organizer data:

```bash
uv run python -m royale.build q4_players
uv run python - <<'PY'
import math
from royale import io
from royale.marts.q4_players import MONEY, outcomes, monthly_summary
m = outcomes(io.mart('q4_players'))
raw = io.table('player_period')
assert len(m) == len(raw) == 148893
assert not m.duplicated(['player_id', 'period_month']).any()
assert io.mart_path('q4_players').stat().st_size < 5 * 1024 * 1024
for col in MONEY:
    assert abs(m[col].sum() - float(raw[col].sum())) < 1e-6
print(m[MONEY].sum())
print(monthly_summary(m).to_string(index=False))
for month, g in m.groupby('period_month'):
    a = g[g.tracked_coin_in_usd > 0]
    row = monthly_summary(g).iloc[0]
    assert abs(row.ahead_share - (a.tracked_net_usd > 0).mean()) < 1e-12
    for label, values in [('coin_in', a.tracked_coin_in_usd),
                          ('loss', (-a.tracked_net_usd).clip(lower=0))]:
        for pct in [1, 10]:
            k = math.ceil(len(a) * pct / 100)
            assert abs(values.nlargest(k).sum() / values.sum() - row[f'top_{pct}pct_{label}_share']) < 1e-12
    signed_loss = -a.tracked_net_usd
    print(month, 'alternative signed-loss top10 share',
          signed_loss.nlargest(math.ceil(len(a) * .1)).sum() / signed_loss.sum())
PY
```

Streamlit AppTest was run on the default page, a Feb–Apr period, all options of each demographic filter, all three filters together, a different Lorenz month, and an age-band comparison. Default and period-filtered KPIs were checked against mart sums. A synthetic zero-play group verified undefined concentration/ahead shares and rendering without exceptions. Full suite passed: **35 passed, 3 skipped** with only the action catalog available to raw-data tests (remaining raw datasets were not installed). New verification stays in this finding because the issue scope excludes test files.

Minimal UI reproduction (from repo root):

```bash
uv run python - <<'PY'
from pathlib import Path
from streamlit.testing.v1 import AppTest
at = AppTest.from_file(str(Path('pages/4_players.py').resolve()), default_timeout=30).run()
assert not at.exception
at.select_slider[0].set_value(('2025-02', '2025-04')).run()
assert not at.exception
for i in range(3):
    at.selectbox[i].select(at.selectbox[i].options[1]).run()
    assert not at.exception
at.selectbox[3].select('2025-04').run()
assert not at.exception
at.selectbox[4].select('age_band').run()
assert not at.exception
PY
```
