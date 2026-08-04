# Pillar-by-Pillar Review Checklist

This is the question bank behind step 2 of the review. Work through each pillar and answer every
question with evidence, not intent - a "yes" that nobody can point to a dashboard or test result
for is actually a "no." Questions marked with why-it-matters notes are the ones most likely to
produce a "Now" priority finding; the rest still need answers, but a miss there is more often a
"Next" or "Later."

## Contents

- Operational Excellence
- Security
- Reliability
- Performance Efficiency
- Cost Optimization
- Sustainability
- Scoring and Prioritization

## Operational Excellence

- Is every production change deployed through code review and an automated pipeline, with no
  standing path for manual, undocumented changes? **Why it matters:** manual changes are the
  single most common cause of "nobody knows why this is configured this way" incidents.
- Do runbooks exist for the top five recurring incident types, and were they last validated in
  the past two quarters?
- Is there a single source of truth for on-call rotation, escalation path, and paging thresholds
  that on-call engineers actually trust?
- Are deploys reversible - can the last change be rolled back in minutes without a manual
  database fix-up?
- Is there a blameless post-incident review process, and do its action items actually get closed?
- Are dashboards and alerts owned by the team that gets paged, or inherited from a team that has
  since moved on?
- Is infrastructure defined as code, or does meaningful state live only in a console someone
  clicked through?

## Security

- Is access to production scoped by least privilege and reviewed on a fixed cadence, not granted
  once and never revisited? **Why it matters:** stale broad access is the most common root cause
  behind the blast radius of a compromised credential.
- Are secrets stored in a managed secrets system, with zero secrets committed to source control or
  baked into images?
- Has a vulnerability scan run against this system's dependencies and images in the last 30 days,
  and are criticals tracked to closure?
- Is data encrypted in transit and at rest by default, with no unencrypted path carrying
  sensitive data?
- Is there a tested incident response plan for a credential leak or data exposure, with a named
  first responder?
- Are third-party and vendor integrations inventoried, with their access scope known and
  justified?
- Does the system have a network boundary that actually matches the intended trust model, or has
  it drifted open over time?

## Reliability

- Has the stated failure domain been tested by an actual failure - a chaos exercise, a real
  outage, a DR drill - rather than just designed on paper? **Why it matters:** an untested
  failover is a hypothesis, not a capability, and it tends to fail exactly when it's needed.
- Is there a defined RTO/RPO for this system, and does the last DR drill's actual recovery time
  meet it?
- Does the system degrade gracefully under partial dependency failure, or does one downstream
  outage take the whole system down?
- Are backups tested by restoring them, not just confirmed to exist?
- Is there redundancy across the failure domain that matters for this system (zone, region,
  provider), matched to its actual criticality?
- Are health checks and auto-recovery wired to the failure modes that actually happen in
  production, not just process crashes?
- Is capacity headroom enough to absorb a single-dependency or single-zone loss without cascading?

## Performance Efficiency

- Is there load-test evidence at expected peak traffic, not just steady-state averages? **Why it
  matters:** systems that look fine at average load routinely fall over at peak, and peak is when
  it costs the most to be wrong.
- Are latency and throughput SLOs defined, measured, and visible to the team that owns them?
- Does the system scale (up and down) automatically in response to real load, or does it rely on
  someone noticing and intervening?
- Is the architecture's bottleneck known - which single component caps throughput - and is that
  intentional?
- Are caching and data-access patterns matched to actual read/write ratios, not assumed?
- Has a performance regression ever shipped to production undetected, and if so, what closed the
  gap?

## Cost Optimization

- Does actual spend match the budgeted expectation for this system, or has it drifted without
  anyone noticing? **Why it matters:** unowned cost drift compounds silently and is far more
  expensive to unwind after a year than to catch this quarter.
- Is spend tagged and attributable to a team and a business purpose, with untagged spend near
  zero?
- Is compute and storage rightsized against actual utilization, or provisioned against a
  worst-case guess made at launch and never revisited?
- Are commitment discounts (reserved capacity, savings plans, committed use) applied where usage
  is predictable, without over-committing against volatile workloads?
- Is idle or orphaned infrastructure (unattached volumes, unused environments, forgotten test
  stacks) found and removed on a cadence?
- Does the team have visibility into unit cost (cost per request, per customer, per transaction),
  or only aggregate spend?

## Sustainability

- Is compute and storage rightsized to actual load, avoiding idle capacity that runs (and draws
  power) for no return? **Why it matters:** sustainability and cost efficiency point the same
  direction here - waste found for one pillar is waste found for both.
- Are workloads scheduled or scaled to reduce off-peak resource usage rather than running at
  peak-provisioned capacity around the clock?
- Is data retained only as long as it has a defined purpose, with expired data actually deleted
  rather than accumulated indefinitely?
- Are regions or providers with better carbon intensity considered when latency requirements
  allow the choice?
- Is hardware and instance generation kept reasonably current, since newer generations are
  typically more efficient per unit of work?
- Does the architecture avoid redundant processing or storage (duplicate pipelines, unnecessary
  data copies) that exists from inertia rather than need?

## Scoring and Prioritization

Don't score pillars in isolation and don't average them into a single number - a system with one
severe security gap and five clean pillars is not "83% well-architected," it's a system with a
severe security gap. For every "no" answer collected above:

1. Rate likelihood and impact if the gap is exploited or fails, and separately rate the cost and
   effort to fix it.
2. Rank by risk (likelihood x impact) against effort, using the Now/Next/Later tiers from the main
   skill - cheap fixes for high-risk gaps go first regardless of which pillar they came from.
3. Assign a named owner and a target date to every Now and Next item before the review closes.
   A finding with no owner is not a finding, it's a note that will be forgotten.
4. Carry every open item into the next review cycle and check it closed before scoring anything
   new - a backlog of never-closed findings is itself a finding about the process.
