---
name: serverless
description: Covers functions and managed compute where the platform enforces statelessness and bills per request — cold starts, event-driven design, concurrency limits, and when serverless does not fit. Use this whenever the user is writing a Lambda/Cloud Function/Azure Function, designing an event-driven pipeline, debugging cold-start latency, hitting concurrency throttling, or asking whether to move a workload to serverless. For managed-vs-self-run tradeoffs use `cloud-architecture`; for containers use `kubernetes-operations`; for scheduled batch use `scheduled-jobs`.
license: MIT
---

# Serverless

Serverless is not "no infrastructure" — it is infrastructure with the operational knobs replaced
by a billing meter and a set of hard limits you don't control. The platform enforces statelessness,
imposes concurrency ceilings, and charges per invocation. That's a genuine gift for bursty,
event-driven work, and a genuine liability for steady, latency-sensitive, or long-running work.

The question is never "is serverless good" — it's whether your workload's shape matches the
platform's enforced shape. **Match the workload's traffic and duration profile to the platform's
constraints before you match its convenience.**

## 1. Treat statelessness as enforced, not optional

A function instance can be frozen, killed, or never reused between invocations. Anything written
to local disk or held in memory across calls is not guaranteed to survive to the next one. This
is the same principle as `cloud-architecture`'s statelessness default, except here the platform
enforces it for you instead of asking nicely — so design the function so a cold, stateless restart
on every single call would still be correct.

**Done when:** the function produces correct output with zero assumptions about warm-instance
reuse.

## 2. Budget for cold starts explicitly

A cold start pays for provisioning a runtime, loading your code, and initializing dependencies,
and that latency lands on whichever request triggers it. For latency-sensitive paths, this is not
a rounding error — it can be the majority of response time under low or spiky traffic.

- **Keep the deployment package small** — fewer dependencies to load means a faster cold start.
- **Initialize expensive clients outside the handler** so warm invocations skip that cost, but
  never depend on that state being present.
- **Use provisioned/reserved concurrency** for latency-critical functions if the platform offers
  it, and treat that as paying to opt partway out of serverless's cost model.
- **Accept the latency** for background and async paths where nobody's waiting on the response.

**Done when:** the p99 latency of cold-started requests is measured, not assumed to be rare.

## 3. Design around the event, not around a request/response mental model

Serverless functions are triggered by events — a queue message, an object upload, an HTTP call, a
schedule. Treat the event source's delivery guarantees as part of the design: most queues and
buses deliver at-least-once, which means your handler must be idempotent, not just correct on the
first try. A function that isn't safe to run twice on the same event will eventually run twice.

**Done when:** every event handler is idempotent against duplicate delivery.

## 4. Respect concurrency limits as a real ceiling, not a config detail

Every platform caps concurrent executions per function or per account, and that cap can throttle
requests during a traffic spike exactly when you need capacity most. A downstream dependency (a
database connection pool, a rate-limited third-party API) can also be overwhelmed by serverless's
ability to scale out instantly — the function scales faster than what it calls.

**Done when:** concurrency limits on both the function and its downstream dependencies are known
and one does not silently exceed the other.

## 5. Say no when the shape doesn't fit

Serverless fits bursty, event-driven, short-duration work well. It fits poorly when a workload is
steady-state (you're paying per-request for traffic a fixed server would handle cheaper),
long-running (most platforms cap execution duration), or requires persistent connections or
specialized hardware. Forcing a bad fit into serverless usually shows up as cost per request that
quietly exceeds a always-on server, or as timeout errors that get "fixed" by ever-larger memory
allocations. Naming the mismatch early beats discovering it in a bill or an incident.

**Done when:** a workload proposed for serverless has been checked against duration, steadiness,
and connection-persistence requirements, not just "it's an event handler."

## 6. Measure cost per invocation against the alternative

Serverless pricing is per-request-and-duration, which is cheap at low and bursty volume and can
become more expensive than a small always-on instance at sustained high volume. Do this comparison
with real or projected traffic numbers before committing, and revisit it if traffic patterns
shift from bursty to steady. See `cost-optimization` for the ongoing tracking once it's live.

**Done when:** the cost-per-invocation at expected peak traffic has been compared to a
comparable always-on alternative.

## Report

State the event source and its delivery guarantee, the idempotency approach, the measured or
estimated cold-start impact on the critical path, and the concurrency ceiling relative to
downstream dependencies. Name honestly whether this workload's traffic shape actually fits
serverless or was defaulted into it — that mismatch, if present, is the real risk.
