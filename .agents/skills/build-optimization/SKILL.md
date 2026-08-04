---
name: build-optimization
description: Makes builds fast and reproducible through incremental and hermetic builds, remote or shared caching, dependency caching, and parallelism, without trading correctness for speed. Use this whenever the user complains builds are slow, asks about build caching or cache keys, wants to cut cold-build time, is setting up a remote build cache, or is debugging a build that's fast but wrong. For caching inside a CI workflow use `ci-pipelines`; for shrinking the resulting image use `image-optimization`.
license: MIT
---

# Build Optimization

Build speed and build correctness pull in the same direction far more often than people assume —
a hermetic, well-cached build is both faster and more trustworthy than one that "works on my
machine" via ambient state. The failure mode to design against isn't a slow build, it's a fast
build that's fast because it's silently reusing something stale. Optimize in the order that
preserves correctness first: eliminate unnecessary work, then cache what's safe to cache, then
parallelize what's left.

A build that's fast and wrong costs more than a build that's slow and right, because the wrong
one ships.

**Speed up builds by doing less work and reusing verified work — never by skipping
verification.**

## 1. Make builds hermetic before you make them fast

A hermetic build depends only on declared inputs — no ambient environment variables, no network
calls to unpinned resources, no reliance on whatever happens to be installed on the machine.
Hermeticity is what makes caching and remote/distributed builds *safe*: if a build can produce
different output on two machines with the same declared inputs, no caching strategy built on top
of it is trustworthy, because you can't tell a legitimate cache hit from a stale one hiding a
real difference.

- **Declare every input explicitly** — dependency versions, compiler flags, environment variables
  the build reads.
- **No network access during the build step itself** beyond fetching declared, pinned
  dependencies.
- **Same inputs, same machine class, same output** — verify this before trusting any cache built
  on top.

**Done when:** the same commit, built on two different machines, produces byte-identical (or
content-hash-identical) output.

## 2. Build incrementally: only rebuild what changed

Full rebuilds on every change are the default in most naive setups and the single biggest source
of wasted build time. Incremental build systems (Bazel, Turborepo, Nx, ccache, Go's build cache)
track a dependency graph and only recompile the units affected by a given change. This matters
most in monorepos, where a change to one package shouldn't trigger a rebuild-and-retest of forty
unrelated ones.

```
# the question every incremental build system answers:
# given this diff, which build targets have inputs that changed?
# answer determines the *minimum* rebuild — not "rebuild everything to be safe"
```

**Done when:** a one-line change to a leaf module rebuilds only that module and its dependents,
not the whole tree.

## 3. Layer caches from local to remote, and key them on content

Local caches (a developer's machine) are fast but useless across CI runners or team members;
remote/shared caches (a build cache server, Bazel remote cache, Docker registry as layer cache)
let a build done once by anyone benefit everyone. Key cache entries on a hash of the actual
inputs — source content, dependency versions, compiler flags — never on a branch name, timestamp,
or manually incremented cache version, which are exactly the things that drift out of sync with
what's actually cached.

- **Local cache:** fastest, developer-machine-scoped, warms per-session.
- **Remote/shared cache:** slower per-hit than local but shared across CI runners and the whole
  team — this is where the real leverage is for CI.
- **Content-addressed keys** make cache correctness self-verifying: wrong input hash means
  guaranteed cache miss, never a stale hit.

**Done when:** a cache hit on one CI runner is reusable by a different runner building the same
inputs, without manual synchronization.

## 4. Parallelize what the dependency graph allows, not more

Once the minimum necessary work is identified (via incrementality) and reuse is maximized (via
caching), the remaining work parallelizes across cores or machines based on the dependency graph
— independent modules build simultaneously, dependent ones wait. Parallelizing before
establishing correct incrementality and caching just means doing unnecessary work faster, which
is a much smaller win than not doing it at all.

**Done when:** build time scales down with added parallelism up to the critical path length of
the dependency graph, not further.

## 5. Treat cold-build time as a tested number, not an assumption

A cache-warm build looks fast in every demo and every day-to-day developer loop, which hides how
bad the cold-build path (new contributor, new CI runner, cache eviction, cache-busting dependency
bump) has become. Measure cold-build time explicitly and periodically — it's the number that
determines onboarding experience and the worst-case CI latency when a cache is invalidated or
unavailable.

**Done when:** cold-build time (cache empty, from clean checkout) is a known, tracked number, not
a guess based on the common warm-cache case.

## Report

State what makes the build hermetic (or where it isn't yet), the caching layers in use and how
keys are derived, and both warm-cache and cold-build times. Name the honest gap: usually it's a
build that's still not fully hermetic (some ambient dependency), a cache key that's coarser than
it should be, or a cold-build time nobody has actually measured recently.
