---
name: load-balancing
description: Covers distributing traffic across healthy backends — L4 versus L7 balancing, algorithms, health checks that detect real failure, connection draining during deploys, and the real latency and capacity cost of sticky sessions. Use this whenever the user is choosing a load balancer type, configuring health checks, picking round-robin versus least-connections, debugging uneven traffic distribution, or deciding whether sessions need to be sticky. For routing and auth at the application layer use `api-gateway`, and for balancing across pods inside a cluster use `kubernetes-networking`.
license: MIT
---

# Load Balancing

A load balancer's only job is to keep sending traffic to backends that can actually handle it, and
stop sending it to ones that can't — everything else is a refinement of that. Most load-balancing
incidents are not algorithm problems, they're health-check problems: a backend that's failing gets
traffic anyway because the check never noticed, or a backend that's fine gets pulled because the
check measured the wrong thing.

Correctness here matters more than cleverness. **A load balancer that sends traffic to a dead
backend has failed at its one job, no matter how good the algorithm is.**

## 1. Choose L4 or L7 by what you need to inspect

L4 (transport-layer) balancing routes by IP and port without looking at the request — it's fast,
protocol-agnostic, and can't make routing decisions based on content. L7 (application-layer)
balancing terminates the connection and reads the actual request, so it can route by path or
header, do TLS termination, and retry idempotent requests — at the cost of more compute and being
protocol-specific (usually HTTP).

- **Default to L4** for raw TCP/UDP workloads or when the balancer must stay protocol-agnostic.
- **Use L7** when routing depends on the request itself — path-based routing, header-based
  canaries, or TLS termination all require it.
- **L7 termination breaks true end-to-end TLS** unless it re-encrypts to the backend — know which
  hop actually holds the certificate before assuming traffic is encrypted the whole way.

**Done when:** the balancing layer chosen matches whether routing decisions need request content.

## 2. Make health checks test the thing that actually matters

A health check that only confirms "the process is listening" will happily send traffic to a
backend whose database connection died. The check should exercise a real dependency path — deep
enough to catch actual failure, shallow enough not to become its own bottleneck or cascade a
downstream outage into every backend failing its check simultaneously.

- **Distinguish liveness from readiness**: liveness answers "should this be restarted," readiness
  answers "should this get traffic right now" — a balancer should only ever act on readiness.
- **Set failure and success thresholds deliberately** — too sensitive flaps backends in and out
  under normal jitter; too lax leaves a dead backend serving errors for too long.
- **Avoid checks that call downstream systems the balancer can't see** — a check that fails
  because a shared dependency is degraded can pull every backend at once.

**Done when:** a genuinely unhealthy backend is removed from rotation within one check interval,
and a healthy one is never flapped by check noise.

## 3. Match the algorithm to the actual cost variance between requests

`round-robin` assumes every request costs about the same to serve — true for stateless, uniform
work, false the moment request cost varies widely. `least-connections` accounts for backends
already carrying more in-flight work, which matters when request duration is uneven.
Weighted variants let heterogeneous backend capacity be reflected explicitly instead of assuming
every instance is identical.

| Algorithm | Best fit | Weak point |
|---|---|---|
| Round-robin | Uniform, short requests | Ignores in-flight load |
| Least-connections | Variable request duration | Needs accurate connection counts |
| Weighted (either) | Heterogeneous backend sizes | Weights need upkeep as fleet changes |

**Done when:** the spread between p50 and p99 request duration has been measured, and the chosen
algorithm matches that spread — round-robin only where the spread is narrow.

## 4. Drain connections before a backend disappears

Removing a backend abruptly — scale-down, deploy, or a node being recycled — mid-request forces
in-flight requests to fail. Connection draining marks the backend as not-accepting-new while
letting existing connections finish within a bounded grace period, which is the difference between
a deploy nobody notices and a deploy that spikes error rate every time.

**Done when:** a rolling deploy or scale-down produces zero failed in-flight requests, verified by
watching error rate through the event rather than assuming the config is correct.

## 5. Know what sticky sessions actually cost you

Session affinity (routing the same client to the same backend, usually via cookie or source IP)
solves in-memory session state cheaply, but it defeats even distribution — one hot backend can end
up overloaded while others idle, and draining or losing that backend loses the client's state
entirely unless it's also replicated elsewhere. Prefer externalizing session state so any backend
can serve any request; reach for stickiness only when that's genuinely not feasible.

- **Stickiness concentrates load** on whichever backends happen to hold the busiest sessions.
- **A backend replacement drops sticky sessions** unless state lives outside the process — see
  `caching-strategies` for externalizing that state properly.
- **Cookie-based affinity survives client IP changes**; IP-based affinity breaks behind NAT or
  mobile networks where source IP shifts mid-session.

**Done when:** every route using session affinity names the state that forced it, and per-backend
load is graphed so the distribution cost of that affinity is visible rather than assumed.

## 6. Watch distribution, not just uptime

A balancer can report 100% healthy backends while sending traffic wildly unevenly — a stale
weight, an algorithm interacting badly with connection reuse, or one AZ silently getting starved.
Per-backend request rate and latency, not just aggregate numbers, are what surface this; see
`metrics-and-monitoring` for the RED breakdown to apply per backend.

**Done when:** per-backend traffic share can be graphed and is within expected bounds, not just
inferred from an aggregate health-check pass rate.

## Report

State the balancing layer (L4/L7) and algorithm chosen, what the health check actually exercises,
the drain grace period, and whether sticky sessions are in use and why. Name the honest gap —
usually a health check that's shallower than it should be, or a sticky-session dependency nobody
has scheduled to remove — rather than reporting the setup as fully tuned when only the common path
has been load-tested.
