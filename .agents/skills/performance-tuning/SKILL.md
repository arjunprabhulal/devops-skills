---
name: performance-tuning
description: Guides systematic performance work — measuring before changing, finding the actual bottleneck with the USE method (Utilization, Saturation, Errors), optimizing the real hot path, and verifying the fix moved the number that matters. Use this whenever the user asks why something is slow, wants to make a service faster, or is about to tune JVM flags or database indexes without data. For finding the hot path itself use `profiling`, for generating load to test under use `load-testing`, and for designs where the bottleneck moves out use `scalability-design`.
license: MIT
---

# Performance Tuning

Most performance work fails before it starts, because it starts with a change instead of a
measurement. Someone bumps a thread pool, adds an index, or increases memory, the number moves
a little, and nobody can say whether it was the change or noise. Tuning without a baseline is
not engineering, it is folklore that happens to run in production.

The fix is a discipline, not a tool: measure the current state, form a hypothesis about the
bottleneck, make one change, and measure again against the same baseline. Anything that skips
a step is a guess wearing a lab coat.

**If you can't point to the metric that proves the change worked, you haven't tuned anything.**

For the USE method applied resource-by-resource with the exact Linux commands, read
`references/use-method.md`.

## 1. Establish a baseline before touching anything

A baseline is the number you will compare every change against — latency at a given percentile,
throughput at a given error rate, cost per request. Without it, "faster" is a feeling, and
feelings regress silently when someone else's change ships next week.

- **Capture the full distribution, not an average** — p50 hides the p99 problem that users
  actually feel.
- **Record the load level the baseline was taken at** — a number without its traffic context
  cannot be compared later.
- **Freeze the environment while measuring** — comparing a tuned staging box to an untuned
  production box tells you about the environment, not the change.

**Done when:** there is a written baseline number, its percentile, and the load level it was
measured under.

## 2. Find the bottleneck with the USE method

Utilization, Saturation, Errors — for every resource in the request path, check whether it is
busy, queueing, or failing. The instinct is to tune the component you understand best; the USE
method forces you to check the one that is actually constrained instead.

| Resource | Utilization | Saturation | Errors |
|---|---|---|---|
| CPU | % busy | run-queue length | throttling events |
| Memory | % used | swap / page faults | OOM kills |
| Disk / network | % busy | queue depth | retransmits, retries |

- **Saturation, not utilization, predicts the cliff** — a CPU at 60% with a growing run queue is
  closer to failure than one at 90% with none.
- **Check every resource in the path**, not just the obvious one — the database connection pool
  is a resource too.
- **Stop guessing once one resource shows saturation or errors** — that is the bottleneck until
  proven otherwise.

**Done when:** one resource is identified as saturated or erroring, with the metric that shows
it, and the rest are ruled out.

## 3. Change one thing, then remeasure against the baseline

A tuning session that changes five settings at once and reports "it's faster now" has learned
nothing reusable — nobody knows which change mattered, and the next regression will require
redoing all of it blind. One change, one remeasurement, one recorded delta.

- **Write the hypothesis before the change** — "increasing pool size should reduce queue wait" —
  so a null result is informative instead of confusing.
- **Revert changes that don't move the baseline metric** — a change that doesn't help is
  complexity with no payoff, not a free improvement to keep.
- **Watch for a bottleneck that just moved** — fixing the database often reveals the app server
  was the real limit all along; expect another round.

**Done when:** each applied change has a recorded before/after delta on the same baseline metric.

## 4. Optimize the hot path, not the path you know best

Time spent making a function that runs once per request 10% faster is wasted if a different
function runs 10,000 times per request. Let `profiling` tell you where time is actually spent,
then fix the disproportionate cost, even when it means touching unfamiliar code.

- **Fix the biggest contributor first** — a 5% speedup on 80% of the time beats a 50% speedup on
  2% of the time.
- **Watch for algorithmic wins over micro-optimizations** — an O(n²) call in a loop beats any
  amount of constant-factor tuning.
- **Beware caching as a first move** — it hides a slow path instead of fixing it, and adds
  invalidation risk; use it once the real cost is understood.

**Done when:** the change targets the largest measured contributor to the baseline metric, not
the most familiar code.

## 5. Verify under realistic load, not a synthetic single request

A change that helps one hand-run request can regress under concurrency — lock contention,
connection pool limits, and GC pauses only appear under real traffic shape. Confirm the win with
`load-testing` at production-like concurrency before calling it done.

- **Re-run the exact baseline scenario**, same load level and duration, not a friendlier one.
- **Check for new bottlenecks introduced by the fix** — a bigger cache can trade latency for
  memory pressure elsewhere.
- **Watch resource cost alongside speed** — a change that halves latency by doubling instance
  count is a scaling decision, not a tuning win; that tradeoff belongs in `scalability-design`.

**Done when:** the improvement holds under a load test that matches the original baseline's
concurrency and duration.

## 6. Record what changed and why, so it survives the next engineer

An untracked tuning change looks like an arbitrary setting to the next person who touches the
system, and they either revert it by accident or are afraid to touch it at all. Document the
bottleneck found, the change made, and the measured effect next to the config itself.

- **Link the change to its measurement**, not just a commit message saying "perf improvements."
- **Note the load level the tuning was valid for** — a setting tuned for today's traffic may be
  wrong at 10x; flag it for revisit in `capacity-planning`.

**Done when:** the change, its cause, and its measured effect are documented next to the
configuration that changed.

## Report

State the baseline metric and its value, the bottleneck identified via USE, the specific change
made, and the measured before/after delta under load. Name honestly which resources were never
checked or which change was applied without a controlled remeasurement — an unverified tuning
change is a regression waiting for the next traffic increase, and saying so is worth more than a
confident number nobody can reproduce.
