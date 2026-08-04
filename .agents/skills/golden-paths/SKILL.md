---
name: golden-paths
description: Curates the one opinionated, secure-and-observable-by-default way to build a service so the easy option and the right option are the same option. Use this whenever the user creates a service template, standardizes how new services get built, decides what ships enabled by default (logging, tracing, auth), or debates letting every team choose its own stack. For where templates are registered and discovered use `service-catalog`; for how they're provisioned end to end use `self-service-infrastructure`; for the platform surface they live on use `internal-developer-platform`.
license: MIT
---

# Golden Paths

A golden path is a single, curated, well-supported way to do something common — start a new
service, add a queue, wire up a database — that comes with security, observability, and reliability
built in by default. It's not a rule enforced by review; it's the option that requires the least
effort, so following it is what happens by default rather than what has to be argued for.

Deviation from the golden path should always remain possible, but it should be a deliberate,
visible choice — never an accident born of the path being harder to find than the workaround.
**The golden path wins by being the least amount of work, not by being the only option allowed.**

## 1. Bundle the boring-but-critical defaults in, not bolted on after

Structured logging, tracing instrumentation, health checks, and a baseline auth setup are exactly
the things teams skip under deadline pressure if they're left as separate steps. A golden-path
template that generates a service with these already wired in means "secure and observable" is the
starting state, not a backlog item someone has to remember to schedule. See `observability` and
`kubernetes-security` for what belongs in the defaults themselves — this skill is about making sure
they ship pre-wired, not about their individual configuration.

- **Structured logs and a trace exporter configured out of the box**, pointed at the real
  platform sinks, not stubbed.
- **A working health/readiness endpoint** from the first commit, so autoscaling and rollout
  checks function immediately.
- **Sane default resource limits and an auth baseline**, not left at "unset" for someone to
  discover the hard way in an incident.

**Done when:** a service scaffolded from the golden path passes a production-readiness review
with zero changes.

## 2. Keep exactly one supported path per common task

Three "recommended" ways to deploy a service is the same as zero recommended ways — everyone picks
a different one and the platform team ends up supporting all three. Consolidate to one template per
task, retire the others deliberately, and resist the urge to add a second option just because one
team prefers a different framework. Discoverability depends on this too: `service-catalog` can only
guide people to "the" template if there's a single unambiguous one to point at.

**Done when:** for any common task, a developer asking "how do I do X" gets pointed to exactly one
template, not a menu of alternatives to choose between.

## 3. Version the path and give migration a deadline

A golden path frozen at its first release becomes a golden path to yesterday's best practices — the
security baseline it shipped with drifts out of date while every service built from it stays
un-patched. Version templates explicitly, and when a new version fixes something that matters
(a vulnerable default, a deprecated API), give existing services a real migration deadline instead
of leaving the old version quietly supported forever.

| Path version | Status | Migration deadline |
|---|---|---|
| v3 (current) | actively supported | — |
| v2 | deprecated, security-patched only | 90 days |
| v1 | unsupported | already past due |

**Done when:** every service knows which version of its golden path it's on, and no version is
"quietly still fine" without an actual support commitment behind it.

## 4. Make deviation visible, not invisible

Teams will sometimes have a real reason to step off the path — a genuine performance constraint, an
external requirement the template doesn't cover. That's fine; what's not fine is a deviation nobody
can see. Require deviations to be declared (a flag in the catalog entry, a documented exception),
so the platform team can track how often and why people leave the path instead of discovering it
during an incident. A pile of undeclared deviations is the strongest signal the path itself needs
to change.

**Done when:** every service that deviates from its golden path has that deviation recorded and
visible in `service-catalog`, with a stated reason.

## 5. Treat frequent deviation as a signal to widen the path, not a compliance problem

If half the org deviates from the same golden-path default, the default is wrong for your org, not
the org wrong for deviating. Review deviation patterns regularly and fold the common ones back into
the template as a supported option, rather than treating every deviation as a violation to chase
down. A golden path that never changes in response to real usage will keep losing relevance until
nobody uses it at all.

**Done when:** the last golden-path update was driven by an observed deviation pattern, not just
the platform team's own roadmap.

## Report

State which templates are currently golden, their version and migration deadlines, and what ships
enabled by default in each. Name the most common deviation you're seeing and whether it's been
folded back into the path yet — an unaddressed deviation pattern is the honest signal the path
doesn't fit reality, and naming it beats claiming full compliance.
