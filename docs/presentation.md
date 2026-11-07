# The Gilded Ace: luck, location, or a leak?

Draft for [#28](https://github.com/shaswat-singh23/datathon-dashboard/issues/28).
This is a slide outline and speaker script, not a cleared submission deck.
The decider still needs to pin the presentation deadline and confirm the proposed
presenter assignments below.

**Evidence hold:** every source finding linked here currently has an `unchecked`
review status. [Findings policy](../findings/README.md) permits numerical slide
claims only after independent checking. [#60](https://github.com/shaswat-singh23/datathon-dashboard/issues/60)
tracks that work. Result slots below deliberately contain no analytical values.
Figure links are production instructions, not embedded slide images: the PNGs
already contain provisional numbers and must stay out of the deck until their
displayed claims are checked. Qualitative talking points describe the method;
they do not clear the pending results.

Use the same evidence period and drill as the selected figure. Copy approved
values from the finding, retain its units, baseline and limitation, and add a
visible source footer linking the finding and the relevant appendix section.
Do not fill a slot from memory or from an unchecked dashboard readout. If checking
changes a result, reconcile or recapture its figure before using it.

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
configured game math and location before choosing an intervention.” Reserve a
prominent line for the independently checked headline.

**Say:** “Management wants to replace the lowest-earning machines. We compare
that decision with expected contribution per available hour, then investigate
access and payout variation. Our dashboard lets you change the period and follow
the evidence behind a proposed action.”

**Result slot — HOLD:** Insert the cleared demand headline, including the
Back Forty comparison with the rest of the floor and its observational caveat.
Do not state that the closure caused the measured change.

**Visual after checking:** [headline.png](../figures/headline.png). Keep both
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

**Result slots — HOLD:** Add the checked overlap between the manager and adjusted
lists, then identify any changed candidates with the exact explanation in the
finding. Add the checked payout-screen target and threshold only after its own
finding clears. Describe it as an inspection lead, never proof of a leak or
wrongdoing. If discussing location, show the same-title result and its threshold
sensitivity separately from the simpler zone-peer heuristic.

**Visual after checking:** [q1.png](../figures/q1.png), at the full-period,
all-bank selection documented in [the figure inventory](../figures/README.md).
Its rank and luck columns also need checking; clearing the overlap alone does
not clear the whole screenshot. The later location and payout panels are outside
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

**Result slot — HOLD:** Copy all before/during/after rates for both series from
the checked demand finding. Retain the comparison floor even if the headline
mentions only Back Forty. If adding the same-title result, check the location
finding too. Sensor entries count crossings, not unique guests.

**Visual after checking:** Reuse [headline.png](../figures/headline.png).
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

**Result slots — HOLD:** Add checked lost hours and their scheduled-hours share,
then distinguish coin-in from theoretical house win. If using a manufacturer
comparison, retain the fleet baseline and the zone-mix limitation. Keep player
concentration against its equal-share baseline in backup material rather than
making a targeted-marketing recommendation.

**Visual after checking:** [q3.png](../figures/q3.png). It displays several
aggregates and monthly rows: check all displayed claims in the downtime finding.
[q4.png](../figures/q4.png) is the guest-outcome backup after its finding clears.

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

**Result slot — HOLD:** Copy each full-holdout MAE and units from the checked
evaluation finding. Name the lowest observed error only after checking; do not
describe it as guaranteed future superiority. Explain that MAE summarizes
observed errors and is not a prediction interval. Later-published tourism and
survey data cannot enter this forecast.

**Visual after checking:** [q7.png](../figures/q7.png), using its full May–June
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

**Result slots — HOLD:** Copy the checked funded action, target, quantity, cost,
displaced theo, total spend and unspent budget from the July action finding.
Distinguish funded work from priced alternatives: the challenge permits up to
three action types and does not require funding all of them. Report the
preserve-funds comparison and halved-recovery sensitivity alongside the plan.
Do not infer that low earnings establish replacement uplift.

**Measurement talking point after checking:** Use the finding's documented
paytable/meter comparison with configured RTP and same-configuration controls,
plus availability and payout-residual monitoring. A correction needs a separate
decision and benefit estimate. Maintenance and staffing would require controlled
pilots; regression to the mean is not an intervention effect.

**Visual after checking:** [q6.png](../figures/q6.png). Preserve the alternative
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
it is recorded in the [deployment finding](../findings/24-deploy.md).

**Kyle says:** “Change the period, drill into a bank or guest group, and open the
page's Source expander. The appendix links the result to its reproduction,
alternative explanation and limitation. Model validation has its own page.”

**Shaswat says:** “Use the evidence to decide what to investigate, what to measure
next and which spending to defer.” Add the checked headline and funded decision
here only when their source findings clear.

The public URL is currently pending. This outline does not claim a live-demo
rehearsal or a measured running time; the deployed click path and timed rehearsal
belong to [#25](https://github.com/shaswat-singh23/datathon-dashboard/issues/25).

## Backup: loyalty economics

**Presenter:** Sahith, for questions.

Use [q5.png](../figures/q5.png) only after [the comps finding](../findings/19-comps.md)
clears. Explain economic cost versus menu value, compare redemption intensity
with the earlier-period baseline, and keep carded theo as the denominator.
Comp costs are already inside POS cost of goods sold and are subtracted once.
The later redemption-intensity section is outside this screenshot. Source:
[appendix: loyalty](claims_evidence.md#q5-what-did-loyalty-rewards-cost).

## Release handoff for this draft

- Independent checking in #60 must clear each used finding and update its
  appendix status. A merged implementation PR alone does not clear a finding.
- Fill result slots from cleared findings, including baselines and limitations.
  Review every visible value in a selected figure; omit a figure if any displayed
  result remains unchecked. The [figure inventory](../figures/README.md) maps
  screenshots to evidence and documents their capture settings.
- Confirm presenter roles, add the deployed URL when available, then rehearse.
  Record actual timing rather than treating this outline as a timed demo.
- Until the evidence hold clears and figures are inserted, #28's checked-number
  and figure-use requirements remain pending. Keep the PR in draft.
