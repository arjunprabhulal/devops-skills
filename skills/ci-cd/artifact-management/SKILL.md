---
name: artifact-management
description: Versions, stores, and promotes build outputs — registries, immutability, build-once-promote-many, retention and garbage collection, and provenance metadata. Use this whenever the user sets up an artifact or container registry, asks how to promote a build between environments without rebuilding, needs a retention or cleanup policy, or wants to trace where an artifact came from. For an image's contents and size use `image-optimization`; for vulnerability scanning use `image-scanning`.
license: MIT
---

# Artifact Management

An artifact is the one thing that should never be ambiguous in a delivery pipeline: given a
version or digest, everyone — CI, CD, an engineer debugging an incident six months later — should
be able to retrieve the exact same bytes. The moment an artifact can be overwritten, rebuilt with
a different result, or referenced by a mutable tag like `latest`, every downstream promise (this
is what passed CI, this is what's in staging, this is what's in prod) becomes unverifiable.

If you can't prove two environments are running the exact same artifact, you can't actually debug
the difference between them.

**An artifact, once built, is immutable — every later stage promotes it, none of them rebuild
it.**

## 1. Build once, promote the same bytes everywhere

Rebuilding "the same" artifact for staging and again for production is the single most common
artifact-management mistake, because non-determinism anywhere in the build (unpinned dependency,
timestamp embedded in the binary, compiler nondeterminism) means the two builds aren't actually
the same thing, and you've now tested one and shipped another. Build exactly once in CI, publish
it with an immutable identity, and every later environment pulls that identity — promotion is a
metadata operation (retag, update a manifest, flip a pointer), never a rebuild.

- **CI builds it once**, produces a content-addressed digest.
- **Staging and production reference that digest**, not a rebuilt equivalent.
- **Promotion changes only which environment points at the digest**, never the bytes themselves.

**Done when:** you can diff the digest running in production against the digest that passed CI
and they match exactly.

## 2. Version with immutable, content-derived identifiers

Mutable tags (`latest`, `stable`, even a branch name) are conveniences for humans, not identities
a system should depend on — the tag `latest` points at something different every time someone
pushes. Use a content digest (sha256) or an immutable version (a semver tag that's never reused,
or the git SHA) as the actual reference everywhere automation touches; reserve human-friendly
tags as an alias layered on top, never as the source of truth for a deploy.

```
# fragile: "latest" is a moving target, deploy is non-reproducible
image: myapp:latest

# durable: this digest is this exact set of bytes, forever
image: myapp@sha256:4f3a9c1e...
```

**Done when:** every automated deploy references an artifact by digest or immutable version,
never by a mutable tag.

## 3. Attach provenance so "what's in this artifact" is answerable without archaeology

An artifact without metadata about its source commit, build pipeline run, and dependency versions
is a black box the moment something goes wrong with it — you're left guessing what code actually
produced it. Attach provenance at build time: source commit SHA, build pipeline/job ID,
dependency lockfile hash, and ideally a signed attestation (SLSA-style) that the artifact came
from the pipeline it claims to. This is what makes an incident retro or a security review
tractable instead of a forensic exercise.

- **Source commit** the build was cut from.
- **Build pipeline run ID** for tracing back to logs and inputs.
- **Dependency manifest hash** for answering "was this affected by CVE-X" without a rebuild.

**Done when:** given only an artifact's digest, you can trace it back to the exact commit and
pipeline run that produced it.

## 4. Set retention policy before storage costs force a bad one

Registries fill up, and without an explicit retention policy, cleanup happens reactively —
someone deletes things in a panic when storage costs spike or a quota is hit, and inevitably
something still in use gets deleted along with the junk. Decide up front what's kept forever
(anything currently deployed anywhere, tagged releases) versus what's garbage-collected on a
schedule (untagged intermediate builds, old PR-build artifacts, anything past N days with no
deployment reference).

- **Never delete** anything referenced by a running deployment or an active rollback target.
- **Keep tagged releases** according to a stated retention window, not indefinitely by default.
- **Garbage-collect untagged/intermediate artifacts** aggressively — these are usually the bulk
  of storage cost.

**Done when:** retention policy is written down and enforced automatically, not executed manually
when storage alerts fire.

## 5. Scope registry access by least privilege, per environment

A registry where any CI job can push directly to the tag that production pulls is one compromised
pipeline away from a supply-chain incident. Separate write access (only the build pipeline can
push new artifacts) from promotion access (only the deploy pipeline, gated appropriately, can
move a digest into a production-referenced state) from read access (runtime pulls should be
read-only). This is a narrower, artifact-specific instance of the concerns in `pipeline-security`
and `supply-chain-security` — worth restating here because registry permissions are so often left
at their overly permissive defaults.

**Done when:** no single compromised credential can both push a new artifact and cause it to be
deployed to production.

## Report

State how artifacts are identified (digest vs tag) in production deploys, what provenance
metadata is attached and how it's queried, and the current retention policy and whether it's
automated. Name the honest gap: usually it's a deploy path that still references a mutable tag
somewhere, provenance that's incomplete for older artifacts, or retention that's still manual.
