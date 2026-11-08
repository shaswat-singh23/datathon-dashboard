# Dashboard walkthrough: investigate before replacing

Issues: #25 (original walkthrough), #107 (110-second story). Target length: **about 110 seconds**, including navigation; the submitted video must stay at or below 120 seconds. Story order follows Task 5 of the [competition presentation plan](superpowers/plans/2026-11-07-competition-presentation.md).

## Before the clock starts

- Public URL: https://datathon-dashboard-o5xb3rbuuqzppphcqeglmq.streamlit.app/ ([deployment finding](../findings/24-deploy.md); that finding is still `Checked by: unchecked`, so rehearse on the live link before recording).
- **Evidence status, claim by claim.** Every number spoken below comes from a finding whose `Checked by` line names a reviewer; the table at the end lists each one. Those checks are tool-assisted re-runs recorded under a teammate's name (Claude Code), not separate human audits; the [appendix](claims_evidence.md) gives the scope of each. Do **not** add the event-lift numbers (finding 16, claim 2: still pending #74), deployment timings (finding 24) or the judge-path rehearsal timings (finding 70): those remain `unchecked`.
- Never describe an inspection lead as wrongdoing, the closure comparison as causal, or retained budget as savings. Always say the casino is fictional and the data synthetic.
- Use a desktop window at 1440 × 1000 with the sidebar open. Visit Home, Machines, Demand, Actions and Model once to warm the app, reset every filter to its full range and **All**, and return to Home at the top.
- The page app is being restructured (plan Tasks 1–4: Home decision cards, grouped navigation). The click column names pages and the headings that exist today; after those changes land, re-confirm each label and keep the narration unchanged.

## Exact click path and spoken script

Times are cumulative cues. The quoted sentences are the complete narration, written as spoken (numbers spelled out) so the word count is honest. Bracketed or plain instructions are silent.

| Time | Page and click | Say | Words |
|---|---|---|---:|
| 0:00–0:15 | **Home**. Point to the decision and the ten-machine question. | “The Gilded Ace is a fictional casino, and this is synthetic data. Management wants to replace its ten lowest-earning machines. But raw earnings blur a weak machine with downtime, payout luck and location.” | 33 |
| 0:15–0:40 | **Machines**, All banks, full period. Point to the manager list beside the adjusted ranking, then scroll to **Leak: inspect, not proof**. | “On Machines, we rank by expected contribution per available hour. Eight of the manager's ten stay in the adjusted bottom ten. M eleven fifty-eight is the only machine of three hundred ten whose payout misses its configured return by more than three point eight standard errors: about ninety-seven percent paid against ninety. That is an inspection lead, not wrongdoing.” | 59 |
| 0:40–1:05 | **Demand** → zone drill **Back Forty**, full period. Scroll to **Back Forty vs rest of floor** with the shaded closure window. | “On Demand, the walkway into Back Forty closed for five weeks. Back Forty wagers per available machine-hour fell from about one hundred thirty-five dollars to ninety-six; the rest of the floor did not drop. Nine of the ten picks sit in Back Forty and seven keep pace with the same game beside them. That is an observational location explanation, not proof.” | 61 |
| 1:05–1:30 | **Actions**. Point to plan cost and budget retained, then the alternatives comparison and the measurement plan. | “So for July we fund one twelve-hundred-dollar configuration inspection and retain ninety-eight thousand eight hundred dollars. Retained budget is not savings. Maintenance at nine thousand and overnight technician coverage at eleven thousand five hundred twenty don't pay back under our recovery scenarios; we defer both. We verify the configuration by July second, then compare payouts with same-configuration machines through July thirtieth.” | 61 |
| 1:30–1:50 | **Model**. Point to the three-model error table, then the Source expander. Close on the sidebar links to Players, Comps and Downtime. | “On a May–June holdout, daily error is two hundred eighteen thousand dollars for a constant mean, sixty-nine thousand for weekday means, and ninety-seven thousand for our fitted trend. The simple baseline wins. Players, Comps, Downtime and every source stay one click away. Inspect, record the result, then measure before replacing anything.” | 51 |

