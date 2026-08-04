---
name: cost-optimization
description: Cuts cloud spend without cutting reliability by finding the few levers that move most of the bill — idle and orphaned resources, over-committed on-demand spend that qualifies for reserved or savings-plan discounts, and oversized fleets — and going after them in dollar order. Use this whenever the user asks how to reduce their cloud bill, reacts to a cost spike or a finance escalation, wants to find waste, or is deciding between on-demand, reserved, and spot pricing. For matching resource size to real usage use `rightsizing`, and for knowing who owns each dollar use `resource-tagging`.
license: MIT
---

# Cost Optimization

Cloud bills rarely have one villain — they have a long tail of small waste and a short list of
big levers. Teams that start by auditing every line item burn weeks on savings measured in
dollars, while the resource that's 40% of the bill sits untouched because nobody sorted by size
first. Optimization is a prioritization problem before it's an engineering problem.

The other trap is treating cost cutting as a one-time project. Spend drifts every time someone
ships a new service, forgets to delete a test environment, or a traffic pattern shifts enough to
make last quarter's instance sizes wrong. A cost review that runs once and declares victory is
already stale by the next billing cycle.

**Find the biggest lever with data, pull it, then come back for the next one.**

For a ranked catalog of savings levers and how to find candidates, read
`references/savings-levers.md`.

## 1. Rank levers by dollar impact before touching anything

Sort the bill by service, then by resource, before deciding what to fix. A single oversized
database instance can dwarf a dozen idle load balancers combined, and no amount of enthusiasm for
cleaning up small things substitutes for finding the one thing that's actually expensive.

- **Pull the billing export or cost-explorer report first** — don't optimize from memory of what
  "feels" expensive.
- **Work top-down** — the top five line items usually explain most of the spend variance.
- **Ignore anything under a threshold that isn't worth an engineer's time** — a $20/month savings
  is not worth a change-review cycle.

**Done when:** the top five cost drivers are known by name and dollar amount, not by guess.

## 2. Kill idle and orphaned resources first — they buy nothing

An idle resource — a stopped-but-not-deleted instance, an unattached volume, a load balancer with
no healthy targets, a snapshot nobody restores from — delivers zero value at full price. Unlike
rightsizing or commitment purchases, removing it carries no performance trade-off to weigh, which
makes it the fastest win available.

- **Unattached storage volumes and old snapshots** accumulate silently after every resize or
  redeploy that doesn't clean up after itself.
- **Load balancers and IPs with no traffic** are easy to find and carry no risk to remove.
- **Non-production environments left running** outside business hours are pure waste multiplied
  by however many nights and weekends they sit idle.

**Done when:** every resource flagged as idle for 30+ days is either justified in writing or
deleted.

## 3. Buy commitment discounts only for the baseline you're sure of

Reserved instances and savings plans trade a discount for a commitment — they pay off only against
usage you're confident will persist. Committing against your peak, or against usage you haven't
rightsized yet, locks in savings on top of waste instead of on top of real need.

- **Commit against the sustained floor**, not the peak — use on-demand or spot to cover the
  variable part above it.
- **Rightsize before you buy commitments**, not after — a commitment against an oversized fleet
  bakes the oversizing in for the contract term.
- **Stagger commitment terms** so you're never re-betting the whole fleet at once as usage
  patterns evolve.

**Done when:** committed spend covers a measured baseline, not a hopeful estimate, and no
commitment was purchased before the underlying fleet was rightsized.

## 4. Rightsize before you optimize pricing

A perfectly-priced instance that's twice the size it needs to be is still twice the cost it needs
to be — pricing optimization and sizing optimization are independent levers, and skipping the
sizing one leaves money on the table no discount can recover. See `rightsizing` for how to size
from measured usage instead of guessing.

**Done when:** no cost-optimization pass ships without checking whether the resource is the right
size, not just the right price.

## 5. Treat tagging as a prerequisite, not an afterthought

You cannot prioritize by dollar impact, attribute an idle resource to an owner, or hold a team
accountable for its own spend if resources aren't tagged to a cost center or owner. Cost
optimization work done on untagged infrastructure degrades into guessing who to ask before
anything can be deleted. See `resource-tagging` for the taxonomy and enforcement mechanics.

**Done when:** every resource under review is tagged well enough to identify an accountable owner
without asking around.

## 6. Re-run the analysis on a cadence, not once

Spend drifts continuously — new services launch, traffic patterns shift, commitments expire. A
cost review that happens once and is declared done misses every dollar of drift that accumulates
afterward, and the next spike arrives looking just as urgent as the last one.

- **Schedule the review**, don't wait for a finance escalation to trigger it.
- **Track savings realized versus identified** — a list of recommendations that never gets acted
  on isn't optimization.

**Done when:** cost review is a recurring calendar item with an owner, not a one-off project.

## Report

State the top cost drivers found, the dollar amount of idle/orphaned waste removed, and the
commitment coverage achieved against the measured baseline. Name the honest gap — usually a
category of spend (data transfer, third-party SaaS, an unrightsized fleet still under commitment)
that wasn't fully addressed this pass — rather than claiming the bill is now optimal.
