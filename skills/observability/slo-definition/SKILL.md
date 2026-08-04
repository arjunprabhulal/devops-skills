---
name: slo-definition
description: Covers turning "the service should be reliable" into a falsifiable number — SLIs that reflect real user experience, SLO targets meaningfully below 100%, the error budget those targets imply, and the policy that gates release velocity when it's spent. Use this whenever the user defines a service's reliability target, argues how reliable something "should" be, picks the metric an SLO is based on, or decides what happens when a budget runs out. For paging math on the budget use `alerting`, for day-to-day tracking use `error-budgets`.
license: MIT
---

# SLO Definition

"We should have five nines" is a number picked because it sounds impressive, not because anyone measured what users actually need or what the system can actually deliver without heroics. A Service Level Objective only has value if it's derived from real user tolerance and real system behavior — otherwise it's just a more precise-sounding version of the same unfalsifiable "be reliable" instruction, and nobody will actually gate a decision on it when it matters.

This is why SLO definition is its own discipline, distinct from the broader observability practice it depends on — see `observability` for the signals underneath, but the number itself is a negotiated business artifact, not just a query result.

The entire value of an SLO is that it turns a subjective argument into a shared, pre-agreed number that both the "ship faster" and "slow down and fix reliability" sides accept in advance.

**An SLO you wouldn't actually enforce with a release freeze isn't a real SLO — it's a vibe with a percentage sign on it.**

## 1. Pick SLIs that measure what the user actually experiences

A Service Level Indicator is the raw measurement the SLO is built on, and the single biggest mistake is picking one because it's easy to measure rather than because it reflects the user's experience. Server-side "did we return a 200" is easy to measure and can be true while the user's request actually failed client-side, timed out, or was slow enough that they gave up.

- **Prefer SLIs measured as close to the user as possible** — successful page loads under a latency threshold, successful checkout completions, messages actually delivered.
- **Instrument the client or an edge layer if that's what it takes**, rather than settling for what server logs already happen to capture.
- **A server-side 200 is a proxy, not the outcome itself** — treat it as a fallback, not a first choice.

**Done when:** each SLI can be traced to a specific, real user-facing outcome, not just an internal system state that correlates with one.

## 2. Set the target below 100%, and defend the number, not just pick it

100% reliability is not a target, it's a physical impossibility that also happens to be enormously expensive to approach — every additional nine costs disproportionately more than the last. The right target sits at the point past which users genuinely can't tell the difference and further investment stops paying off.

- **Derive it from historical performance data and user tolerance**, not from a round number chosen in a meeting.
- **A target above what the system has ever actually sustained** guarantees the budget starts already spent and the policy in step 4 never has real teeth.
- **A target well below what the system routinely achieves** wastes the constraint — nobody ever has to make a hard tradeoff against it.

**Done when:** the SLO target is justified by historical performance or explicit user-tolerance research, not chosen because it sounded appropriately ambitious.

## 3. Derive the error budget as the target's natural consequence

Once the target is set, the error budget isn't a separate decision — it's just "100% minus the target," expressed as an allowance: a 99.9% target over 28 days allows roughly 40 minutes of budget to spend.

That reframe matters because it turns the target from a purity goal into a resource: the budget can be spent on a risky deploy, an experiment, or planned maintenance, and spending all of it deliberately on things that matter is a legitimate outcome, not a failure. See `error-budgets` for the ongoing mechanics of tracking spend and deciding what to spend it on.

**Done when:** the numeric error budget for the current window is stated in concrete units (minutes, request count), not left as an abstract percentage.

## 4. Write the policy for what happens when the budget runs out — before it does

An SLO without a pre-agreed consequence for exhausting the budget is decorative. The policy needs to be specific and written down while everyone's calm:

- **A threshold that triggers a freeze** on non-critical-fix deploys, stated as a specific remaining-budget percentage.
- **A mandatory shift to reliability work** once triggered, not just a suggestion open to negotiation.
- **A named escalation path** for exceptions, agreed by both the team shipping features and the team accountable for reliability.

Writing this after the budget is already gone means it gets negotiated away in the moment it was supposed to prevent.

**Done when:** there's a written policy, agreed by both engineering and whoever owns the release decision, for what happens at specific budget-remaining thresholds.

## 5. Revisit the target on a cadence, not just when it's obviously wrong

An SLO that was correct a year ago can be wrong today — user expectations shift, and the system's architecture changes what's achievable.

- **A target nobody's failed in a year** might be set too low to be a real constraint on anything.
- **A target burned every month** might be set above what the system can currently sustain.
- **Review on a fixed cadence** — quarterly is reasonable — rather than leaving targets as a one-time decision from when the service launched.

**Done when:** every SLO has been reviewed against actual attainment data within the last review cycle, and any target that's never been at risk has been questioned.

## 6. Keep the SLO count small enough that people can actually name them

A service with fifteen SLOs has, in practice, zero SLOs that anyone can recite or gate a decision on — attention doesn't scale with the number defined.

- **Pick two or three** that best represent the user's experience of that service — usually one availability-shaped and one latency-shaped SLI.
- **Resist adding an SLO for every metric that seems worth tracking** — that instinct is real, but the right home for it is a dashboard, not a budget-policy conversation.
- **See `dashboards`** for where the rest of that detail should live instead.

**Done when:** anyone on the team can name the service's SLOs from memory, without looking them up.

## Report

State each SLO's SLI, target, and current attainment against the budget window, and whether the budget-exhaustion policy is written down and agreed by both engineering and release owners.

Name the honest gap — usually a target that was picked rather than derived from data, or a written policy that's never actually been enforced when the budget ran out — rather than presenting the SLOs as settled and battle-tested.
