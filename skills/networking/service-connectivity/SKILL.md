---
name: service-connectivity
description: Covers making service-to-service connections reliable and secure — service discovery, mutual TLS, timeouts and retries with circuit breakers, backpressure under load, and secure links across hybrid or multi-cloud boundaries. Use this whenever the user is setting retry or timeout policy, adding mTLS between services, debugging cascading failures from a slow dependency, connecting services across VPCs or clouds, or seeing an upstream overwhelmed by a retry storm. For the north-south API front door use `api-gateway`, and for a mesh implementing these patterns declaratively use `service-mesh`.
license: MIT
---

# Service Connectivity

Every call one service makes to another is a bet that the other side is up, fast, and honest about
its identity. Distributed systems fail at the seams between services far more often than inside
any single one — a slow dependency without a timeout, a retry storm without backoff, or a
connection that was never actually authenticated all turn a local problem into a cascading one.

Design connectivity assuming the other side will eventually be slow, wrong, or absent — because
over enough time, it will be. **A call without a timeout is a promise to wait forever, and nothing
downstream should ever make that promise.**

## 1. Make service discovery answer "is this instance actually healthy," not just "does it exist"

Discovery mechanisms (DNS-based, a registry, or a mesh control plane) that only track which
instances exist — without incorporating readiness — will happily hand out an address for an
instance that's up but not ready to serve. Discovery and health need to be the same signal, or a
caller ends up needing its own separate health check on top, which most callers skip.

- **Prefer discovery that's health-aware by construction** (e.g., a mesh or orchestrator that
  removes not-ready instances from the result set) over a static list plus a hope.
- **In Kubernetes, this is exactly the Service/Endpoints readiness relationship** — see
  `kubernetes-networking` for that mechanism specifically.

**Done when:** a caller resolving a dependency only ever gets instances that are actually ready to
serve.

## 2. Set timeouts before retries, and retries before circuit breakers

These three exist in a dependency order: a timeout bounds how long one call can hang, a retry
policy decides what to do about the failures a timeout produces, and a circuit breaker stops
retrying a dependency that's clearly down instead of hammering it. Configuring retries without a
timeout, or a circuit breaker without sane retries underneath, just moves the failure mode instead
of fixing it.

```yaml
timeout: 2s              # bound a single call
retry:
  attempts: 2
  backoff: exponential    # avoid synchronized retry storms
  retry_on: [5xx, connect-timeout]   # never retry non-idempotent writes blindly
circuit_breaker:
  error_threshold: 50%
  break_duration: 30s
```

- **Every outbound call needs an explicit timeout** shorter than whatever timeout the caller's own
  caller is using, so failures unwind in order instead of stacking up.
- **Only retry idempotent operations** by default — retrying a non-idempotent write is a
  correctness bug disguised as resilience.
- **A circuit breaker's job is to protect the downstream**, not to make the upstream succeed —
  it should fail fast once open, not queue and hope.

**Done when:** a dependency that goes fully down causes callers to fail fast within one timeout
window, not to pile up waiting or retrying indefinitely.

## 3. Design for backpressure instead of unbounded queuing

When a downstream slows down, an upstream that keeps accepting work at the same rate just builds an
unbounded queue until it runs out of memory or the queue's own latency becomes the real outage.
Backpressure — bounded queues, load shedding, or explicitly signaling "slow down" back to the
caller — turns an overload into a controlled degradation instead of a collapse.

- **Bound every queue** between services; an unbounded queue is a memory leak with a delay on it.
- **Shed load deliberately** (reject the least valuable work first) rather than letting the
  system degrade unpredictably under pressure.
- **A slow downstream should propagate backpressure upstream**, not get silently buffered away
  until the buffer itself becomes the problem.

**Done when:** a downstream slowdown produces a bounded, observable increase in rejected or shed
requests instead of unbounded memory growth.

## 4. Authenticate the connection, not just the request

mTLS gives both sides cryptographic proof of identity at the connection level, independent of
whatever the application-layer payload claims. This matters most for internal traffic that's often
assumed trusted by default — the zero-trust position is that network location proves nothing, and
every hop should verify identity explicitly rather than relying on being inside a perimeter. See
`zero-trust` for the broader posture this is one implementation of.

**Done when:** service-to-service traffic is authenticated by certificate, not by network location
alone, and certificate rotation is automated rather than a manual chore someone forgets.

## 5. Treat hybrid and cross-cloud links as the least reliable path in the system

A link between a datacenter and a cloud VPC, or between two cloud providers, has different latency,
failure modes, and cost characteristics than intra-cloud traffic — and it's usually the path with
the least observability, since it crosses an administrative boundary. Apply every pattern above
more conservatively here: tighter timeouts are wrong (the link is slower), but stronger circuit
breaking and explicit monitoring of the link itself are right.

**Done when:** the cross-boundary link has its own dedicated health signal, separate from the
health of either side's internal services — see `multi-cloud` for the broader architecture this
feeds into.

## Report

State the timeout, retry, and circuit-breaker settings per major dependency, whether mTLS is
enforced or optional, and how backpressure is implemented under load. Name the honest gap — usually
a dependency still missing an explicit timeout, or a hybrid link with no dedicated health check —
rather than claiming full resilience when only the most obvious call paths have been hardened.
