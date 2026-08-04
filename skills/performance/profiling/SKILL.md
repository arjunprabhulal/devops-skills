---
name: profiling
description: Finds where time, memory, and IO actually go inside a running system, using CPU and memory profilers, flame graphs, and the right choice between sampling and instrumentation, so optimization targets the real hot path instead of intuition. Use this whenever the user asks what's slow inside a specific process, wants to read or generate a flame graph, suspects a memory leak, or is about to optimize code without evidence of where the time goes. For deciding what to change once the hot path is known use `performance-tuning`, and for generating load to profile under use `load-testing`.
license: MIT
---

# Profiling

Every engineer has a theory about what's slow, and most of those theories are wrong, because
intuition is trained on code structure, not on runtime behavior. The function that looks
expensive because it's long is rarely the one burning the CPU; the one that looks trivial because
it's three lines and called in a tight loop usually is. Profiling replaces the theory with a
measurement of where the program actually spends its time and memory.

The discipline is to follow the data even when it points somewhere surprising, and to stop
tuning the moment the numbers agree with what you already believed if you never actually looked.

**Don't optimize what you assume is slow — profile, then optimize what the data says is slow.**

## 1. Choose sampling or instrumentation on purpose, not by default

Sampling profilers interrupt the program periodically and record the call stack, giving low
overhead and a statistical picture. Instrumentation profilers insert timing code around every
function call, giving exact counts and timings but at a real cost that can itself distort the
result. Picking the wrong one either misses short-lived hot spots or perturbs production traffic.

- **Use sampling in or near production** — the overhead is low enough to leave running, and
  statistical accuracy is enough to find the hot path.
- **Use instrumentation for precise call counts**, in a controlled environment — it answers "how
  many times" and "exactly how long," which sampling can only estimate.
- **Never trust instrumentation numbers from a heavily instrumented run** for tuning production
  latency — the overhead itself can dominate the measurement.

**Done when:** the profiling method is chosen deliberately for the question being asked, and its
overhead is accounted for in reading the result.

## 2. Read the flame graph for width, not height

A flame graph stacks call frames vertically by depth and sizes them horizontally by time spent.
The instinct is to stare at the tallest stack because it looks most complex; the frame that
matters is the widest one, because width is where the CPU actually spent its time, regardless of
how deep the call chain got there.

- **Scan for the widest frames first**, then read down to see what code they belong to — depth is
  call structure, width is cost.
- **Look for repeated identical stacks** — the same wide frame appearing under many different
  parents often means one shared function or query is the real bottleneck.
- **Distinguish "on-CPU" from "off-CPU" time** — a flame graph of CPU samples won't show time
  spent blocked on IO or locks; that needs a separate off-CPU or wall-clock profile.

**Done when:** the widest frame in the flame graph has been identified and traced to a specific
function or query, not just eyeballed.

## 3. Profile memory and IO, not only CPU

A system can be CPU-idle and still be slow because it's waiting on disk, a lock, or garbage
collection triggered by allocation pressure. CPU profiling alone is blind to all three. Memory
profiling shows what's allocating and what's being retained; IO profiling shows what's actually
waiting on disk or network rather than computing.

- **Profile allocations, not just live heap size** — a high allocation rate causes GC pressure
  even if nothing leaks, and shows up as CPU time spent collecting, not in the allocating code.
- **Distinguish a leak from a plateau** — heap that grows and never stabilizes under steady load
  is a leak; heap that grows to a ceiling and holds is just a larger working set.
- **Trace IO wait separately from CPU busy time** — a slow endpoint with low CPU usage is almost
  always blocked on IO or a lock, and a CPU profile alone will show nothing useful.

**Done when:** memory allocation behavior and IO wait time have both been checked, not just CPU
samples.

## 4. Profile under conditions that resemble production

A profile taken against an empty local database, with no concurrent requests, measures a
different program than the one running in production — index scans, lock contention, and cache
misses only appear at realistic data volume and concurrency. Combine profiling with
`load-testing` to get a profile that reflects the real hot path.

- **Use production-scale data**, not a seeded dev dataset — query plans change with cardinality.
- **Profile under concurrent load**, not a single request — contention and queueing don't exist
  in isolation.
- **Prefer profiling live production with low-overhead sampling** over an unrepresentative
  staging environment, when the tooling allows it safely.

**Done when:** the profile was captured under data volume and concurrency that resembles
production, or the gap from production is explicitly noted.

## 5. Confirm the fix with a second profile, not a feeling

Fixing what the first profile showed doesn't guarantee it was the whole problem — a second
bottleneck may have been hiding behind the first, or the change may not have touched the code
path that actually ran. Re-profile after the change to confirm the hot frame shrank and see
what's now the widest frame instead.

- **Compare before and after flame graphs directly**, not just an overall latency number — the
  latency number can improve for the wrong reason.
- **Expect a new hot spot to appear** — fixing the biggest bottleneck routinely promotes the
  second-biggest into view; that's progress, not failure.
- **Hand the confirmed win to `performance-tuning`** to record the change and its measured delta
  against the baseline.

**Done when:** a post-change profile confirms the previous hot frame shrank and identifies
whatever is now the largest remaining contributor.

## Report

State the profiling method used and why, the widest frame or largest allocation source found and
the function or query it traced to, and whether memory and IO were checked alongside CPU. Name
honestly which conditions weren't production-representative — data volume, concurrency, or
overhead from instrumentation — since a profile taken under the wrong conditions can point
confidently at the wrong bottleneck.
