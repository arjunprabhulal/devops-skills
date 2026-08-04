---
name: dns-management
description: Covers DNS as production infrastructure that can take down everything downstream — record types, TTL tradeoffs, propagation and caching, health-checked failover, and split-horizon setups for internal versus external views. Use this whenever the user is planning a DNS cutover, choosing a TTL, debugging why a domain won't resolve after a change, setting up failover records, or separating internal and external resolution of the same zone. For diagnosing an active resolution failure step by step use `network-troubleshooting`, and for distributing traffic once DNS resolves use `load-balancing`.
license: MIT
---

# DNS Management

DNS is the layer everyone forgets is a distributed system until it breaks one. A record change
doesn't take effect atomically everywhere — it propagates through a chain of caching resolvers,
each honoring a TTL you set, and a large share of "the whole platform is down" incidents turn out
to be a single wrong record or an expired zone, not the application at all.

Treat every DNS change like a deploy: plan the rollout, control the blast radius with TTL, and
have a way to verify it landed before you call it done. **DNS is infrastructure with its own
deploy pipeline — changes have propagation lag and no instant rollback.**

## 1. Pick the record type for what's actually being pointed at

`A`/`AAAA` records point a name directly at an IP; `CNAME` points a name at another name and
cannot coexist with other records on the same label; `ALIAS`/`ANAME` (provider-specific) give
CNAME-like flexibility at a zone apex where CNAME is disallowed. Getting this wrong is the most
common reason a root domain can't point at a load balancer with a rotating IP.

- **Zone apex records** (`example.com`, not `www.example.com`) generally cannot be a `CNAME` per
  the DNS spec — use an apex-capable alias feature or an `A` record with a stable IP.
- **`MX` and `TXT`** carry mail routing and verification/SPF/DKIM data — breaking these silently
  breaks email deliverability, not uptime, so they're easy to overlook in a network review.
- **`NS` delegation** determines who is authoritative for a subdomain; a stale `NS` record points
  queries at a name server that no longer answers for that zone.

**Done when:** every record's type matches what it points at, and the zone apex resolves without
relying on `CNAME`.

## 2. Use TTL as a deliberate lever, not a fixed default

A long TTL (hours) reduces query load and is fine for stable records, but it means a mistake or an
emergency failover takes that long to fully propagate through every caching resolver on the
internet. A short TTL (minutes) costs more queries but buys fast rollback. The move is to lower
TTL *before* a planned cutover and raise it again once the new value has proven stable.

**Done when:** any record involved in an upcoming cutover has had its TTL lowered at least one
full TTL cycle in advance.

## 3. Build failover on health checks, not on hope

DNS-based failover — routing policies like weighted, latency-based, or primary/secondary with
health checks — only helps if the health check reflects something real (a synthetic HTTP request
to the actual service path, not just "is the IP pingable"). Without a health check, a failover
record is just a second static record that never activates.

- **Health-check the thing users actually depend on** — an endpoint that exercises the real
  request path, not the load balancer's own liveness port.
- **Know your failover's floor**: even a perfect health check can't fail traffic over faster than
  the TTL lets caches expire the old answer.
- **Test the failover deliberately** on a schedule, the same way you'd test a disaster-recovery
  runbook — see `disaster-recovery` for the broader failover practice this feeds into.

**Done when:** a simulated origin failure causes traffic to shift within one TTL window, verified
end to end, not just configured.

## 4. Respect that propagation is caching, not replication

There is no single moment when "DNS has propagated" — every resolver between the user and your
authoritative server caches independently until its copy of the TTL expires, and negative
responses (NXDOMAIN) get cached too, per the zone's `SOA` negative-caching value. A record that
looks wrong five minutes after a change may just be a resolver that hasn't expired its cache yet;
don't chase a phantom bug by re-editing the record.

**Done when:** you can distinguish "not yet propagated to this resolver" from "the record is
actually wrong" using a fresh query against the authoritative server directly.

## 5. Make split-horizon DNS a deliberate design, not an accident

Split-horizon (or split-view) DNS answers the same name differently depending on whether the
query comes from inside or outside the network — internal clients get a private IP, external
clients get a public one. This is the right tool for exposing one hostname to both, but it is a
common source of "works on my laptop, not in the datacenter" bugs when the two views drift or a
record is added to only one.

- **Keep both views in sync deliberately** — a change made to the external zone and forgotten in
  the internal one is the classic split-horizon bug.
- **Document which resolver serves which population**, since debugging requires knowing which view
  a given client is even hitting.

**Done when:** internal and external views resolve consistently for every name that should be
dual-homed, and the exceptions are documented, not accidental.

## 6. Monitor DNS as a first-class production dependency

Domain and DNSSEC certificate expiry, authoritative server health, and unexpected zone changes are
all classic self-inflicted outages that monitoring catches trivially and nothing else catches at
all. DNS failures rarely show up in application metrics — the app never even gets a chance to run.

**Done when:** domain expiry, DNSSEC expiry, and unauthorized zone changes all have their own
alerts, independent of application-level monitoring covered in `observability`.

## Report

State the record types and TTLs touched, whether a cutover required a temporary TTL reduction and
whether it was reverted, how failover health checks were validated, and the current split-horizon
posture if one exists. Name the honest gap — usually a record whose TTL was never lowered back
down, or a failover path that's configured but has never actually been tested — rather than
implying the zone is fully verified when only the changed records were checked.
