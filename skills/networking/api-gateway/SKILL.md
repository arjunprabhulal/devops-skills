---
name: api-gateway
description: Covers the managed front-door pattern for APIs — request routing, centralized auth, rate limiting and quotas, request/response shaping, and recognizing when a gateway helps versus becomes a bottleneck or single point of failure. Use this whenever the user is designing an API entry point, adding rate limits or quotas, centralizing auth for several backend services, transforming a request between an external and internal contract, or debugging a gateway timeout. For east-west traffic between internal services use `service-connectivity`, and for token issuance details use `iam-access-management`.
license: MIT
---

# API Gateway

An API gateway earns its place by centralizing the things every backend would otherwise
reimplement badly: authentication, rate limiting, and a stable external contract in front of
services that change internally all the time. It only pays for itself when it stays a thin,
well-understood layer — the moment it accumulates business logic, it becomes a second application
nobody wants to own, deployed on a critical path everything else depends on.

The gateway is infrastructure, not a place to write features. **Every rule it enforces should be
cross-cutting; anything specific to one backend belongs in that backend.**

## 1. Route by contract, not by convenience

The gateway's routing table is the external API's actual shape — clients depend on it staying
stable even as internal services are renamed, split, or replaced behind it. Decide routing rules
(path, host, header) up front as a deliberate contract, not as whatever happened to match during
initial setup, because changing that contract later is a breaking change for every client.

- **Version the external contract explicitly** (`/v1/`, a header, or a distinct host) so internal
  refactors never force every client to change at once.
- **Keep the mapping from external route to internal service in one place**, reviewable as a unit,
  not scattered across per-team gateway plugins.

**Done when:** an internal service can be renamed or split without any external client noticing.

## 2. Centralize auth, but don't let the gateway become the source of truth for identity

The gateway is the right place to enforce "is this request authenticated" once instead of in every
backend — validating a token's signature and expiry is exactly the kind of cross-cutting check that
belongs at the edge. It is the wrong place to own user identity or session state; that stays in an
identity provider, with the gateway only checking, not issuing or storing.

- **Validate tokens at the gateway**, and pass identity downstream as a verified header or claim so
  backends don't re-implement token parsing.
- **Never let the gateway silently downgrade auth failures to "allow"** on a validation error —
  fail closed, not open.
- **Full identity and authorization policy design** lives in `iam-access-management`; the gateway
  enforces decisions, it doesn't define them.

**Done when:** every backend behind the gateway can trust that an authenticated request has
already been verified, without re-checking the token itself.

## 3. Set rate limits and quotas around a real capacity number

A rate limit that isn't tied to what the backend can actually absorb is either useless (too high to
ever protect anything) or a self-inflicted outage waiting to happen (too low, throttling
legitimate traffic). Quotas are a different, business-facing control — how much a given client is
entitled to over a longer window — and conflating the two produces confusing 429s that don't map
to either concern.

```yaml
rate_limit:
  per_client: 100/s        # protects backend capacity, short window
quota:
  per_client_monthly: 1_000_000   # business entitlement, long window
```

**Done when:** a rate-limit response tells the caller which control they hit and when to retry,
and the limit itself is tied to a measured backend capacity, not a guessed number.

## 4. Shape requests at the edge only when it saves every backend from doing it

Header injection, request/response transformation, and payload validation at the gateway are
worthwhile when every backend behind it would otherwise duplicate the same logic. They stop being
worthwhile the moment the transformation encodes business rules specific to one backend — that
turns the gateway into an undeployable, unversioned dependency every team is afraid to touch.

- **Cross-cutting shaping** (CORS headers, request-ID injection, response envelope normalization)
  belongs at the gateway.
- **Business-specific transformation** (reshaping one service's payload) belongs in that service,
  even if it means one more hop.

**Done when:** no rule in the gateway config is specific to a single backend's business logic.

## 5. Recognize when the gateway becomes the bottleneck or the single point of failure

A gateway that terminates every request for every service is now on the critical path for all of
them — its capacity, its deploy cadence, and its uptime become the platform's. That's an acceptable
tradeoff deliberately made, not a default that should go unexamined as traffic grows.

- **Capacity-test the gateway itself**, not just the backends behind it — see `load-testing`.
- **Deploy the gateway with the same rigor as any other production service** (canary, rollback,
  redundancy across zones) since an outage here takes down everything behind it.
- **Consider a service mesh for internal traffic** once east-west volume between services
  outgrows what routing through a single north-south gateway makes sense for — see
  `service-mesh`.

**Done when:** you can state the gateway's own capacity limit and what happens to all backend
traffic if it degrades.

## Report

State what the gateway centralizes (auth, rate limiting, routing), the external API contract
version, the measured capacity behind current rate limits, and how the gateway itself is deployed
for redundancy. Name the honest gap — usually a rate limit set by guess rather than measurement, or
a piece of business logic that crept into the gateway config — rather than presenting the gateway
as a clean, thin layer when it has accumulated exceptions.
