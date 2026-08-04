---
name: rightsizing
description: Matches compute, memory, and storage allocation to real measured usage instead of the guess made at launch time, sizing from percentiles rather than averages, and preferring autoscaling over a fixed size wherever demand varies. Use this whenever the user asks whether an instance or fleet is oversized, wants to cut provisioned capacity, is picking an instance type, or is choosing between fixed capacity and autoscaling. For turning savings into a prioritized plan use `cost-optimization`, and for the commitment discounts that should follow a sized fleet use `cloud-budgeting`.
license: MIT
---

# Rightsizing

Most instance sizes are set once, at launch, from a guess made before real traffic existed — and
then never revisited, because a running system that isn't on fire doesn't generate a reason to go
back and check. The gap between provisioned and used capacity grows quietly for as long as nobody
looks, and by the time someone does look it's often large enough to embarrass whoever picked the
original size.

Rightsizing is not a one-time correction. Usage changes with every feature release, traffic
pattern shift, and dependency change, so a size that was correct six months ago is a guess again
today. The discipline is the measurement loop, not the resize itself.

**Size from what the system actually uses, not from what someone guessed it might need.**

## 1. Size from measured usage, never from instinct

"This feels like it needs 4 vCPUs" is not data. Pull actual CPU, memory, disk, and network
utilization over a representative window before changing anything — a resize based on a hunch is
just as likely to be wrong in the expensive direction as the cheap one.

- **Use a window that includes peak traffic**, not just a quiet afternoon that understates real
  need.
- **Check all resource dimensions**, not just CPU — a service throttled on memory or IOPS won't
  show up in a CPU-only view.

**Done when:** every resize decision cites a metrics window, not a guess.

## 2. Look at the right percentile, not the average

Average utilization hides the peaks that actually determine whether a resource is adequately
sized — a workload that averages 20% CPU but spikes to 95% during checkout on Fridays will fall
over if sized to the average. Size to a high percentile (p95 or p99) of the metric that matters for
the workload's actual failure mode, with headroom for the spike, not to what it looks like on a
typical Tuesday.

**Done when:** the sizing decision states which percentile was used and why it fits the workload's
traffic shape.

## 3. Prefer autoscaling to a fixed guess wherever demand varies

A fixed size is a bet that usage stays flat — true for very few real workloads. Where demand
varies meaningfully by time of day, day of week, or event, autoscaling adapts capacity to the
actual curve instead of provisioning for the peak all day and wasting the difference the rest of
the time. See `autoscaling` for the mechanics of scaling policies and cooldowns.

- **Fixed capacity fits workloads with genuinely flat, predictable demand** — a fixed-size batch
  cluster with a known job size, for instance.
- **Autoscaling fits everything else** — anything with a daily cycle, a weekly cycle, or bursty
  traffic.

**Done when:** every workload with variable demand runs on autoscaling instead of a fixed size
picked to cover its peak.

## 4. Treat downsizing as a queue, not a one-time sweep

A single rightsizing sweep finds the backlog that accumulated before anyone looked, but usage
keeps drifting the moment the sweep ends. Turning rightsizing into a standing queue — new
candidates surfaced as usage patterns change, reviewed and actioned on a cadence — keeps the gap
from re-accumulating into the next big embarrassing sweep.

**Done when:** rightsizing candidates are reviewed on a recurring cadence, not discovered fresh
each time someone asks why the bill is high.

## 5. Treat CPU and memory as separate sizing problems

A resource can be oversized on CPU and undersized on memory at the same time, and picking a size
that only looks at one dimension will get the other wrong. Size each resource dimension against
its own utilization data, then pick the smallest instance type or request/limit pair that covers
all of them with headroom — not the smallest that covers whichever dimension was checked first.

**Done when:** every sizing decision states the CPU, memory, and (where relevant) storage or IOPS
utilization it was based on, not just one dimension.

## 6. Re-measure after every change

A resize changes the workload's behavior — a smaller instance under real load may show different
utilization than the old one did, because contention, garbage collection, or I/O wait patterns
shift with the resource ceiling. Re-measuring after the change, not just before it, catches a
resize that was too aggressive before it turns into an incident.

**Done when:** every resize is followed by a post-change metrics check confirming the new size
holds up under real traffic.

## Report

State which resources were resized, the percentile and window the sizing was based on, and how
much provisioned capacity was removed. Name the honest gap — usually a workload whose traffic
pattern is too irregular to trust a percentile-based estimate yet, or one still pending
autoscaling migration — rather than claiming the whole fleet is now optimally sized.
