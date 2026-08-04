---
name: capacity-planning
description: Ensures a system has enough headroom before it needs it, by forecasting growth, modeling load against real saturation signals, and accounting for the lead time it takes to actually add capacity. Use this whenever the user asks whether current infrastructure can handle projected growth, is planning for a known traffic spike or seasonal peak, sees resource utilization trending upward, or asks "when will we run out of X." For reacting to load automatically in real time use `autoscaling`, and for right-sizing what's already provisioned use `rightsizing`.
license: MIT
---

# Capacity Planning

Autoscaling handles the minutes-to-hours timescale of load fluctuation. Capacity planning
handles the weeks-to-months timescale where the thing you're short on isn't compute headroom
but lead time — a database that needs a resize scheduled during a maintenance window, a quota
increase that takes two weeks to approve, a new region that takes a quarter to stand up.
Autoscaling can't add capacity that doesn't exist yet in the account, the budget, or the
vendor relationship.

The recurring failure is planning for the average and getting surprised by the peak. Average
load tells you what the system does most of the time; it tells you nothing about whether it
survives Black Friday, a viral moment, or the batch job that runs once a quarter.

**Plan for the peak, not the average — and start before you need it.**

## 1. Forecast from actual growth, not from hope

A capacity forecast built on "we think we'll grow 20% this year" is a guess with a number
attached. A useful forecast starts from real historical growth curves — user count, request
volume, data size — and projects forward with an explicit method, so the assumption is visible
and arguable rather than buried.

- **Use the metric that actually drives resource consumption**, not a proxy — active users
  doesn't tell you storage growth if usage patterns are changing.
- **Separate organic growth from step changes** — a new product launch or a big customer
  signing is a different forecast input than steady month-over-month trend.
- **Re-forecast on a cadence**, quarterly at minimum — a forecast that's a year stale is worse
  than no forecast, because it's trusted.

**Done when:** there's a written growth forecast, tied to a real historical metric, with a
stated re-forecast date.

## 2. Model load against saturation, not utilization

CPU at 60% sounds fine until you know the queue starts backing up at 65%. The number that
matters isn't current utilization, it's the point at which the system's behavior changes —
queueing, error rate rising, latency cliffing. Find that saturation point per resource, then
plan headroom relative to it, not relative to some arbitrary utilization target borrowed from
a different system.

| Resource | Saturation signal, not just utilization |
|---|---|
| Compute | Request queue depth / scheduling latency |
| Database | Connection pool exhaustion, lock wait time |
| Network | Retransmit rate, not just bandwidth used |
| Storage | IOPS ceiling, not just capacity used |

- **Find the knee of the curve empirically** — via `load-testing`, not by assuming a
  round-number threshold.
- **Different resources saturate differently** — a system can be CPU-fine and
  connection-pool-dead at the same load.

**Done when:** the planned headroom is expressed relative to a measured saturation point, not
an assumed utilization percentage.

## 3. Account for the lead time to add capacity, not just the amount

The forecast tells you how much you'll need; lead time tells you when you must start acquiring
it. A cloud VM might be minutes; a reserved-instance commitment, a database engine upgrade, a
new peering arrangement, or a vendor quota increase can be weeks. Plan the *trigger date* to
start provisioning, working backward from the need date by the lead time — not the need date
itself.

- **List lead time per capacity type explicitly** — quota increases, hardware, licenses, and
  new regions all differ wildly.
- **Trigger the request on a date, not a feeling** — "start the quota increase request 6 weeks
  before projected exhaustion," written down.
- **Build in slack for the request to be denied or delayed** — vendor lead times are
  estimates, not guarantees.

**Done when:** every capacity type in scope has a stated lead time and a calculated trigger
date derived from it.

## 4. Plan explicitly for known peaks, not just trend

Steady growth forecasting misses events — a product launch, a marketing campaign, a seasonal
peak, a scheduled batch job that dwarfs normal traffic. These need their own capacity plan,
sized to the peak's expected multiple of baseline, tested ahead of time rather than discovered
live.

- **Size for the peak multiple, not baseline plus a margin** — a 10x Black Friday spike needs
  10x planning, not "add 20% headroom."
- **Load-test at the target peak before it arrives** — see `load-testing` — a plan that's
  never been load-tested is a guess.
- **Have a degrade-gracefully plan for beyond-forecast load** — feature flags to shed
  non-critical work, queueing instead of failing — see `feature-flags`.

**Done when:** every known upcoming peak event has a capacity plan sized to its expected
multiple and validated by a load test.

## 5. Tie capacity to cost, explicitly

Headroom costs money sitting idle most of the time. Capacity planning that ignores cost
produces over-provisioned systems that are safe but wasteful; capacity planning that ignores
safety produces cheap systems that fall over at the peak. Make the tradeoff a stated decision,
not a default.

- **State the cost of the headroom** you're carrying, in the same conversation as the risk it
  protects against.
- **Use reserved or committed capacity for predictable baseline**, on-demand or autoscaled for
  the variable peak — see `cost-optimization` for the broader tradeoff.
- **Revisit over-provisioned capacity on the same cadence as the forecast** — capacity
  headroom rots the same way stale forecasts do.

**Done when:** the capacity plan states its cost and that cost has been explicitly accepted,
not just incurred by default.

## Report

State the forecast horizon and method used, the saturation-based headroom target for each key
resource, and the trigger dates for any capacity that needs lead time. Name explicitly which
resources still lack a tested saturation point or a known lead time — an untested assumption
about when a system falls over is the gap most likely to turn into a real incident, and it's
cheaper to admit it now than to discover it at the peak.
