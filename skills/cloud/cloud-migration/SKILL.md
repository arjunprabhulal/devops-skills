---
name: cloud-migration
description: Guides moving workloads to or between clouds using the 6 Rs, a phased cutover with a real rollback path, data sync, and avoiding a lift-and-shift that just relocates old problems. Use this whenever the user is planning a cloud migration, choosing between rehost/replatform/refactor, designing a cutover plan, migrating a database to a new provider, or asking why a "simple" migration is stalling. For the target shape use `cloud-architecture`; for sync mechanics use `data-migration`; for running providers long-term use `multi-cloud`.
license: MIT
---

# Cloud Migration

A migration that copies the current architecture verbatim into a new provider ships the current
architecture's problems to a new address, plus a new set of provider-specific quirks nobody has
learned yet. The move itself is rarely the hard part; deciding what to actually change during the
move is.

Every workload deserves an explicit choice among the 6 Rs before it gets touched, and every
cutover deserves a rollback plan tested before the migration is called done. **Decide what you're
changing on purpose, and prove you can go back before you can't.**

## 1. Assign each workload one of the 6 Rs, deliberately

The 6 Rs — retire, retain, rehost, replatform, repurchase, refactor — are a forcing function
against defaulting everything to "rehost" (lift-and-shift) because it's the least work upfront.
Rehosting is often correct for low-value or soon-to-be-decommissioned systems; it's usually wrong
for anything that will live for years, because it carries forward architectural debt at cloud
prices instead of on-prem prices.

- **Retire** what nobody uses — the cheapest migration is not migrating.
- **Rehost** for speed when the system is stable and not worth re-architecting yet.
- **Replatform** to pick up a managed equivalent (self-run DB to managed DB) without a full rewrite.
- **Refactor** only when the business value of the change justifies the schedule risk.

**Done when:** every workload in scope has an assigned R and a one-line reason for it.

## 2. Sequence the migration by dependency and risk, not by ease

Migrate low-risk, low-dependency workloads first to build confidence in the process and tooling,
but track the full dependency graph so you don't strand a migrated service that still needs to
call something on the old side. Cross-environment calls during migration usually mean higher
latency and a temporary hybrid network — plan that connectivity explicitly rather than discovering
it's needed mid-cutover.

**Done when:** the migration order respects the dependency graph and no step assumes a dependency
has already moved when it hasn't.

## 3. Migrate data with continuous sync, not a single copy-and-switch

For anything but the smallest datasets, a one-time copy means the data is stale the moment
traffic starts flowing on the old system after the copy began. Use continuous replication or
change-data-capture to keep source and target in sync until the actual cutover moment, then cut
over with a short, well-understood freeze window. See `data-migration` for the sync mechanics and
`backup-and-restore` for the safety net if the sync itself fails.

**Done when:** source and target data are verified consistent immediately before cutover, with a
freeze window short enough to be acceptable to the business.

## 4. Write the rollback plan before the cutover plan

A cutover plan without a tested rollback is a bet with no exit. Know exactly how to redirect
traffic back to the old environment, how stale the old environment's data will be if you do, and
how long that rollback takes — before you need any of that under pressure. This is the same
discipline as `deployment-strategies`, applied to an environment-level cutover instead of a
release.

```
cutover checklist:
  - [ ] traffic can be redirected back within <N> minutes
  - [ ] old environment's data lag at rollback time is known and acceptable
  - [ ] rollback has been rehearsed at least once, not just documented
```

**Done when:** rollback has been executed in a rehearsal, not just written down.

## 5. Cut over in phases with a canary slice of real traffic

Route a small percentage of real traffic to the new environment before the full switch, and watch
error rates, latency, and cost against the old environment's baseline. A full cutover based only
on staging tests finds its problems in production, at full volume, with no comparison baseline.
For the traffic-shifting mechanics themselves, see `progressive-delivery`.

**Done when:** the new environment has served a canary slice of real production traffic within an
acceptable error-rate band before full cutover.

## 6. Decommission the old environment on a deadline, not indefinitely

A migration isn't done until the old environment is off — running both in parallel indefinitely
doubles cost and doubles the surface for drift between them. Set a decommission date at the start
of the migration and treat slipping it as a signal that something in the cutover isn't actually
trusted yet.

**Done when:** the old environment is decommissioned, or the reason it's still running is written
down with an end date.

## Report

State the R assigned to each workload and why, the data-sync approach and verified consistency at
cutover, and the rollback rehearsal result. Name what was lifted-and-shifted unchanged despite
being known technical debt — that carried-over debt is the honest cost of migration speed, and
pretending it isn't there just defers the reckoning.
