---
name: supply-chain-security
description: Establishes trust in what you build and ship — SBOMs, build provenance, dependency pinning and verification, artifact signing, and signature verification before deploy. Use this whenever the user is asking what's inside their build, wants to pin or verify a dependency, is setting up artifact signing or SLSA provenance, is deciding whether to trust a third-party package, or is hardening a release pipeline against tampering. For patching what a scan finds use `vulnerability-management`; for the CI system producing these builds use `pipeline-security`.
license: MIT
---

# Supply Chain Security

Most teams can name every line of code they wrote and none of the hundreds of transitive
dependencies that ended up in the build. The supply chain attack doesn't target your code — it
targets the thing your code trusts implicitly: a package registry, a build server, a base
image, a CI action pulled by a floating tag. Trust that isn't verified is just an assumption
wearing a disguise.

The goal is to be able to answer, for any artifact running in production: what's in it, how it
was built, and whether it's been altered since. If you can't answer all three, you're trusting
a black box.

**If you can't prove what's in an artifact and how it got there, you're one compromised
dependency away from finding out the hard way.**

## 1. Generate an SBOM for every build

A software bill of materials is the artifact's ingredient list — every direct and transitive
dependency, its version, and its license. Without one, "are we affected by this new CVE"
requires an emergency audit instead of a query. Generate it as a build step (Syft, cdxgen, or
language-native tooling), not as a periodic manual exercise that's stale the moment it's
produced.

- **Store the SBOM alongside the artifact**, indexed by build ID, so it's queryable months
  later during an incident.
- **Diff SBOMs between releases** to catch dependency changes that snuck in without review.

**Done when:** every artifact in the registry has a corresponding SBOM you can query by package
name.

## 2. Pin dependencies and verify checksums, don't trust floating tags

`latest`, unpinned version ranges, and mutable tags mean the same build command can produce a
different artifact tomorrow — which is exactly what a compromised upstream registry needs. Pin
exact versions and lockfiles, and verify package checksums or signatures against a known-good
value before they enter the build.

```bash
# floating and unverified — silently pulls whatever the registry serves today
FROM node:latest
RUN npm install left-pad

# pinned and reproducible
FROM node:20.11.1-bookworm-slim@sha256:abc123...
RUN npm ci   # honors package-lock.json exactly
```

**Done when:** a build run twice from the same commit produces byte-identical dependency
versions.

## 3. Capture build provenance, aim for SLSA

Provenance answers "what process produced this artifact, from what source, on what
infrastructure" — a signed, tamper-evident attestation, not a changelog. Moving up SLSA levels
is a progression: reproducible builds, isolated build environments, and provenance generation
that's non-forgeable by the build's own operator. Most teams don't need the top level
immediately, but every level up removes a category of forgeable trust.

**Done when:** you can produce a signed provenance statement linking a running artifact back to
the exact source commit and build system that made it.

## 4. Sign every artifact you ship

An unsigned artifact is indistinguishable from a tampered one once it leaves the build system.
Sign container images, binaries, and packages (cosign/sigstore or equivalent) as a mandatory
build step, using keys or an identity-based signing flow the build system controls — not a
shared long-lived key sitting in a laptop. See `secrets-management` for how that signing key
itself should be stored and rotated.

**Done when:** every artifact in the registry has an associated, verifiable signature.

## 5. Verify signatures before anything deploys

Signing without enforcement is theater — it only matters if something checks it and refuses to
proceed on failure. Enforce signature verification as an admission gate at deploy time
(registry policy, admission controller, or pipeline gate), so an unsigned or tampered artifact
physically cannot reach production regardless of how it got into the registry.

- **Fail closed**: if verification can't run, block the deploy, don't wave it through.
- **Verify provenance too**, not just the signature — a validly signed artifact built from the
  wrong source is still wrong.

**Done when:** attempting to deploy an unsigned artifact is rejected by the pipeline or the
cluster.

## Report

State which build stage generates the SBOM, what signs artifacts and where that key lives, and
whether signature verification is currently enforced or only logged. Name any dependency class
still unpinned or any artifact type not yet signed — that's the open door, and saying so
plainly is worth more than a partial rollout described as done.