**Timing estimate.** 265 spoken words. At 150 words per minute that is **106 seconds** of speech (segments 13, 24, 24, 24 and 20 seconds); at the 145 words per minute used in the earlier rehearsal it is 110 seconds. Each segment fits its cue window, and the narration ends at about 1:45–1:50, inside the 110-second target and well under the 120-second limit. This is an estimate, not a timed human take: clicks alone took 77 seconds on the old seven-step route, so speak over page loads rather than waiting for each one. If a timed take runs over, cut “Nine of the ten picks sit in Back Forty, and” first (then say “Seven picks keep pace with the same game beside them”).

The funded plan has **one** action type. Maintenance and technician coverage are priced alternatives, not commitments, and preserving the full budget is the zero-spend baseline. The closing sentence is the testable recommendation: inspect configuration, record the result, then measure outcomes. Do not close with savings, revenue uplift or a commercial ask.

## Spoken numbers and their sources

| Spoken | Exact value and meaning | Finding | Checked by (from the finding) |
|---|---|---|---|
| ten lowest-earning machines | Bottom 10 by total house win over active on-floor days, Jan 1–Jun 30 2025 | [22-machines](../findings/22-machines.md) | Alex (Claude Code, Opus 5.5), 2026-11-07 16:15 |
| Eight of the manager's ten | 8/10 overlap with the bottom 10 by expected contribution per available hour | [22-machines](../findings/22-machines.md) | Alex (Claude Code, Opus 5.5), 2026-11-07 16:15 |
| one machine of three hundred ten; three point eight standard errors | 1/310 machines outside the ±3.8 SE payout interval (M-1158) | [32-leak-screen](../findings/32-leak-screen.md) | Alex (Claude Code, Opus 5.5), 2026-11-07 16:15 |
| about ninety-seven percent paid against ninety | M-1158 observed RTP 96.96% vs configured 90.00% | [32-leak-screen](../findings/32-leak-screen.md) | Alex (Claude Code, Opus 5.5), 2026-11-07 16:15 |
| five weeks; one hundred thirty-five to ninety-six; rest of floor did not drop | W-ENT-B40 closed Mar 3–Apr 6 gaming dates (35 days); Back Forty coin-in per available machine-hour $135.5 before vs $96.3 during; rest of floor $206.1 vs $210.7 | [16-demand-changes](../findings/16-demand-changes.md), claim 1 | Alex (Claude Code, Opus 5.5), 2026-11-07 16:25 (claims 1 and 3 only) |
| Nine of the ten picks sit in Back Forty; seven | 9 picks in Back Forty; 7/10 meet the same-title location screen at the 90% tolerance (5 at 95%, 3 at 100%) | [31-location](../findings/31-location.md) | Kyle (Claude Code, Fable 5.1), 2026-11-07 17:05 |
| twelve-hundred-dollar inspection; ninety-eight thousand eight hundred | One A-INSPECT of M-1158 at $1,200; $98,800 of $100,000 retained | [23-july-actions](../findings/23-july-actions.md) | Kyle (Claude Code, Fable 5.1), 2026-11-07 16:25 |
| nine thousand; eleven thousand five hundred twenty | Ridgeline preventive sweep $9,000; extra grave-shift technician $11,520; both deferred | [23-july-actions](../findings/23-july-actions.md) | Kyle (Claude Code, Fable 5.1), 2026-11-07 16:25 |
| July second; July thirtieth | Verify configuration July 2; monitor July 2–30 against same-configuration controls | [23-july-actions](../findings/23-july-actions.md) | Kyle (Claude Code, Fable 5.1), 2026-11-07 16:25 |
| two hundred eighteen thousand; sixty-nine thousand; ninety-seven thousand | May–June holdout MAE per day: constant $218,258.10, weekday $68,698.55, fitted weekday + trend $96,657.83 | [47-forecast-evaluation](../findings/47-forecast-evaluation.md) | Kyle (Claude Code, Fable 5.1), 2026-11-07 16:25 |

## Previous rehearsals (superseded route)

The 1:55 seven-step route from #25 was rehearsed by automated clicks with narration allowances: locally by Sahith (115.07 s) and on the public URL by Kyle (111.93 s, [finding 70](../findings/70-judge-qa.md), still `unchecked`). Neither was a human spoken take, and neither timed this script. Time this script with a human speaker after the app changes land, and record the result here.
