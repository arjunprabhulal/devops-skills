---
name: feature-flags
description: Decouples deploying code from releasing it to users through runtime feature flags — flag types, targeting rules, and the flag-debt cleanup discipline that keeps the flag system from becoming its own liability. Use this whenever the user wants to gate a feature behind a flag, is asking about kill switches, needs to roll out a change gradually to a subset of users, or has accumulated stale flags nobody remembers the purpose of. For strategies that use flags as part of a rollout mechanism use `deployment-strategies`; for the broader deploy-vs-release distinction use `continuous-delivery`.
license: MIT
---

# Feature Flags

A feature flag turns a deploy-time decision into a runtime decision, which is enormously valuable
for exactly one reason: it lets you separate "is the code safely running in production" from "can
users see the new behavior." That separation is the entire point. Flags misused as a permanent
branching mechanism, left in code long after their purpose is served, become a second,
undocumented configuration system that makes the codebase harder to reason about than not having
flags at all.

Every flag you add is a debt you're taking on with an implicit promise to pay it back by removing
it.

**A feature flag is a temporary bridge between "deployed" and "released" — it should have an
owner and an expected removal date from the moment it's created.**

## 1. Distinguish release flags from operational flags — they have different lifespans

A release flag exists to ramp a specific feature from 0% to 100% of users and then gets deleted
once fully rolled out — its lifespan is weeks, not years. An operational flag (a kill switch for
a risky dependency, a toggle for degrading gracefully under load) is meant to live indefinitely
as a genuine piece of operational tooling. Treating a release flag like it's permanent is how
flag debt accumulates; treating an operational kill switch like it needs to be deleted after
rollout is how you lose a tool you'll need in the next incident.

- **Release flags:** temporary, tied to one feature's rollout, deleted once at 100% and stable.
- **Operational/kill-switch flags:** permanent, tied to resilience, kept and tested like any
  other safety mechanism.
- **Experiment flags:** temporary, tied to an A/B test's duration, deleted once the experiment
  concludes and a winner is picked.

**Done when:** every flag in the system is labeled with its type, and release/experiment flags
have a target removal date.

## 2. Target deliberately, and make the default path the safe one

Flag targeting (percentage rollout, user segment, internal-only) is what makes a flag useful for
buying information gradually rather than an all-or-nothing switch. The default state of any new
flag should be "off" or "old behavior," so that if the flag system itself fails (config service
down, cache stale) the system fails toward the known-safe, already-verified behavior rather than
toward the new, less-proven one.

```
# targeting a canary rollout: internal users first, then 5%, then 50%, then 100%
flag: new-checkout-flow
default: false
rules:
  - if user.internal == true → true
  - if user.id % 100 < 5 → true   # ramp this percentage over days, not minutes
```

**Done when:** the flag evaluation service being unreachable results in every user getting the
old, proven behavior, not the new one.

## 3. Test both code paths, not just the one you're excited about

A flag means two code paths exist in production simultaneously, and it's easy to thoroughly test
the new path while letting the old path's test coverage quietly rot, or vice versa for an
operational kill switch nobody exercises until the incident where it's needed. Both states of
every flag need to be exercised by CI and, ideally, by production canary traffic — an untested
"off" path in a kill switch is a kill switch that might not actually work when you flip it under
pressure.

- **CI runs both flag states** for anything with meaningful branching logic.
- **Kill switches get periodically exercised**, not just written and forgotten — an emergency
  lever tested once in production, deliberately, beats one tested zero times.
- **Combinatorial explosion is real** — more than a handful of interacting flags makes exhaustive
  testing infeasible; keep concurrent flags on any one code path small.

**Done when:** both states of any release flag have been exercised by an automated test in the
last CI run.

## 4. Assign an owner and a removal date at creation time, not after

The single largest source of flag debt is flags created without anyone accountable for removing
them — they work, nobody's in pain, so they stay forever, and eventually the codebase has dozens
of permanent `if` branches for features that shipped years ago. Require an owner and an expected
removal date (or removal trigger: "remove once at 100% for 2 weeks with no incidents") as part of
creating any release or experiment flag, and track flags past their expected removal date the
same way you'd track any other overdue work item.

**Done when:** every release and experiment flag has a named owner and either a removal date has
passed with the flag removed, or there's an active, visible reason it hasn't been.

## 5. Remove the flag, not just set it to 100%

Setting a flag to always-true and walking away is not removal — the conditional, the old code
path, and the flag definition all still exist, still cost cognitive overhead on every read, and
still risk someone accidentally flipping it back. Removal means deleting the flag check, deleting
the dead code path it was guarding, and deleting the flag definition from the flagging system
itself. Budget this as real engineering work, not an afterthought — a flag "done" at 100% rollout
that never gets cleaned up is exactly how flag debt compounds.

**Done when:** the flag's conditional and dead code path are deleted from the codebase, not
merely left permanently on.

## Report

State how many active flags exist, broken down by type (release/operational/experiment), and how
many are past their expected removal date. Name the honest gap explicitly: almost every real
system has some flag debt — say how much, and whether cleanup is a scheduled activity or
something that only happens when someone trips over it.
