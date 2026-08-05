---
name: observability
description: Frames the mental model for making a running system explain itself — metrics, logs, and traces as complementary signals, RED and USE checklists, SLOs and error budgets, cardinality as the tax paid for detail. Use this whenever the user asks why something broke with no warning, is deciding what to instrument before a service ships, is choosing between a metric, log, or trace, or asks what observability means beyond "we have dashboards." For metric mechanics use `metrics-and-monitoring`, for logs use `log-management`, for tracing use `distributed-tracing`.
license: MIT
---

# Observability

Monitoring answers questions you thought to ask in advance: is CPU high, is the queue backing up. Observability answers questions you didn't think to ask until the incident was already happening — why did *this* customer's *this* request fail on *this* pod during *this* deploy. You cannot dashboard your way to that; you need enough structured, correlated context emitted at the time the event happened that you can slice it afterward in ways you never pre-built a panel for.

That distinction should drive every instrumentation decision: not "does this look good on a dashboard" but "if this broke at 3am, could I find the cause from what I emitted." **Instrument for the incident you haven't had yet, not the one you just fixed.**

## 1. Pick the signal that matches the question

Metrics, logs, and traces are not interchangeable — each is cheap for a different question and expensive for the others:

| Signal | Answers | Cost driver |
|---|---|---|
| Metric | Is X happening, how much, over what time | Cardinality (label combinations) |
| Log | What exactly happened on this one event | Volume × retention |
| Trace | Where did the time go across services | Sampling rate |

A common mistake is logging what should be a metric (counting errors by parsing log lines) or trying to alert on high-cardinality logs instead of a counter. Decide the signal type before you write the instrumentation, not after storage costs surprise you.

- **Reach for a metric** when the question is "how much / how often / is it trending" and you'll query it repeatedly.
- **Reach for a log** when the question is "what exactly happened on this one event" and you need full detail.
- **Reach for a trace** when the question is "where did the time go" across more than one service.

See `metrics-and-monitoring`, `log-management`, and `distributed-tracing` for how to do each well.

**Done when:** no dashboard or alert is built on counting log lines where a counter would serve, and each signal's type can be traced to the question it answers.

## 2. Cover every service with RED, every resource with USE

Two checklists prevent blind spots without requiring bespoke thought per service. For request-driven services, track **Rate, Errors, Duration** — traffic volume, failure rate, and latency distribution. For anything with finite capacity — CPU, disk, connection pools, queues — track **Utilization, Saturation, Errors**. Applying both mechanically to every new service means you stop discovering gaps during incidents and start discovering them in code review.

Most outages show up first in one of these five numbers. If a service has none of them wired up, that's the instrumentation backlog, not a hypothetical.

- **Rate, Errors, Duration** for anything a request passes through — API, queue consumer, batch job with a throughput target.
- **Utilization, Saturation, Errors** for anything with finite capacity — CPU, memory, disk, connection pools, thread pools.
- **A service missing either checklist** is the next incident's blind spot, not a documentation nicety to backfill later.

**Done when:** every request-driven service exposes RED and every resource-bound dependency exposes USE.

## 3. Carry high-cardinality context, deliberately

The detail that makes an investigation fast — user ID, request ID, pod name, feature flag state — is exactly the detail that makes metrics expensive if attached as labels. The fix isn't avoiding context, it's putting it in the right signal: keep metric labels low-cardinality (service, endpoint, status class) and put the high-cardinality detail in structured logs and trace attributes, correlated by a shared request or trace ID. That correlation ID is the hinge everything else swings on.

- **Metrics stay low-cardinality**: service, endpoint, status class, region — nothing that grows unbounded with traffic.
- **Logs and traces carry the detail**: user ID, request ID, feature flag state, the specific query that ran.
- **A shared correlation ID ties them together**, so a spike on a graph becomes a specific set of logs and a specific trace in one query, not a guess.

**Done when:** you can go from a metric spike to the specific logs and trace for one affected request in under a minute.

## 4. Turn "reliable" into a number

"The service should be reliable" is not falsifiable and cannot gate a release. An SLO — 99.9% of requests succeed under 300ms, measured over 28 days — is. Once you have that number, the error budget (the allowed 0.1%) becomes the shared currency between "ship faster" and "stop shipping and fix reliability," replacing debates about vibes with a number both sides agreed to in advance. Define these before you argue about them mid-incident.

- **The SLI should reflect what the user experiences**, not just what's easy to read off a server log.
- **The target sits below 100%** — deliberately, because chasing the last fraction of a percent is rarely worth the cost.
- **The budget is what turns the target into a decision-making tool**, not just a compliance number nobody consults.

See `slo-definition` for picking SLIs that actually reflect user experience.

**Done when:** every service with real users has an SLO and someone other than the on-call engineer can name it.

## 5. Alert on the symptom, page on the budget

Observability data is worthless if it either never triggers action or triggers it too often to trust. Alert on what the user is experiencing (error rate, latency, budget burn), not on internal causes (a specific pod restarted, disk at 80%) — causes are for debugging, not for waking someone up.

- **Symptoms page**: elevated error rate, degraded latency, budget burning fast.
- **Causes inform the investigation**: which pod, which dependency, which deploy — surfaced on a dashboard, not in the page itself.
- **Multi-window burn-rate alerting on the budget from step 4** is the sharpest version of this: it pages fast for a fast, severe burn and stays quiet for the burn every service has on a bad Tuesday.

Full detail in `alerting`.

**Done when:** every page maps to a symptom a user would notice, and every alert has a documented response, not just a threshold.

## 6. Treat retention and cardinality as a cost you actively manage

Observability data is unbounded by default — every service will happily generate more logs, more label combinations, and more spans than any budget supports. Cost is itself a signal: a sudden spend spike on telemetry often means a cardinality bug (an unbounded label like user ID or request path) shipped to production, not that the system got more interesting.

- **Set retention per signal by how long the question stays relevant** — hot metrics for weeks, raw logs for days, sampled traces from the start, not everything at full fidelity forever.
- **Watch telemetry spend as a leading indicator**, not just an invoice — a step change in cost usually means something changed in the code, not in traffic.
- **Review cardinality contributors on a cadence**, the same way you'd review any other unbounded resource.

**Done when:** telemetry spend is reviewed on a cadence and a cardinality regression shows up as a cost alert, not just a bill.

## Report

State which services have RED/USE coverage, what the SLOs are and where they're defined, whether alerting is symptom-based or still cause-based, and whether logs/traces/metrics are correlated by a shared ID. Name the honest gap — usually incomplete trace coverage, an unmanaged cardinality risk, or a service with dashboards but no SLO — rather than claiming full observability when only metrics are actually in place.
