---
name: cdn
description: Covers caching and serving content at the edge — cache keys and TTL design, invalidation strategies, origin shielding, deciding what is safely cacheable, and moving static and dynamic content closer to users. Use this whenever the user is configuring a CDN, choosing cache-control headers, debugging stale or leaking cached content, setting up cache invalidation after a deploy, or deciding whether a response is safe to cache at all. For application-layer and database caching use `caching-strategies`, and for the origin's own load-balancing behavior use `load-balancing`.
license: MIT
---

# CDN

A CDN's entire value is serving a response without asking the origin, from a location physically
closer to the user. Every problem in CDN configuration traces back to one question asked
carelessly: is this response actually the same for the next request, or did it just look that way
in testing? Get that wrong and you either serve one user's private data to another, or fail to
cache anything and pay full origin cost with extra hops on top.

**A cached response is a promise that this exact bytes-for-bytes answer is correct for anyone who
asks the same question — verify that promise before you make it.**

## 1. Define the cache key as precisely as the response varies

The cache key — usually URL plus a chosen set of headers/cookies/query params — determines what
counts as "the same request." Too narrow a key (ignoring a header the response actually varies by,
like `Accept-Language` or an auth cookie) causes one user's personalized or region-specific
response to be served to everyone else. Too broad a key (including a header that doesn't affect
the response, like a random request ID) destroys the cache hit rate by fragmenting it into
singletons.

- **Include every header or param the response body actually varies on** — check server-side
  `Vary` behavior, don't assume.
- **Exclude anything that's unique per request but doesn't change the response** — tracking IDs,
  timestamps in query strings, cache-busting params added out of habit.
- **A cache key that's too narrow is a security bug**, not just a correctness bug, if it leaks
  personalized content across users.

**Done when:** two requests that produce the same key always produce the same correct response for
either requester.

## 2. Set TTL by how wrong a stale answer is allowed to be

Static assets with content-hashed filenames can cache essentially forever, because a new version
gets a new URL — the old cached copy is never wrong, just superseded. Anything without that
property needs a TTL chosen by asking how long a stale answer is tolerable: a product price is not
the same tolerance as a blog post body.

```
Cache-Control: public, max-age=31536000, immutable   # hashed filename, cache forever
Cache-Control: public, max-age=60, stale-while-revalidate=30   # changes often, needs freshness
```

**Done when:** every cacheable response's TTL is recorded with the staleness window it implies, and
no route is serving the platform's default TTL unrecorded.

## 3. Invalidate deliberately, not by dropping the whole cache

Purging an entire cache on every deploy forces every request to hit the origin at once — a
self-inflicted thundering herd right when the origin just changed and is least proven stable.
Targeted invalidation (by URL, by tag, or by relying on content-hashed filenames so nothing needs
purging at all) keeps the cache warm for everything unaffected by the deploy.

- **Content-hashed filenames need no invalidation** — the URL itself changes, making this the most
  reliable pattern available.
- **Tag- or path-based purges** should be scoped to exactly what changed, not the whole zone, as
  a habit.
- **A full purge is an emergency tool**, not a routine deploy step — reach for it only when
  something incorrect was cached and must be gone immediately.

**Done when:** a routine deploy invalidates only the URLs it actually changed.

## 4. Use origin shielding to protect the origin from cache-miss storms

Without a shield, every edge location that misses the cache goes straight to the origin
independently — a cold cache after a purge or a new region rollout can multiply origin load by the
number of edge locations. An origin shield (a single designated caching layer between edges and
origin) collapses those redundant misses into one request per unique resource, and is the
difference between a cache miss being routine and being an incident.

**Done when:** a simultaneous cold-cache event across edge locations produces roughly one origin
request per resource, not one per edge location.

## 5. Know what's safe to cache before you cache it

Caching a response that contains per-user data, an auth token, or a request that mutates state
(most non-`GET` methods) is a data-leak or correctness bug waiting to happen, not just a
performance question. Default to not caching anything that isn't explicitly verified safe, rather
than caching by default and discovering the exception in production.

- **Never cache authenticated or personalized responses** unless the cache key genuinely captures
  every dimension of that personalization.
- **Never cache mutating methods** (`POST`/`PUT`/`DELETE`) — caching is for idempotent reads.
- **Treat `Set-Cookie` in a cached response as a red flag** — it usually means the response was
  meant for one specific client, not the cache in general.

**Done when:** every cached response has been explicitly confirmed identical for any requester who
would produce the same cache key.

## Report

State the cache-key definition, TTL policy per content class, invalidation strategy used on
deploys, and whether origin shielding is in place. Name the honest gap — usually a response class
that's cached more broadly than it should be, or an invalidation step still done as a full purge
out of caution — rather than reporting the edge layer as fully tuned when only the common path has
been verified.
