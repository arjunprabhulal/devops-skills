---
name: container-registry
description: Stores and distributes container images safely — tagging strategy, immutability, retention and garbage collection, access control, signing, and replication or pull-through caching. Use this whenever the user asks about registry setup, mutable versus immutable tags, cleaning up old images, who can push or pull, image signing or verification, or images being slow to pull across regions. For scanning image contents use `image-scanning`; for reducing what gets pushed use `image-optimization`.
license: MIT
---

# Container Registry

A registry is not just storage, it's the trust boundary between "someone built this" and
"production is running it." Most registry incidents trace back to one thing: a tag that meant one
image yesterday and a different one today, with nothing in the deploy pipeline able to tell.

**A tag you can overwrite is not a version, it's a pointer with a rumor attached.**

## 1. Never deploy off a mutable tag

`latest`, and any tag your CI re-pushes on every build, can change underneath a running
deployment with no record of what actually shipped. Tag every build with something immutable — a
git SHA, a semantic version, or the content digest itself — and deploy by that identifier.
Mutable, human-friendly tags (`stable`, `latest`) are fine as a *pointer* for humans browsing the
registry, but the deploy manifest should always reference the immutable tag or digest underneath.

```
myapp:latest          -> convenience pointer, humans only
myapp:2.4.1            -> immutable, safe to deploy
myapp@sha256:abc123...  -> what actually got pulled, verifiable
```

**Done when:** every running deployment can be traced to one specific, unchangeable image digest.

## 2. Set a retention policy before storage becomes the incident

Registries fill up silently — every CI run pushes a new tag, and without garbage collection the
registry grows until a push fails mid-release. Define retention rules explicitly: keep all tags
referenced by an active deployment or Helm chart indefinitely, keep the last N builds per branch,
and expire untagged/dangling manifests on a schedule. Automate the sweep; a manual cleanup process
is a process nobody runs until it's an emergency.

- **Never expire** a tag or digest currently referenced by a running deployment.
- **Cap per-branch history** (e.g., last 20 builds) instead of keeping every commit forever.
- **Sweep dangling manifests** left behind by re-tags and failed pushes on a schedule.

**Done when:** registry storage growth is bounded by a policy, not by whoever notices it's full.

## 3. Scope push and pull access separately

Push access is a much higher-privilege action than pull — anything that can push can put an
attacker-controlled image in front of "trusted" tags. Grant push only to CI service identities
building from a protected branch or a reviewed release process, never to a broad human group.
Pull access can be wider (all engineers, all clusters) but should still be scoped per-repository
or per-namespace rather than one shared credential covering every image in the org, so a leaked
credential has a bounded blast radius.

**Done when:** no human account holds standing push access, and pull credentials are scoped to
what a given consumer actually needs.

## 4. Sign images and verify before pull in production

A digest tells you the image is unchanged since push; a signature tells you *who* pushed it. Sign
images at build time (cosign or the registry's native signing) and enforce signature verification
at deploy time via admission control, so an image that reached the registry through some path
other than your pipeline — a compromised credential, a manual push — gets rejected before it runs.
Signing is about provenance of the artifact; what's *inside* it is `image-scanning`'s concern, and
the two should run as separate, complementary gates.

**Done when:** a deploy of an unsigned or invalidly-signed image is rejected, not just logged.

## 5. Replicate or cache for the regions that actually pull

A single-region registry turns every pull from a distant cluster into a cross-region network
dependency — slow at best, a hard outage dependency at worst if that region has an incident.
Use registry replication or a pull-through cache local to each region or cluster so pulls resolve
against nearby storage. Verify replication lag explicitly; a replica that's behind by an hour can
serve an older, potentially vulnerable image without anyone noticing.

**Done when:** pulls in every active region resolve against local or near storage, and replication
lag is monitored.

## Report

State the tagging convention in use, the retention policy and its horizon, who holds push access,
and whether signature verification is enforced at deploy time. Name any region or cluster still
pulling cross-region without a local cache — that latency and availability exposure is the honest
gap, not a registry that "works fine today."
