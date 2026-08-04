---
name: caching-strategies
description: Covers caching correctly — deciding what is worth caching, choosing between cache-aside, write-through, and write-behind, setting TTLs from real staleness tolerance, invalidating on write instead of hoping a TTL catches it, and preventing thundering-herd stampedes on expiry. Use this whenever the user adds a cache layer, picks a TTL, debugs stale reads, sees a load spike on the database right after a cache miss, or asks whether something should be cached at all. For the database load a cache protects use `database-operations`, and for proving a cache is actually paying off use `load-testing`.
license: MIT
---

# Caching Strategies

Caching is one of the few changes that can make a system both faster and more fragile in the
same commit. It is easy to add and easy to get subtly wrong, and the failure mode is rarely a
crash — it is a user seeing data that is quietly, plausibly wrong, which is far harder to
notice and debug than an error.

The decision to cache something is really two decisions: is this worth the complexity, and am
I willing to accept the staleness this introduces. Skipping the second question is how caches
turn into a source of bugs instead of a source of speed.

**A cache without an explicit invalidation and staleness story is not an optimization — it is
a bet that nobody will notice when the data is wrong.**

## 1. Cache what is expensive and read-heavy, not everything

Every cached value is a second copy of the truth that can drift from the source, so caching
should be reserved for data where the read cost or read frequency actually justifies that
risk.

- **Cache results that are expensive to compute or fetch** — aggregations, joins across
  services, external API calls — not simple key lookups that are already fast.
- **Cache data that is read far more often than it changes.** A value read a thousand times
  between writes is a good candidate; a value read once per write gains little from caching.
- **Skip caching data with strict consistency requirements**, like account balances or
  inventory counts at checkout, unless the invalidation story is airtight.

**Done when:** each cached value has a stated reason — read frequency, compute cost, or
upstream latency — that justifies the staleness risk it introduces.

## 2. Pick the pattern that matches your consistency needs

The three common caching patterns trade off differently between read speed, write speed, and
staleness risk, and picking the wrong one for the workload is a common source of both bugs and
wasted engineering effort.

| Pattern | Reads | Writes | Risk |
|---|---|---|---|
| Cache-aside | App checks cache, falls back to source, populates cache | Simple, cache invalidated on write | Cache can go stale if invalidation is missed |
| Write-through | Always served from cache | Written to cache and source together, in sync | Write latency increases; cache always fresh |
| Write-behind | Always served from cache | Written to cache immediately, source asynchronously | Fast writes; risk of data loss if cache fails before flush |

Cache-aside is the right default for most systems — it is the simplest to reason about and
fails safe by falling back to the source. Write-through and write-behind earn their added
complexity only when write latency or write volume genuinely demands it.

**Done when:** the chosen pattern is named explicitly and its tradeoff is understood, not
inherited by default from whatever library example was copied.

## 3. Set TTLs from staleness tolerance, not convenience

A TTL is a promise about how stale data is allowed to get, and that promise should come from
how the data is used, not from a round number that felt reasonable.

- **Ask how long stale data can go unnoticed or unharmful** for this specific value, and set
  the TTL at or below that — a product price tolerates minutes of staleness; a live inventory
  count during a flash sale may tolerate none.
- **Shorter TTLs increase load on the source** as cache misses become more frequent; longer
  TTLs increase the blast radius of any data that is wrong. Neither direction is free.
- **Vary TTLs by data type** rather than using one global default across the whole cache —
  different values have genuinely different staleness budgets.

**Done when:** every TTL can be justified by a stated staleness tolerance for that specific
piece of data.

## 4. Invalidate on write, do not rely on TTL alone

A TTL bounds how long staleness can last, but it does not prevent staleness the moment a write
happens — a cache that only expires on a timer will serve wrong data for the full TTL window
after every update, which is often the exact moment users are looking.

- **Invalidate or update the cache entry as part of the same write path** that changes the
  source of truth, rather than leaving it to expire naturally.
- **Version or namespace cache keys by the underlying data's version** where invalidation
  across many keys is hard, so a bulk change can be reflected by bumping one version key.
- **Treat TTL as a safety net for missed invalidations**, not as the primary invalidation
  mechanism — if it is doing all the work, staleness windows are longer than intended.

**Done when:** a write to the source of truth results in the cache reflecting the new value
before the TTL would have expired it naturally.

## 5. Prevent stampedes with jitter and locks

When a popular key expires, every concurrent request that misses the cache at that instant can
hit the source simultaneously — a thundering herd that can take down the exact system the
cache was protecting.

- **Add jitter to TTLs** so a batch of keys set at the same time do not all expire in the same
  instant and trigger a synchronized stampede.
- **Use a lock or single-flight pattern on cache miss**, so only one request repopulates a
  given key while others wait for that result instead of all recomputing it.
- **Consider serving stale data briefly while refreshing in the background** for high-traffic
  keys, trading a moment of staleness for protecting the source entirely.

**Done when:** a cache miss on a high-traffic key results in one source request, not one per
concurrent caller.

## 6. Accept staleness deliberately and say so

Every cache introduces some staleness window, and pretending otherwise just delays the moment
someone discovers it the hard way. The honest move is to state the staleness bound up front so
it is a known tradeoff, not a surprise bug report.

- **Document the maximum staleness a cached value can exhibit**, derived from its TTL and
  invalidation path, somewhere consumers of that data can find it.
- **Flag data paths where staleness is not acceptable** and route those to the source directly
  rather than forcing a cache-consistency solution onto a value that cannot tolerate it.

**Done when:** the maximum staleness window for each cached value is written down somewhere
visible to whoever consumes that data.

## Report

State what is cached and why, the pattern used (cache-aside, write-through, write-behind), the
TTL and its staleness justification for each value, and whether stampede protection exists on
high-traffic keys. Name the honest gap — usually a cache with no explicit invalidation on
write, relying entirely on TTL expiry — rather than presenting the cache as fully consistent.
