---
name: scalability-design
description: Designs systems to handle the next order of magnitude of load by removing state, shared contention, and single bottlenecks, and by choosing deliberately between horizontal and vertical scaling for each component. Use this whenever the user is designing a new service for growth, asks whether an architecture will handle 10x traffic, is deciding between scaling out and scaling up, or hits a wall where adding more instances stops helping. For proving the design holds under real traffic use `load-testing`, and for provisioning the headroom over time use `capacity-planning`.
license: MIT
---

# Scalability Design

Scaling problems are rarely solved by adding more of what you already have — they're solved by
removing whatever forces every request through the same place. A stateless web tier scales by
adding boxes; a single Postgres primary handling every write doesn't, no matter how many app
servers point at it. The architecture decides which resource has to grow linearly with load and
which one hits a wall first.

Design decides the ceiling long before anyone hits it. The question worth asking early is not
"can we add more servers" but "what breaks first, and does adding more servers even help it."

**Scale the thing that's actually the bottleneck — everything else is decoration.**

## 1. Make the request path stateless wherever possible

A stateless component can be replicated freely because any instance can serve any request; a
stateful one can't, because the request has to find the instance holding its state. Pushing
session state, in-memory caches, and local files out of the application tier — into a shared
store or the client — is what makes horizontal scaling actually work instead of just adding boxes
that can't share the load.

- **Externalize session and user state** to a shared cache or database, not local memory or disk,
  so any instance can serve any request.
- **Avoid sticky routing as the default fix** — it papers over statefulness instead of removing
  it, and it reintroduces a single point of failure per session.
- **Treat local disk as ephemeral** — anything written locally disappears when the instance is
  replaced; see `stateful-workloads` for components that must genuinely hold state.

**Done when:** any request can be served by any instance of the stateless tier, verified by
killing an instance mid-traffic without a user-visible failure.

## 2. Choose horizontal or vertical scaling per component, deliberately

Horizontal scaling — adding more instances — is usually cheaper, more resilient to a single
failure, and has no hard ceiling. Vertical scaling — bigger instances — is simpler and sometimes
unavoidable for components that can't be split, like a single-writer database. Applying one
strategy everywhere by default, instead of choosing per component, wastes either engineering
effort or money.

| Component type | Usual right answer | Why |
|---|---|---|
| Stateless app tier | Horizontal | No shared state to serialize around |
| Single-writer database | Vertical, then partition | Writes serialize through one node |
| Cache layer | Horizontal, sharded | Scales with data size and read volume |

- **Default to horizontal for anything stateless** — it degrades more gracefully and has no
  single-box ceiling.
- **Accept vertical scaling as a bridge, not a strategy** — it buys time before the harder work of
  partitioning or offloading.
- **Know each component's ceiling before you need it** — a database's vertical limit should be a
  known number, not a surprise at the outage.

**Done when:** every major component has a stated scaling strategy and the reason it was chosen,
not a default applied uniformly.

## 3. Find and remove the bottleneck that doesn't scale with the rest

Every architecture has a component that scales linearly and one that doesn't — a shared lock, a
single message queue partition, a rate-limited third-party API, a database sequence. Adding
capacity everywhere except that one component just moves the queue in front of it; the system's
real capacity is the bottleneck's capacity, full stop.

- **Look for anything shared across all requests** — a single lock, counter, or connection pool
  is a serialization point no amount of horizontal scaling elsewhere fixes.
- **Partition or shard what can't otherwise scale** — splitting a database by key range or tenant
  turns one bottleneck into many independently-scalable ones.
- **Confirm the bottleneck empirically**, via `profiling` and `load-testing`, rather than
  guessing which component is the constraint.

**Done when:** the component that would be the first to saturate at 10x current load has been
identified and either scales independently or has a stated remediation plan.

## 4. Decouple components so failure and load don't propagate

A synchronous call chain means every downstream slowdown becomes an upstream slowdown, and every
downstream outage becomes an upstream outage. Introducing a queue, an async boundary, or a cache
between components lets each one scale and fail independently, instead of the whole chain moving
at the speed of its slowest link.

- **Put a queue between producer and consumer** where the two don't need to scale together — it
  absorbs bursts instead of propagating them upstream.
- **Set timeouts and circuit breakers on every synchronous call** — an unbounded call to a slow
  dependency turns their saturation into yours.
- **Cache aggressively at read-heavy boundaries** — see `caching-strategies` for what's safe to
  cache and for how long.

**Done when:** a slowdown in one component, injected deliberately, does not cause cascading
failure in components that don't directly depend on its capacity.

## 5. Design for the failure of any single instance, not just its slowness

At scale, instance failure isn't an edge case — with enough instances running long enough, one is
always failing. A design that assumes every instance stays up will fail unpredictably at scale
even if it works fine in a three-node test. Redundancy and graceful degradation have to be
designed in, not patched on after the first outage.

- **Run enough replicas that losing one doesn't lose capacity**, not just enough for redundancy
  on paper.
- **Design degraded modes explicitly** — what serves when a dependency is down — rather than
  discovering the failure mode live.
- **Validate the assumption with `load-testing`, especially under an injected instance failure**
  — a design that's never seen a failure under load is unverified.

**Done when:** the design has an explicit answer for what happens when any single instance or
dependency fails under full load, not just when it's healthy.

## Report

State which components are stateless and horizontally scaled, which are vertically scaled and
why, and which single component was identified as the bottleneck at the next order of magnitude.
Name honestly which part of the design has not been validated under real load or failure
injection — an architecture diagram that looks scalable but has never been tested under a
component failure is still a guess.
