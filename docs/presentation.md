# The Gilded Ace: luck, location, or a leak?

Draft for [#28](https://github.com/shaswat-singh23/datathon-dashboard/issues/28).
This is a slide outline and speaker script, not a cleared submission deck.
The decider still needs to pin the presentation deadline and confirm the proposed
presenter assignments below.

**Evidence status, claim by claim.** [Findings policy](../findings/README.md)
permits numerical slide claims only from a finding whose `Checked by` is not
`unchecked`. The values below are copied from findings that name a check:
22 (machines), 32 (payout screen), 31 (location), 16 claims 1 and 3 (closure,
June softening), 17 (downtime), 18 (players), 19 (comps), 23 (July plan) and
47 (forecast evaluation). Those checks are tool-assisted re-runs recorded under
a teammate's name (Claude Code), not separate human audits; the
[appendix](claims_evidence.md) gives each check's scope. Still `unchecked` and
kept off slides: the event lifts in finding 16 (claim 2, #74), the deployment
record (24) and the public-URL judge-path timings (70).

The submitted video follows the shorter story in the
[110-second demo script](demo_script.md); this deck is the longer live version.
Copy values only from the finding, retain its units, baseline and limitation,
and add a visible source footer linking the finding and the relevant appendix
section. Do not fill a slot from memory or from a dashboard readout. If a
finding changes, reconcile the slide and recapture its figure. Always state that
the casino is fictional and the data synthetic.

## Presenter plan and ownership

Assignments follow merged implementation PRs, with framing and the final decision
assigned to the decider. They are proposed rehearsal roles, not confirmed bookings.
Everyone has a speaking section; Sahith supports technical questions across the
machine, action and model work.

| Presenter | Speaking section | Ownership used for the assignment |
|---|---|---|
| Shaswat | Opening; decision and close | Decider in [AGENTS.md](../AGENTS.md); team story workflow in [PR #6](https://github.com/shaswat-singh23/datathon-dashboard/pull/6). Sahith supplies action analysis from [PR #52](https://github.com/shaswat-singh23/datathon-dashboard/pull/52). |
| Sahith (`sahith1021`) | Machine triage | Machine rankings [PR #48](https://github.com/shaswat-singh23/datathon-dashboard/pull/48), location [PR #53](https://github.com/shaswat-singh23/datathon-dashboard/pull/53), payout screen [PR #54](https://github.com/shaswat-singh23/datathon-dashboard/pull/54); figures [PR #57](https://github.com/shaswat-singh23/datathon-dashboard/pull/57). |
| Kyle (`kyledong25`) | Access and demand; evidence trace | Demand [PR #38](https://github.com/shaswat-singh23/datathon-dashboard/pull/38), Claims & Evidence appendix [PR #62](https://github.com/shaswat-singh23/datathon-dashboard/pull/62). |
| Alex (`dandelino-del`) | Operations and guest outcomes; model validation | Downtime [PR #41](https://github.com/shaswat-singh23/datathon-dashboard/pull/41), player outcomes [PR #43](https://github.com/shaswat-singh23/datathon-dashboard/pull/43), original forecast [PR #45](https://github.com/shaswat-singh23/datathon-dashboard/pull/45). Sahith supports evaluation controls from [PR #55](https://github.com/shaswat-singh23/datathon-dashboard/pull/55). |

## Slide: The replacement decision

**Presenter:** Shaswat.

**On slide:** Title above; “Compare low earnings with exposure, availability,
configured game math and location before choosing an intervention.” Footnote:
“Fictional casino, synthetic data, January–June 2025.”

**Say:** “Management wants to replace the lowest-earning machines. We compare
that decision with expected contribution per available hour, then investigate
access and payout variation. Our dashboard lets you change the period and follow
the evidence behind a proposed action.”

**Result (finding 16, claim 1; checked):** During the five-week walkway closure,
Back Forty coin-in per available machine-hour fell from **$135.5 to $96.3**
while the rest of the floor went from **$206.1 to $210.7**. Observational: do not
state that the closure caused the measured change.

**Visual:** [headline.png](../figures/headline.png). Keep both
series, the before/during/after windows, units and zero-origin axis visible.
Use the same headline again on the demand slide so the opening and evidence agree.

**Source footer:** [Demand finding, evidence 1](../findings/16-demand-changes.md)
and [appendix: demand](claims_evidence.md#q2-what-changed-in-demand-and-is-it-location).

**Handoff:** “Sahith will show how we test the manager's list.”

## Slide: Compare the manager's picks with adjusted economics

**Presenter:** Sahith.

**On slide:** “Raw house win → expected contribution per available hour →
investigation.” Keep separate labels for earnings rank, location association and
payout inspection; these screens answer different questions.

**Say:** “Our baseline is the manager's lowest total house win over active,
on-floor days. We compare it with theoretical win less supplied costs per
available hour. We follow dated placements and exclude off-floor records. A
low adjusted rank does not estimate the benefit of replacing that machine.”

**Results (findings 22 and 32; checked):** **8 of 10** manager picks remain in the
adjusted bottom ten. The two that leave are M-1158 (adjusted rank 74) and
M-1118 (rank 111). M-1158 is the **only one of 310** machines whose configured
RTP lies outside its observed-payout interval at **±3.8 standard errors**
(observed **96.96%** versus configured **90.00%**), against **24/310** flagged by a
naive 1.96 screen. Describe it as an inspection lead, never proof of a leak or
wrongdoing. If discussing location, show the same-title result (finding 31:
**7/10** at a 90% tolerance, **5** at 95%, **3** at 100%) separately from the
simpler zone-peer heuristic, which flags none.

**Visual:** [q1.png](../figures/q1.png), at the full-period, all-bank selection
documented in [the figure inventory](../figures/README.md). Its overlap, rank
and luck columns match finding 22's table. The later location and payout panels are outside
this capture; use their findings for speaker detail rather than implying they
appear in this image.

**Source footer:** [Machine rankings](../findings/22-machines.md),
[payout screen](../findings/32-leak-screen.md),
[same-title location comparison](../findings/31-location.md), and
[appendix: machines](claims_evidence.md#q1-which-of-the-managers-bottom-ten-are-truly-underperforming).

**Handoff:** “Kyle will compare the access window with the rest of the floor.”

## Slide: Test an access explanation against a comparison floor

**Presenter:** Kyle.

**On slide:** “Back Forty and the rest of the floor, before / during / after
the walkway closure.” Label the quantity as coin-in per available machine-hour,
not revenue or profit.

**Say:** “We compare the same windows in Back Forty and elsewhere using total
coin-in divided by total available hours. Traffic and occupancy help distinguish
reaching the zone from play once seated. Same-title comparisons probe game mix.
Renovation, seasonality and nonrandom placement still limit a causal conclusion.”

**Result (finding 16, claim 1; checked):** Coin-in per available machine-hour,
before / during / after: Back Forty **$135.5 / $96.3 / $125.9**; rest of floor
**$206.1 / $210.7 / $197.4**. Zone entries per day 603 / 421 / 552; coin-in per
occupied hour about flat ($479 / $464 / $487). Same-title comparison (finding
31; checked): nine picks sit in Back Forty and **7/10** keep pace with local
same-title peers whose demand is roughly 35% to 40% below the same titles elsewhere.
Sensor entries count crossings, not unique guests. Finding 31 groups by UTC
closure boundaries and reports Back Forty $134.55 / $96.25 / $124.14; do not mix
its values with finding 16's windows on one slide.

**Visual:** Reuse [headline.png](../figures/headline.png).
[q2.png](../figures/q2.png) is a full-floor overview, not the Back Forty window
comparison; keep it as a backup rather than using it to illustrate that claim.

**Source footer:** [Demand finding](../findings/16-demand-changes.md),
[same-title comparison](../findings/31-location.md), and
[appendix: demand](claims_evidence.md#q2-what-changed-in-demand-and-is-it-location).

**Handoff:** “Alex will explain the operating and guest-outcome limits.”

## Slide: Value availability and describe guest outcomes honestly

**Presenter:** Alex.

**On slide:** “Lost play is an opportunity estimate; carded play is a partial
view of guests.”

**Say:** “We value unavailable hours at each machine's own available-hour play
rate in the same month. Guests may switch machines, so estimated lost play is
not a guaranteed recovery. Carded outcomes exclude untracked guests; wagers
include replayed winnings. We do not recommend encouraging heavy losers to play
more.”

**Results (findings 17 and 18; checked):** On-floor machines lost **5,021**
machine-hours, **0.38%** of scheduled hours, worth about **$974k** coin-in and
**$91k** theo. Ridgeline faults **1.68** versus **0.57** per 1,000 scheduled hours
for the rest of the fleet, with similar repair response; zone mix is not
controlled. Keep player concentration (top 10% of active carded players hold
about 40% of tracked wagers, against an equal-share 10%) in backup material
rather than making a targeted-marketing recommendation.

**Visual:** [q3.png](../figures/q3.png); its displayed aggregates and monthly rows
match finding 17. [q4.png](../figures/q4.png) is the guest-outcome backup.

**Source footer:** [Downtime](../findings/17-downtime.md),
[player outcomes](../findings/18-player-outcomes.md), and
[appendix: downtime](claims_evidence.md#q3-how-much-play-was-lost-to-downtime-and-where).

## Slide: Validate a forecast against simple baselines

**Presenter:** Alex, with Sahith supporting evaluation questions.

**On slide:** “Train January–April; freeze predictions; evaluate May–June.”
Reserve a result table for constant mean, weekday mean and fitted weekday-plus-trend
regression, all scored with daily dollar MAE on the same holdout.

**Say:** “The target is daily floor coin-in. Our required baseline is the
training-period constant daily mean. We also compare weekday means with a fitted
weekday-plus-trend regression. Inputs use calendar dates known at prediction
time. Filtering the evaluation period recalculates scores without refitting.”

**Result (finding 47; checked):** Full May–June holdout MAE per day: constant
training mean **$218,258**, weekday mean **$68,699**, fitted weekday + trend
**$96,658**. The weekday baseline has the lowest observed error; do not describe
it as guaranteed future superiority. Explain that MAE summarizes
observed errors and is not a prediction interval. Later-published tourism and
survey data cannot enter this forecast.

**Visual:** [q7.png](../figures/q7.png), using its full May–June
holdout and Month drill. Preserve the training/test boundary and baseline scores.

**Source footer:** [Forecast evaluation](../findings/47-forecast-evaluation.md),
[original forecast](../findings/20-coin-in-forecast.md), and
[appendix: validation](claims_evidence.md#q7-model-and-validation).

**Handoff:** “Shaswat will connect the checked evidence to a spending decision.”

## Slide: Price the decision and specify what it will teach us

**Presenter:** Shaswat, with Sahith supporting pricing and action evidence.

**On slide:** Reserve an action table with columns “choice,” “cost,” “effect and
uncertainty,” and “measurement.” Include preserving funds as the decision baseline.

**Say:** “We compare the proposed inspection with preserving funds, maintenance
and extra technician coverage. Pricing includes quantity, lead time and recurring
days through the shared budget validator. An inspection buys information; its
value is not a demonstrated revenue recovery. Recovery scenarios are assumptions,
not confidence intervals for an intervention effect.”

**Results (finding 23; checked):** Fund one `A-INSPECT` of M-1158, quantity 1,
cost **$1,200**, displaced theo about **$24**; total spend **$1,200**, budget
retained **$98,800**. Budget retained is not savings. Deferred alternatives:
Ridgeline preventive sweep **$9,000** and extra grave-shift technician **$11,520**;
neither covers its price under the historical recovery scenarios, which are
hypothetical, not confidence intervals. Distinguish funded work from priced alternatives: the challenge permits up to
three action types and does not require funding all of them. Report the
preserve-funds comparison and halved-recovery sensitivity alongside the plan.
Do not infer that low earnings establish replacement uplift.

**Measurement talking point:** Use the finding's documented
paytable/meter comparison with configured RTP and same-configuration controls,
plus availability and payout-residual monitoring. A correction needs a separate
decision and benefit estimate. Maintenance and staffing would require controlled
pilots; regression to the mean is not an intervention effect.

**Visual:** [q6.png](../figures/q6.png). Preserve the alternative
prices, assumptions, and budget remainder. The measurement plans are in the
finding and later page sections, outside this capture.

**Source footer:** [July action plan](../findings/23-july-actions.md), supported by
[payout screening](../findings/32-leak-screen.md) and
[downtime](../findings/17-downtime.md), plus
[appendix: actions](claims_evidence.md#q6-what-should-management-fund-in-july).

## Slide: Trace the recommendation and close

**Presenter:** Kyle demonstrates the evidence route; Shaswat delivers the close.

**On slide:** “Selection → source finding → reproduction → alternative explanation
→ limitation → measurement.” Link the [repository](https://github.com/shaswat-singh23/datathon-dashboard),
[Claims & Evidence appendix](claims_evidence.md), and
[AI-use disclosure](ai_disclosure.md). Add the public dashboard link only after
it is recorded in the [deployment finding](../findings/24-deploy.md) (URL recorded;
that finding is still `unchecked`).

**Kyle says:** “Change the period, drill into a bank or guest group, and open the
page's Source expander. The appendix links the result to its reproduction,
alternative explanation and limitation. Model validation has its own page.”

**Shaswat says:** “Inspect M-1158's configuration for twelve hundred dollars,
record the result, then measure outcomes before replacing anything. We retain
ninety-eight thousand eight hundred dollars; that is unspent budget, not savings.”

Public URL: https://datathon-dashboard-o5xb3rbuuqzppphcqeglmq.streamlit.app/
(finding 24, `unchecked`). This outline does not claim a measured running time;
the timed video script is [demo_script.md](demo_script.md).

## Backup: loyalty economics

**Presenter:** Sahith, for questions.

Use [q5.png](../figures/q5.png) with [the comps finding](../findings/19-comps.md)
(checked): economic cost $190,669 against $682,750 menu value. Explain economic cost versus menu value, compare redemption intensity
with the earlier-period baseline, and keep carded theo as the denominator.
Comp costs are already inside POS cost of goods sold and are subtracted once.
The later redemption-intensity section is outside this screenshot. Source:
[appendix: loyalty](claims_evidence.md#q5-what-did-loyalty-rewards-cost).

## Release handoff

- Each value above is copied from a finding with a named check. Before
  presenting, re-read each finding's `Checked by` line; if it changed, update
  the slide and its appendix row.
- Do not add the event lifts (finding 16, claim 2), deployment timings (24) or
  judge-path timings (70) until those findings are checked.
- The [figure inventory](../figures/README.md) still carries a blanket
  provisional note from before the checks landed; it is outside this ticket's
  scope. Its values match the checked findings listed above.
- Confirm presenter roles, then rehearse aloud and record actual timing.
