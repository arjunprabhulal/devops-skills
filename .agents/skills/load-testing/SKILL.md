---
name: load-testing
description: Tests a system under realistic traffic shapes to find its breaking point before users do — modeling real request mixes and ramp patterns, measuring latency percentiles and error rate together, and exercising the whole system instead of one endpoint in isolation. Use this whenever the user wants to know how much traffic a system can handle, is preparing for a launch or seasonal peak, or is about to ship a change that affects throughput. For diagnosing why an endpoint is slow use `profiling`, and for sizing headroom from results use `capacity-planning`.
license: MIT
---

# Load Testing

A load test that hammers a single endpoint with identical requests until it falls over answers a
question nobody asked. Production traffic is a mix — read-heavy here, write-heavy there, some
users idle, some hammering the API — and the interactions between those flows are exactly what
break systems that look fine in isolation. A load test that doesn't resemble real traffic
validates nothing real.

The goal is not to prove the system survives; it's to find the load level and failure mode where
it doesn't, on purpose, before a real spike does it for you.

**A load test that never fails the system hasn't found its limit — it's found its patience.**

## 1. Model the traffic shape, not just the volume

Total requests per second is the least interesting number in a load test. What matters is the
mix of operations, their relative frequency, and the pattern of arrival — bursty versus steady,
diurnal versus flat. A test that sends uniform traffic when real traffic bursts at the top of
every minute will miss the exact failure that burst causes.

- **Derive the mix from real traffic logs**, not intuition — the read:write ratio and endpoint
  frequency should come from production, not a guess.
- **Include realistic user behavior**, not just raw requests — think time between actions, session
  length, and abandoned flows all change how connections and caches behave.
- **Reproduce bursts, not just averages** — a flat ramp to the same average RPS as a real burst
  can hide the exact contention the burst causes.

**Done when:** the test's operation mix and arrival pattern are derived from real traffic data,
not assumed.

## 2. Ramp up to find the breaking point, don't just hit a target and stop

Testing at a single fixed load only tells you pass or fail at that one point. Ramping load up in
steps — while holding each step long enough to reach steady state — reveals exactly where
behavior changes: where latency starts climbing, where errors appear, where throughput stops
increasing with more load. That knee in the curve is the number worth knowing.

- **Hold each load step long enough to stabilize** — connection pools, caches, and autoscalers
  all take time to settle; a too-short step measures the ramp, not the load.
- **Keep ramping past the first sign of trouble** — stopping at the first error hides whether the
  system degrades gracefully or falls off a cliff.
- **Record the load level of the knee**, not just the final failure — that's the actionable
  capacity number, distinct from the point of total collapse.

**Done when:** the test reports the load level where throughput stops scaling and the load level
where the system fails, as two distinct numbers.

## 3. Report percentiles and errors together, never throughput alone

A system can hit its target requests-per-second while p99 latency triples and a slice of requests
silently error — a throughput-only report would call that a pass. Latency distribution and error
rate are the two signals that tell you whether users are actually having a bad time.

| Signal | Why it matters more than the average |
|---|---|
| p50 / p95 / p99 latency | Averages hide the tail that real users hit |
| Error rate by type | Timeouts and 5xxs mean failure even if RPS holds |
| Throughput vs. load | Flattening throughput under rising load is the real ceiling |

- **Report percentiles, never the mean alone** — the mean is dominated by the fast common case
  and hides the slow tail.
- **Break errors down by type** — a rising timeout rate signals saturation; a rising 4xx rate
  might just mean the test data ran out.
- **Correlate the latency knee with a resource signal** — connect it back to `performance-tuning`
  by checking what saturated at that load level.

**Done when:** the report includes p50/p95/p99 latency and error rate by type at every load step,
not just an average.

## 4. Test the whole system, including its dependencies

Load-testing a service behind a mock of its database or downstream APIs measures an idealized
system that doesn't exist in production. Real load exposes real contention — connection pool
limits, downstream rate limits, shared cache eviction — that only show up when the dependencies
are real or realistically simulated.

- **Point the test at a production-like environment**, with real datastore sizes and index
  cardinality — an empty test database has no query plan surprises.
- **Include downstream services in scope**, or explicitly simulate their real latency and error
  rate — a mocked-out dependency hides where the actual limit lives.
- **Watch shared infrastructure**, not just the service under test — a load test can starve other
  tenants of a shared database or queue.

**Done when:** the test exercises real or realistically-simulated dependencies, not mocks that
return instantly.

## 5. Automate the test so it runs before every risky change

A load test run once before launch and never again is a snapshot of a system that no longer
exists by the time the next release ships. Wiring load tests into the pipeline — even a smaller,
faster version — catches regressions before they reach production instead of during the next
incident.

- **Keep a fast smoke-scale version in CI**, and reserve the full-scale ramp test for pre-release
  or scheduled runs — see `ci-pipelines` for wiring it in.
- **Fail the pipeline on a percentile or error-rate regression**, not just a hard crash — silent
  latency creep is a regression too.
- **Re-run the full test whenever the traffic model changes**, not just when code changes — a new
  feature can shift the mix even if performance code didn't move.

**Done when:** a load test runs on a repeatable schedule or trigger, and a percentile regression
fails it automatically.

## Report

State the traffic model used and its source, the load level at the throughput knee and the load
level at failure, and the percentile latency and error rate observed at each. Name honestly which
dependencies were mocked instead of real, and which traffic patterns weren't modeled — an
untested traffic shape is exactly the one that will show up in the next real spike.
