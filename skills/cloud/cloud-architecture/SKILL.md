---
name: cloud-architecture
description: Designs systems for the cloud's actual shape — regions and availability zones, managed vs self-run tradeoffs, statelessness, failure-domain isolation, and the cost and lock-in consequences of each choice. Use this whenever the user is choosing a region topology, deciding between a managed service and self-hosting, sketching a new system's compute and data layout, or asking why an architecture is expensive or fragile. For the virtual network layer use `cloud-networking`; for moving an existing workload use `cloud-migration`; for scoring an existing system use `well-architected-review`.
license: MIT
---

# Cloud Architecture

The cloud is not a bigger data center; it is a set of failure domains with prices attached. Every
region, zone, and managed service is a boundary that fails independently and bills differently.
Architecture in the cloud is mostly the discipline of choosing which boundaries your system can
survive crossing, and which ones you pay to avoid.

Most bad cloud architectures are not wrong on features — they are wrong on failure domains, built
as if a region or a disk is permanent. **Design for the boundary to fail, then decide what you're
willing to pay to make that survivable.**

## 1. Put failure domains on paper before compute

Draw the regions, zones, and managed-service boundaries before you draw a single instance or
container. Every one of those lines is a place where a real outage has happened to someone. A
single-AZ deployment is a bet that AZ never fails; a single-region deployment is a bet the region
never does. Neither bet needs to be wrong — but it must be a decision, not a default.

- **Zones** protect against power, network, and hardware failure at low latency cost and low
  effort — use them for anything worth being up during a routine outage.
- **Regions** protect against correlated failures (control-plane bugs, natural disasters) at real
  latency and data-consistency cost — reserve multi-region for the workloads that justify it.
- **Managed-service boundaries** (a database's own failover, a queue's durability guarantee) often
  give you more resilience per dollar than DIY replication across zones.

**Done when:** every major component has a stated failure domain and a stated blast radius if
that domain goes down.

## 2. Default to managed, justify self-run

A managed database, queue, or cache pushes operational failure modes onto someone whose full-time
job is not failing at them. Self-running the same thing is sometimes right — cost at scale,
a feature the managed version lacks, regulatory control — but it is a decision with an ongoing
staffing cost, not a one-time engineering cost. Write down the reason, because in a year someone
will ask why you're patching a database cluster by hand.

**Done when:** every self-run component has a written reason it isn't managed, and that reason is
still true.

## 3. Make statelessness the default for compute

Stateless compute can be killed, replaced, and scaled horizontally without a runbook. State that
must survive a restart belongs in a database, object store, or managed cache — not on local disk,
not in process memory. This single rule is what makes autoscaling, rolling deploys, and zone
failover boring instead of terrifying. See `stateful-workloads` for the cases where state on the
compute layer is genuinely unavoidable, and `caching-strategies` for keeping a fast local cache
without making it a source of truth.

**Done when:** killing any compute instance without warning loses no data and no in-flight
correctness.

## 4. Price the architecture before you build it

Every architectural choice — cross-AZ traffic, multi-region replication, a managed service's
per-request pricing — has a cost curve that is invisible until the bill arrives. Cross-zone and
cross-region data transfer is usually the surprise line item, not compute. Estimate it from
expected traffic, not from the diagram looking clean. For the ongoing discipline of catching cost
drift, use `cost-optimization`; this step is about not committing to a shape that is expensive by
construction.

**Done when:** the dominant cost drivers of the design are named and estimated, not just guessed.

## 5. Name the lock-in and decide if it's worth it

A managed queue, a proprietary database API, a provider-specific serverless trigger — each buys
convenience by binding you to one vendor's implementation. That is frequently a good trade: the
switching cost you're avoiding by not building portability you'll never use is real. It is a bad
trade only when you can't articulate why you took it. Do not build abstraction layers "just in
case" — that is its own cost, covered in `multi-cloud`.

**Done when:** each vendor-specific dependency has a one-line justification, not just a shrug.

## 6. Re-draw the diagram when traffic or team shape changes

An architecture sized for one region and ten engineers does not automatically stay right at ten
regions and two hundred engineers. Revisit the failure-domain diagram and the managed/self-run
list on a cadence, not only after an incident forces it.

**Done when:** the architecture diagram and its assumptions have an owner and a review date.

## Report

State the failure domains chosen (zone-, region-, or multi-region-tolerant) and why, which
components are managed vs self-run and the reason for each self-run exception, and the estimated
dominant cost driver. Name the biggest untested assumption in the design — usually "we have never
actually lost a full region" — because that gap is the real risk, not the diagram.
