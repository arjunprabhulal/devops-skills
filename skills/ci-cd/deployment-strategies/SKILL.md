---
name: deployment-strategies
description: Chooses and implements the deployment technique — blue-green, canary, rolling, or shadow — that buys the most information before you're fully committed, plus the rollback plan that makes each one safe. Use this whenever the user asks how to deploy with zero downtime, wants a canary or blue-green setup, is worried about a risky rollout, or is planning a DB migration alongside a code deploy. For deciding whether to release deployed code at all use `feature-flags`; for a Kubernetes-native rollout use `progressive-delivery`.
license: MIT
---

# Deployment Strategies

A deployment strategy is really a question of how much information you buy before you're fully
committed, and how expensive backing out is if that information is bad. Rolling deploys buy
almost nothing (all pods eventually run the new version, fast) but are cheap; canaries buy a lot
(real traffic against a small blast radius) at the cost of complexity; blue-green buys instant
rollback at the cost of running double infrastructure. Pick based on the blast radius of being
wrong, not on what's trendy.

The deploy itself is rarely the risky part — not having a tested way back out is.

**Every deployment strategy is a trade between how much you learn before full exposure and how
fast and cheaply you can undo it if you learn something bad.**

## 1. Match the strategy to the blast radius, not the org's default

Rolling updates are the right default for most internal services and low-risk changes —
Kubernetes does this natively, it's cheap, and a bad version only affects a fraction of traffic
briefly before it's caught by a readiness probe. Reach for canary or blue-green when the cost of
a bad version reaching real users is high (payment paths, anything customer-facing at scale) or
when the change touches something readiness probes can't catch, like subtle data corruption or
latency regressions.

- **Rolling:** default choice; cheap; bounded but not zero exposure during rollout.
- **Canary:** route a small percentage of real traffic to the new version, watch metrics, expand
  gradually — buys real-world signal at low blast radius.
- **Blue-green:** two full environments, instant traffic switch, instant rollback — most
  expensive to run, fastest to reverse.
- **Shadow:** mirror real traffic to the new version without serving its responses — buys
  behavioral signal with zero user-facing risk, but only for read paths.

**Done when:** the blast radius is written down as a number — users or percent of traffic exposed
before the first health gate — and that number is what the rollout actually enforces.

## 2. Treat rollback as a feature you test, not a hope

A rollback plan that has never been executed is a guess. If "roll back" means "redeploy the
previous artifact," verify that artifact is still available (see `artifact-management`) and that
redeploying it actually restores the previous behavior — not just the previous code, but
compatibility with whatever state (DB schema, message formats, feature flags) the system is
currently in. Practice rollback on a low-stakes deploy occasionally so the first time it's used
under pressure isn't the first time it's used at all.

```bash
# the two questions that matter before any deploy ships:
# 1. what's the exact command/pipeline job to roll back?
# 2. how long does rollback take, end to end, measured — not estimated?
```

**Done when:** someone who did not write the deploy can execute the rollback from the runbook
alone, and it has been timed at least once.

## 3. Separate deploy from release for anything risky

Deploying new code and exposing it to users are different actions, and collapsing them removes
your safety margin. A canary or blue-green switch is still a full release the instant it takes
traffic; wrapping the risky code path in a feature flag lets you deploy fully, verify health with
zero users on the new path, then ramp exposure independently of the deploy. This is the sharper
tool for anything where "50% of pods have the bug" (rolling) is still too much exposure. See
`feature-flags` for flag mechanics and cleanup discipline.

**Done when:** for any deploy marked risky, there's a way to reduce user exposure to zero without
also reverting the deploy.

## 4. Make the database change survive both old and new code

The single most common cause of a "successful" rollback that still causes an outage is a database
migration that isn't backward compatible — the old code can't run against the new schema. Every
schema change during a rolling or canary deploy must work for both versions simultaneously,
because for some window, both are running. Expand/contract is the pattern: add the new
column/table first (deploy N), migrate reads/writes to it (deploy N+1), only then drop the old
one (deploy N+2) — never combine "add" and "remove" in the same release.

- **Additive first:** new columns nullable or defaulted, new tables don't break old queries.
- **Dual-write or backfill** during the transition window if both versions must stay correct.
- **Drop only after** every version that reads the old shape is fully retired.

**Done when:** the previous code version, if rolled back to, runs correctly against the current
database state.

## 5. Watch the signal that actually predicts failure, not just uptime

A canary that's "up" but silently slower, erroring on a rare code path, or corrupting a fraction
of writes will pass a naive health check and still cause damage. Pick metrics specific to the
change being shipped (error rate on the affected endpoint, p99 latency for the affected path, a
business metric if the change touches revenue logic) rather than generic infra metrics alone, and
automate the canary's promote/abort decision on those metrics wherever the strategy supports it.
See `metrics-and-monitoring` for building the underlying signal.

**Done when:** the canary or rollout stage has an automated abort condition, not just a person
watching a dashboard and hoping.

## Report

State which strategy was chosen and why given the blast radius, what the rollback procedure is
and whether it's been tested, and how the database migration (if any) stays compatible across the
version boundary. Name the honest gap: usually it's an untested rollback, a metric that isn't
wired to an automated abort, or a schema change that quietly assumes the old code is already
gone.
