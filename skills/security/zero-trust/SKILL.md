---
name: zero-trust
description: Replaces network location with verified identity as the basis for access, removing implicit trust inside the perimeter via microsegmentation and continuous verification. Use this whenever the user assumes "inside the VPC" means trusted, wants access controls that follow identity rather than IP address, is planning a migration off perimeter-based security, or is limiting lateral movement after a compromised workload. For firewalls and segmentation use `network-security`; for the role model behind access decisions use `iam-access-management`.
license: MIT
---

# Zero Trust

Perimeter security makes one assumption that modern breaches consistently break: that
everything inside the network boundary can be trusted because getting inside was hard. It
wasn't hard — a phished credential, a compromised laptop, or a vulnerable service is enough to
get inside, and once an attacker is in, a perimeter model hands them free lateral movement to
everything else on the network, because nothing inside was designed to distrust anything else
inside.

Zero trust replaces "where is this request coming from" with "who or what is this request, and
is it authorized for exactly this action, right now." Every request is verified on its own
merits, independent of network location, every time.

**Being on the network was never proof of anything except that you were on the network.**

## 1. Verify identity, not IP address or subnet

An IP address says where a packet came from, not who's actually making the request — it's
trivial to spoof, and it says nothing once traffic is routed through a shared subnet or a
compromised jump host. Every request should authenticate as a specific identity (a user, a
workload, a service account) with cryptographic proof, and every decision should be made
against that identity, not against "is this traffic coming from inside the VPC."

**Done when:** revoking a workload's identity blocks its access, regardless of what network
segment it's still physically connected to.

## 2. Eliminate implicit trust between internal services

"It's an internal service call, so it's fine" is exactly the assumption zero trust exists to
remove. Every service-to-service call should authenticate and authorize independently — mTLS
with workload identity, short-lived tokens per call — the same as a call arriving from outside
would. This is a meaningfully different bar than internal TLS alone (see `network-security` for
the wire-encryption piece); zero trust additionally requires each call to prove *who* is
calling, not just that the channel is encrypted.

**Done when:** a service can't successfully call another internal service without presenting a
verifiable identity, even from an already-internal network path.

## 3. Microsegment down to the workload, not just the subnet

Network segmentation by tier (see `network-security`) is a coarse first cut; zero trust pushes
the boundary down to individual workloads, where each workload has an explicit, minimal list of
what it's allowed to talk to. This is what actually limits lateral movement — a compromised pod
in the application tier still can't reach a database it was never authorized to reach, even
though both live in the same broad segment.

- **Default every workload to zero allowed connections**, then add exactly what its function
  requires.
- **Tie policy to workload identity**, not IP, so policy survives autoscaling, rescheduling,
  and IP churn.

**Done when:** a compromised workload's lateral movement options are limited to the specific
peers it was explicitly authorized to reach.

## 4. Make every access decision continuous, not one-time

A perimeter model checks trust once, at the network boundary, and then trusts everything that
follows. Zero trust re-evaluates on every request — is this identity still valid, still
authorized, still exhibiting expected behavior — so a session or credential that was legitimate
a minute ago but is now compromised or revoked doesn't get a free pass on the strength of an
earlier check.

**Done when:** revoking a credential mid-session terminates access within the credential's
normal validity window, not just at next login.

## 5. Migrate incrementally, starting from the highest-value assets

Rearchitecting every system for zero trust at once is not realistic and stalls the whole
effort. Start with the highest-value or most exposed assets — the systems holding customer
data, the ones with the widest current blast radius — and expand outward. A partial rollout
that covers the systems that matter most is worth far more than a stalled all-or-nothing plan.

- **Keep perimeter controls during the transition**: zero trust is additive to the fundamentals
  in `network-security`, not a replacement that lets you drop segmentation and egress control
  early.

**Done when:** the highest-value systems require verified identity for every access, even from
inside what used to be the trusted perimeter.

## Report

State which systems currently enforce identity-based access versus which still rely on network
location or perimeter trust, and what the microsegmentation boundary currently is (subnet,
tier, or workload). Name the highest-value system still trusting network position alone —
that's the biggest remaining exposure, and naming it is more credible than declaring the
migration complete.
