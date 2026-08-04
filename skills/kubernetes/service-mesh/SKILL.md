---
name: service-mesh
description: Covers when and how to adopt a service mesh — mTLS between services, traffic shifting, retries/timeouts enforced at the mesh layer, near-free observability, and the real latency and complexity cost of running one. Use this whenever the user asks whether they need a service mesh, is configuring mTLS or traffic-splitting rules, or is debugging sidecar-added latency. For basic Service/Ingress routing use `kubernetes-networking`; for canary rollout mechanics use `progressive-delivery`.
license: MIT
---

# Service Mesh

A service mesh moves cross-cutting network concerns — mTLS, retries, timeouts, traffic splitting,
request-level observability — out of application code and into a shared sidecar proxy layer. That's
a genuine architectural win once you have enough services that reimplementing retry logic in five
languages is more expensive than running a mesh. It is also real infrastructure with its own
control plane, its own failure modes, and a latency cost on every single request.

The mesh is worth it when the alternative is duplicating the same networking logic across many
services; it's not worth it just because it's available. **Adopt a mesh to solve a problem you
already have, not one you're anticipating.**

## 1. Justify the mesh against what NetworkPolicy and Ingress already give you

Plain Kubernetes already provides L3/L4 segmentation (NetworkPolicy) and L7 HTTP routing at the edge
(Ingress). A mesh's value is specifically service-to-service L7: per-request retries, mTLS between
every pod pair without app changes, and fine-grained traffic splitting for internal calls — if the
actual need is "block namespace A from reaching namespace B," that's `kubernetes-networking`, not a
mesh-sized solution.

- **Small service counts (a handful of services)** rarely justify the operational overhead — the
  same retry/timeout logic in a shared library is often less total complexity.
- **Real triggers for a mesh**: many services in multiple languages needing consistent
  retry/timeout/circuit-breaking behavior, a compliance requirement for mTLS everywhere, or
  fine-grained internal traffic shifting for progressive delivery.
- **Write down the specific problem** the mesh is meant to solve before adopting one — "observability"
  alone is rarely enough justification since most of it is achievable via `distributed-tracing` and
  `metrics-and-monitoring` without a mesh.

**Done when:** the decision to adopt (or not adopt) a mesh is backed by a named problem it solves
that the existing stack can't.

## 2. Get mTLS to strict mode deliberately, not accidentally

Most meshes support permissive mode (accepts both mTLS and plaintext) as a migration state and
strict mode (mTLS only) as the end state. Leaving a mesh in permissive mode indefinitely means
you've paid the operational cost of the mesh without getting its main security guarantee — any pod
that never got the sidecar injected can still talk to everything in plaintext.

- **Roll out namespace by namespace**, permissive first to confirm nothing breaks, then flip to
  strict — flipping cluster-wide to strict at once will break any service that doesn't yet have a
  sidecar.
- **Sidecar injection must be enforced**, not optional — a namespace that allows non-injected pods
  undermines strict mTLS for everything that talks to them.
- **Certificate rotation is the mesh control plane's job** — verify it's actually happening
  automatically, not just configured; an expired root cert takes down every mTLS connection in the
  mesh simultaneously.

**Done when:** every namespace in scope is in strict mTLS mode and no pod skips sidecar injection
without a documented exception.

## 3. Do traffic shifting at the mesh only when app-level isn't enough

Weighted routing and header-based traffic splitting at the mesh layer let you shift traffic between
versions without redeploying — genuinely useful for canaries and A/B testing across many services.
But if the need is a single service's canary rollout, an Ingress controller or the deployment
tooling itself (Argo Rollouts, Flagger) may already do this without mesh-wide sidecar overhead.

- **Mesh-level shifting shines** when splitting needs to be consistent across a call chain (multiple
  services all routing the same user to the same version), which single-service tools can't
  coordinate.
- **The actual canary analysis and promotion decision** — what metric gates promotion, how fast to
  ramp — is `progressive-delivery`'s concern; the mesh is just the traffic-splitting mechanism.

**Done when:** you can state why traffic shifting needed mesh-wide coordination rather than a
single ingress or deployment-tool feature.

## 4. Set retries and timeouts at exactly one layer

Retries configured both in application code and at the mesh sidecar compound — a 3x app-level retry
wrapped by a 3x mesh-level retry is 9 attempts, which can turn a struggling downstream service into
a fully overwhelmed one during an incident. Pick one layer to own retry/timeout policy per call
path and remove it from the other.

```yaml
# mesh-level retry policy (e.g. Istio VirtualService) — remove equivalent app-level retry logic
retries:
  attempts: 3
  perTryTimeout: 2s
  retryOn: 5xx,reset,connect-failure
```

**Done when:** for any given call path, retries and timeouts are configured at exactly one layer,
verified by checking both the app code and the mesh config.

## 5. Budget for the latency and resource cost of every sidecar

Every request now passes through two additional proxy hops (client sidecar, server sidecar), which
adds real tail latency and doubles the container count (and often memory/CPU overhead) per pod. For
latency-sensitive services this is not free, and it's the most common reason a mesh adoption gets
partially rolled back.

- **Measure p99 latency before and after** injection on a real workload, not a synthetic one —
  sidecar overhead varies by mesh implementation and payload size.
- **Budget sidecar CPU/memory into every pod's requests** — an uninstrumented sidecar cost is a
  common cause of nodes running hotter than capacity planning assumed.

**Done when:** the measured p99 latency and resource overhead of sidecar injection is known and
was an accepted tradeoff, not a surprise discovered in production.

## Report

State the specific problem the mesh was adopted to solve, the mTLS mode per namespace, where
retries/timeouts are owned, and the measured latency/resource overhead of sidecar injection. Call
out any namespace still in permissive mTLS or any service with duplicated retry logic — naming that
half-migrated state is more useful than declaring the mesh fully adopted.
