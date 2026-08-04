---
name: chaos-engineering
description: Deliberately injects controlled failure into a system to find weaknesses before they find you in production, using a stated hypothesis, a bounded blast radius, and a defined steady-state metric to verify against. Use this whenever the user wants to run a game day, test resilience by killing pods or nodes, ask "what happens if this dependency goes down," or validate that a failover or circuit breaker actually works. For the drill that validates region/backup failover use `disaster-recovery`; for injecting load rather than failure use `load-testing`.
license: MIT
---

# Chaos Engineering

Most systems have never actually experienced the failures their architecture claims to handle.
The retry logic, the circuit breaker, the multi-AZ failover — these are assumptions that live
in a design doc until something breaks them for real, usually in production, usually at the
worst time. Chaos engineering moves that first real test from an incident to a planned
experiment, where you control the timing and the blast radius.

The point is not to break things randomly — random breakage is what production does on its
own. The point is to test a specific belief about how the system behaves under a specific
failure, and find out you were wrong somewhere safer than 3am on a Saturday.

**Test a stated hypothesis about failure, don't just cause chaos.**

## 1. Start from a hypothesis, not a stunt

"Let's kill a random pod and see what happens" is not an experiment, it's a demo. A real chaos
experiment states, in advance, what you believe will happen — "if we kill the primary database
instance, the read replica promotes within 30 seconds and error rate stays under 1%" — so that
when reality diverges from the belief, you have found something specific and actionable, not
just a surprising graph.

- **Write the hypothesis before running anything** — what you expect, and the metric that
  would prove or disprove it.
- **Base it on a real dependency**, not an arbitrary one — pick failures your architecture
  actually claims to survive.
- **A confirmed hypothesis is still valuable** — it's evidence the system works as designed,
  not a wasted experiment.

**Done when:** the experiment has a written hypothesis and a specific metric that will confirm
or refute it.

## 2. Define steady-state before you break anything

You cannot tell whether an experiment caused harm if you don't know what "normal" looked like
a minute before you started. Steady-state is a small set of metrics — error rate, latency,
throughput — that represent the system behaving correctly, measured and agreed on before
injection starts.

```
steady_state:
  error_rate: < 0.5%
  p99_latency: < 400ms
  checkout_success_rate: > 99%
```

- **Use business-relevant metrics**, not just infrastructure ones — "checkout succeeds" tells
  you more than "CPU is nominal."
- **Confirm steady-state holds for a few minutes before injecting** — don't start an
  experiment during an unrelated blip.
- **The experiment's success criterion is "steady-state holds through and after"**, not
  "nothing crashed."

**Done when:** steady-state metrics and their acceptable thresholds are defined and observed
as normal before injection begins.

## 3. Bound the blast radius deliberately

An experiment that can take down more than you intended is not an experiment, it's an incident
you started on purpose. Scope every chaos run to the smallest slice that still tests the
hypothesis — one pod, one AZ, a percentage of traffic — and have a kill switch that's faster
than the damage can spread.

- **Scope to a percentage or a single instance first**, widen only after it's proven safe.
- **Always have an automatic abort** — if steady-state metrics breach a hard threshold, the
  experiment stops itself, it does not wait for a human to notice.
- **Run during business hours with responders present**, not at 2am unattended — the whole
  point is controlled conditions.

**Done when:** the experiment has an explicit scope limit and an automatic abort condition,
both tested before the first real run.

## 4. Progress from staging to production deliberately

Staging never fully represents production traffic patterns, data volume, or scale — some
failure modes only appear under real load. But production chaos without staging first is
reckless. The right sequence is staging to validate the experiment mechanics are safe, then
production with a small blast radius, widening only as confidence builds.

- **Staging tells you the experiment tooling and abort mechanism work** — it does not tell you
  how the real system behaves under real load.
- **The first production run should target the smallest reasonable slice** and be ready to
  abort, even if staging went perfectly.
- **Some things only chaos-test safely in production** — DNS failover, cross-region traffic
  shifts — because staging's topology doesn't match; be honest about that gap rather than
  pretending staging coverage is equivalent.

**Done when:** the experiment has run successfully in staging and at least once in production
at limited scope.

## 5. Run it as a game day, not a solo script

A chaos experiment run alone by one engineer against a dashboard only tests the system. A game
day — with the on-call team, the IC, and the actual alerting and paging path all live — tests
the system *and* the humans and process meant to respond to it. That's usually where the more
valuable findings are: alerts that don't fire, runbooks that are stale, an on-call engineer
who didn't know this dependency existed.

- **Page for real** — trigger the actual alerting path, not a simulated one, to test whether
  it works.
- **Have the responder use the real runbook** — see `runbooks` — and note where it was wrong
  or missing.
- **Debrief immediately after**, while the experience is fresh, and file findings the same way
  as an incident postmortem.

**Done when:** a game day has exercised the real alert and response path, not just the failure
injection itself.

## 6. Turn every finding into a fix, not a footnote

An experiment that reveals a weakness and then goes nowhere is worse than not running it — it
means the organization now knows about a gap and left it open. The output of chaos engineering
is a prioritized list of concrete fixes, tracked the same way a production bug would be.

- **File every gap as a ticket with an owner**, not as a line in a slide deck.
- **Re-run the same experiment after the fix ships** to confirm it actually closed the gap.
- **Build a library of experiments** you re-run periodically — resilience regresses silently
  as the system changes underneath it.

**Done when:** every finding from the experiment has a tracked owner, and previously-fixed
experiments are scheduled to re-run.

## Report

State the hypothesis tested, the steady-state metrics and whether they held, the blast radius
used, and every gap the experiment surfaced. Name explicitly which failure modes are still
untested — a system that has only been chaos-tested against pod death has not been
chaos-tested against region loss or dependency failure, and claiming resilience beyond what
was actually tested is the exact overconfidence this practice exists to prevent.
