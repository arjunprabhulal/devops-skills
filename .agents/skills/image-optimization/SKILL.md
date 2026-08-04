---
name: image-optimization
description: Shrinks container image size and build time — base image choice, layer minimization, dependency pruning, .dockerignore, multi-arch builds, and measuring what actually ends up in the image. Use this whenever the user complains an image is too large, a build or CI pipeline is slow, asks about distroless or scratch images, wants multi-architecture support, or wants to know what is actually inside a shipped image. For image structure and non-root users use `containerization`; for build-cache design in CI use `build-optimization`.
license: MIT
---

# Image Optimization

Size and build time are the same problem viewed from two angles: both come from carrying more
into the image, and into the build, than the running application needs. A slow build is usually a
large one — the layers you push are the layers a runner had to pull, unpack, and cache too.

Optimize by removing, not by compressing after the fact. **The fastest layer to pull is the one
that was never built.**

## 1. Choose the smallest base that still lets you debug

`scratch` and distroless bases produce the smallest, lowest-attack-surface images, but they ship
without a shell — a production incident that needs `exec`-ing in becomes much harder. A
distro-based "slim" variant is usually the right default: small enough to matter, still
debuggable. Reserve `scratch` for statically-linked binaries (Go, Rust) where you genuinely never
need a shell inside the container, and keep a debug-variant image or an ephemeral debug container
available as a sidecar for when you do.

- **Default to `-slim` or distroless** for interpreted-language runtimes.
- **Use `scratch`** only for fully static binaries with no runtime dependency on libc or a shell.
- **Keep a debug path** (ephemeral containers, sidecar) rather than adding shell tools "just in
  case."

**Done when:** the base is the smallest variant that still supports your actual debugging
workflow.

## 2. Collapse and reorder layers deliberately

Every `RUN`, `COPY`, and `ADD` is a layer, and layers do not shrink when a later layer deletes
their contents — deleting a file in layer 5 does not reclaim the space it took in layer 3. Chain
related commands with `&&` so temporary files never persist as their own layer, and clean package
manager caches in the same `RUN` that created them:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
```

Layer *order* still matters for cache reuse (see `containerization`), but here the goal is layer
*count and content* — fewer, tighter layers pull and unpack faster regardless of cache state.

**Done when:** no layer contains data a later layer only deletes.

## 3. Prune dev dependencies before the final stage

Lockfiles routinely pull in test frameworks, linters, and type-checking tools that the running
application never touches. Install with a production flag (`npm ci --omit=dev`,
`pip install --no-deps` plus an explicit runtime requirements file) or, better, install
everything in a build stage and copy only `node_modules`'s production subset — or the compiled
artifact — into the runtime stage. This is where multi-stage builds pay off twice: once for
excluding compilers, again for excluding dev-only packages.

**Done when:** `npm ls --omit=dev` (or the language equivalent) matches what actually ships in the
runtime image.

## 4. Keep the build context and cache mounts tight

A `.dockerignore` that excludes `.git`, `node_modules`, build output, and test fixtures shrinks
both the context sent to the daemon and the chance of a stray `COPY . .` invalidating cache
unnecessarily. For package managers, use BuildKit cache mounts (`RUN --mount=type=cache`) so
dependency downloads persist across builds without polluting the final image layers — you get the
speed of a warm cache without paying its size cost in the shipped artifact.

**Done when:** repeat builds on an unchanged lockfile complete without re-downloading dependencies
or bloating the image.

## 5. Build multi-arch without doubling maintenance

If the fleet runs on both amd64 and arm64 (mixed cloud instance types, Apple Silicon dev
machines), build a single manifest list with `docker buildx build --platform linux/amd64,linux/arm64`
rather than maintaining parallel Dockerfiles. Watch for base images or dependencies that only
publish one architecture — that gap surfaces as a build failure on one platform, not a warning.

**Done when:** the pushed manifest resolves correctly on every target architecture without a
platform-specific Dockerfile.

## 6. Measure the image, don't estimate it

`docker history` and a layer-inspection tool (dive, or `docker buildx imagetools inspect`) show
exactly what each layer contributed and let you catch an accidental 200MB layer before it ships.
Track image size in CI as a number that can regress, the same way you'd track a performance
benchmark — a size budget that silently creeps up is a slow leak nobody notices until the pull
timeout starts firing.

**Done when:** you can name the largest layer in the image and justify why it's there.

## Report

State the before/after image size, the base image chosen and why, and which stage removed dev
dependencies. Name the largest remaining layer and whether it can shrink further — an unexplained
large layer is the honest gap, not a size number alone.
