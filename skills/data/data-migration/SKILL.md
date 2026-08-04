---
name: data-migration
description: Covers changing schema or data shape without downtime using expand-then-contract — adding new structures alongside old, backfilling historical data in batches, dual-writing during the transition, verifying both old and new code paths, and keeping every step independently reversible. Use this whenever the user renames a column, changes a data type, moves data between tables, backfills a new field, or asks how to migrate without a maintenance window. For deploy sequencing of each phase use `deployment-strategies`, and for day-to-day database operations use `database-operations`.
license: MIT
---

# Data Migration

The instinct when a schema needs to change is to write one migration that gets the database
from old shape to new shape and run it. That instinct is exactly what causes downtime: a
single atomic cutover means the old code and the new code cannot both be correct at the same
moment, so somewhere in the deploy there is a window where reads or writes are wrong.

The fix is to stop treating "old schema" and "new schema" as two states connected by one
migration, and instead treat the migration as a sequence of states where old and new coexist,
each individually safe, each individually undoable.

**A migration that cannot be paused halfway through, with both old and new still working, is
not actually a migration — it is a scheduled outage with a script attached.**

For a worked SQL walkthrough of the expand, backfill, and contract phases, read
`references/expand-contract.md`.

## 1. Split every migration into expand, migrate, contract

Expand-then-contract is the pattern underneath every zero-downtime schema change: add the new
thing without touching the old thing, move the data, then remove the old thing only once
nothing depends on it anymore.

- **Expand**: add the new column, table, or field alongside the existing one. Nothing reads or
  depends on it yet, so this step alone cannot break anything running in production.
- **Migrate**: backfill historical data and start writing to both old and new. This is the
  phase with real risk, and it is where the rest of this skill's sections apply.
- **Contract**: once every reader has moved to the new shape and it has run correctly for a
  observation period, remove the old column, table, or field.

Each phase ships as its own deploy, sequenced with normal rollout controls — see
`deployment-strategies` for how to stage and gate a rollout, since migration phases are just
deploys with an extra constraint: the previous phase must already be stable in production.

**Done when:** the migration is written as three separate, independently deployable changes,
not one script that jumps from old shape to new shape.

## 2. Backfill in small, resumable batches

A backfill that updates every row in one transaction locks the table for its full duration and
either completes entirely or rolls back entirely — on a large table, neither outcome is
acceptable.

- **Batch by a bounded key range or row count**, committing each batch separately, so a
  failure partway through loses only the current batch, not the whole backfill.
- **Throttle between batches** to leave headroom for production traffic; an unthrottled
  backfill competing with live queries for I/O will show up as latency elsewhere.
- **Make the backfill idempotent and resumable** — re-running it after an interruption should
  pick up where it left off, not double-write or error out.

**Done when:** the backfill can be paused and resumed without manual intervention or risk of
double-processing a row.

## 3. Dual-write only as long as necessary

During the migrate phase, the application writes to both the old and new location so that
either can serve reads. Dual-writing is a temporary bridge, not a permanent architecture, and
it carries its own risk: a write that succeeds to one side and fails to the other.

- **Write to the new location first, then the old**, or wrap both in a mechanism that detects
  and reconciles drift — silent divergence between the two is the main failure mode to guard
  against.
- **Monitor for divergence explicitly** — a periodic comparison job that flags rows where old
  and new disagree, rather than assuming the dual-write is correct because no errors surfaced.
- **Set a deadline for how long dual-writing runs.** An open-ended dual-write phase becomes
  permanent complexity that nobody remembers to remove.

**Done when:** a divergence check between old and new data sources has run clean, and a date
is set for ending the dual-write phase.

## 4. Verify both code paths before touching the old one

The whole point of expand-then-contract is that at every phase, both the old and new code
paths are live and correct — which only holds if both have actually been verified, not just
the new one that got the attention during development.

- **Run the same test suite against both paths**, or add explicit tests that assert old and
  new produce equivalent results for the same input.
- **Use a feature flag to control which path serves live traffic**, so verification can happen
  gradually against real traffic percentages rather than an all-or-nothing switch — see
  `feature-flags` for the mechanics of that rollout.
- **Confirm the new path under real production load**, not just synthetic tests, before the
  contract phase removes the option to fall back.

**Done when:** the new code path has served production traffic correctly at full volume before
the old path is scheduled for removal.

## 5. Keep every step independently reversible

The value of splitting a migration into phases evaporates if any individual phase cannot be
undone. Reversibility per-step is what makes each phase low-risk enough to ship with normal
deploy confidence instead of migration-specific dread.

- **Keep the old column or table intact through the migrate phase** so a rollback of the
  application deploy does not also require an emergency data rollback.
- **Write the contract-phase removal as its own reversible deploy** wherever the platform
  allows it (a soft delete or renamed-not-dropped column) before a true destructive drop.
- **Avoid combining a schema change with a data type change** in the same phase — each
  independent change should have its own independently reversible step.

**Done when:** any single phase of the migration can be rolled back without requiring a rollback
of any other phase.

## 6. Delete the old path deliberately, not by accident

The contract phase is the one that is actually destructive, and it is also the one people rush
because the migration has been "basically done" for weeks by the time they get to it.

- **Confirm nothing still reads the old column or table** — check application code, ad hoc
  queries, and downstream consumers like analytics pipelines, not just the primary service.
- **Keep a backup or export of the removed data** for a defined retention window after the drop,
  in case something unmonitored was still depending on it.

**Done when:** the old structure has been removed, its removal was intentional and reviewed,
and a backup of the pre-removal state exists for the agreed retention window.

## Report

State which phase (expand, migrate, or contract) the migration is currently in, whether
dual-writing is active and its planned end date, and the result of the last old/new divergence
check. Name the honest gap — usually a dual-write phase running longer than planned, or an old
code path that has not been fully confirmed unused — rather than declaring the migration
complete before the contract phase has actually shipped.
