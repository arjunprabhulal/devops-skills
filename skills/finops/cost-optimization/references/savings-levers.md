# Savings Levers, Ranked

This is the reference to open when you know you need to cut spend but not where to start. It
ranks the common levers biggest-and-easiest first, so the order itself is the prioritization —
work from the top down and stop when the remaining levers cost more effort than they return.

## Contents

- 1. Kill idle and orphaned resources
- 2. Turn off non-production outside business hours
- 3. Rightsize over-provisioned compute and storage
- 4. Buy commitment discounts against a measured floor
- 5. Move fault-tolerant workloads to spot/preemptible capacity
- 6. Tier and lifecycle storage
- 7. Cut egress and data-transfer costs
- 8. Review managed-service tiers
- Measuring what you actually saved

## 1. Kill idle and orphaned resources

Unattached disks left behind after an instance was terminated, load balancers with no healthy
targets, old snapshots and AMIs nobody restores from, unreleased elastic IPs, zombie dev/test
environments spun up for a project that shipped months ago. Each one delivers zero value at full
price.

Small per resource, but the count compounds fast in any account more than a year old — orphaned
storage and idle compute together commonly run 5-15% of total spend in accounts that have never
been swept. Effort/risk is the lowest of any lever: no performance trade-off to weigh, since
you're removing something already contributing nothing. The only risk is deleting something
someone forgot to tag as "actually needed," which a short grace period solves.

**Find candidates:** query the billing export or cost-explorer for resources with zero
attachment, zero traffic, or zero connections over a 30-day window. Cross-reference against
tagging so you know who to ask before deleting — see `resource-tagging`.

## 2. Turn off non-production outside business hours

Dev, staging, QA, and demo environments that run 24/7 but are only ever used during a working
day. Scale-to-zero or scheduled stop/start for anything that doesn't need to be up when nobody's
using it.

Roughly 65-75% of the non-prod compute bill for environments cut down to a standard workday and
workweek — 12 hours a day, 5 days a week is about a quarter of the hours in a week. Effort/risk is
low: automation to stop and start on a schedule is a one-time build, and the blast radius is
bounded to non-production traffic. Worst case, someone needs an environment at 2am and waits for
it to spin back up.

**Find candidates:** filter the non-prod tag or account for anything without a scheduled stop
already attached. Anything still running unscheduled after this pass should have a written reason.

## 3. Rightsize over-provisioned compute and storage

Instances, databases, and volumes sized for a peak that never comes, provisioned by guess instead
of measurement, or never revisited after the workload that justified the size moved on.

20-40% of the compute bill in fleets that have never been rightsized against real utilization
data — oversizing compounds because nobody downsizes proactively, only after a cost review forces
the question. Effort/risk is moderate: requires real utilization data (CPU, memory, IOPS,
connections) over a representative window, not a single low-traffic day, plus a change window to
resize or migrate. Undersizing is the real risk — verify against peak plus headroom, not average.
See `rightsizing` for how to size from measured usage instead of guessing.

**Find candidates:** pull utilization percentiles per resource over 2-4 weeks; anything sitting
well below its provisioned capacity at p95 is a candidate. Prioritize by resource size, not gap
size — a large instance at 30% beats a small one at 5%.

## 4. Buy commitment discounts against a measured floor

Reserved instances, savings plans, or committed-use discounts that trade a committed dollar
amount or usage level for a lower rate than on-demand.

30-60% off on-demand rates for the covered usage, depending on term length and payment structure
— the discount is large, which is exactly why buying it against the wrong baseline is expensive.
The risk isn't in buying the discount, it's in what you commit against: committing against your
peak, or against a fleet you haven't rightsized yet, locks in savings on top of waste for the
length of the term — a 1-3 year mistake instead of a reversible one.

**Find candidates:** look at usage over the last 3-6 months and find the level that never dropped
below — that's your baseline. Commit against the sustained floor only, after rightsizing, and
stagger terms so the whole fleet isn't re-bet at once.

## 5. Move fault-tolerant workloads to spot/preemptible capacity

Spare capacity priced well below on-demand for workloads that can tolerate interruption — batch
jobs, CI runners, stateless web tiers behind autoscaling, rendering and training jobs with
checkpointing.

60-90% off on-demand rates for the capacity that runs on spot. Effort/risk is moderate to high
depending on the workload: a stateful service without graceful interruption handling will drop
requests or lose data when capacity is reclaimed. Only move workloads that already tolerate a node
disappearing without warning, and prove it in a lower environment first.

**Find candidates:** anything already running behind an autoscaler with health checks and
graceful shutdown, anything stateless, anything batch or queue-driven with retry built in.

## 6. Tier and lifecycle storage

Moving data to cheaper storage classes as it ages out of frequent access, and deleting it
outright once past any retention requirement — hot storage for active data, cold/archive tiers
for logs, backups, and old snapshots nobody has pulled in months.

Tiering commonly cuts the affected storage line 40-70%, since archive tiers are priced a fraction
of hot storage — the catch is retrieval cost and latency, so this only pays off for data that's
genuinely infrequently accessed. Effort/risk is low once a lifecycle policy is written; the main
risk is tiering something accessed more often than assumed, which shows up as retrieval fees
eating the savings.

**Find candidates:** access logs or last-accessed metadata per object/volume — anything untouched
for 30-90 days is a lifecycle candidate; anything untouched for a year past its retention
requirement is a deletion candidate, not just a tiering one.

## 7. Cut egress and data-transfer costs

Cross-region and cross-AZ traffic, transfer to the public internet, and unnecessary hops through
NAT gateways or load balancers that each add their own per-GB charge.

Varies widely by architecture, but data-heavy services routinely find 10-30% of their bill hiding
in transfer costs nobody was watching, because compute and storage get all the attention on a cost
dashboard. Effort/risk is moderate — often requires an architecture change (co-locating services
in the same AZ, adding a cache or CDN, compressing payloads) rather than a config flag.

**Find candidates:** break the bill down by transfer type (inter-region, inter-AZ, internet
egress) instead of looking at the total — the total hides which specific path is expensive.
Services with heavy cross-AZ chatter or large payloads served straight from origin are the usual
suspects.

## 8. Review managed-service tiers

Databases, caches, search clusters, and other managed services provisioned on a tier bought for
an old requirement — a support tier, a redundancy level, or a feature tier nobody uses anymore.

Savings vary, but this lever tends to be underrated because these are "set and forget" purchases
— a support or feature tier bought two reorgs ago rarely gets revisited on its own. Effort/risk is
low to moderate: usually a config or contract change, not a migration, but changing redundancy or
support tiers can affect reliability guarantees, so confirm what you're giving up before
downgrading.

**Find candidates:** list every managed service's current tier next to what it's actually using —
multi-AZ redundancy nobody tests failover on, a support tier above what the team actually files, a
feature tier for capabilities never turned on.

## Measuring what you actually saved

A recommendation isn't a saving until it's realized — track savings identified versus savings that
show up in the next bill, not the estimate at the time of the change. Compare against a baseline
that accounts for organic growth, or a rightsizing win looks erased by three new services launching
the same month.

And the one trade nobody should make silently: reliability. Every lever above has a version that
goes too far — the idle load balancer that turns out to be a disaster-recovery standby, the
rightsized instance that starts paging on the next traffic spike, the spot fleet that was never
actually fault-tolerant. Cheaper and broken isn't optimization. If a savings change removes
headroom or redundancy, say so out loud and get sign-off before it ships, don't discover it during
the next incident.
