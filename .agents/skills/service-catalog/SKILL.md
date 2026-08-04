---
name: service-catalog
description: Builds and maintains a catalog of every service, its owner, and its scaffolding template so "who owns this" and "how do I start a new one" always have one authoritative answer. Use this whenever the user sets up Backstage or a similar catalog, asks who owns a service during an incident, scaffolds a new service, audits for orphaned systems, or wires ownership metadata into paging and access control. For the templates it scaffolds from use `golden-paths`; for the platform it runs on use `internal-developer-platform`; for wiring ownership into paging use `on-call-management`.
license: MIT
---

# Service Catalog

During an incident, "who owns this" is a question that should never require asking around. A
service catalog exists to make ownership, on-call routing, and dependencies a lookup instead of a
Slack archaeology exercise. The catalog fails the moment it drifts from reality — a stale entry is
worse than no entry, because it sends the incident responder to the wrong team with false
confidence.

Treat the catalog as the source of truth by construction, not by discipline: **an entry that isn't
enforced by tooling will go stale, and a stale catalog is a liability wearing the costume of
documentation.**

## 1. Make registration a side effect of scaffolding, not a separate step

If registering a new service in the catalog is a manual form someone fills out after the fact, it
gets skipped under deadline pressure and the catalog silently loses coverage. Wire catalog
registration into the scaffolding path itself — creating a service from a template in
`golden-paths` should register it automatically, with owner and metadata pre-populated from the
template's prompts.

**Done when:** a newly scaffolded service appears in the catalog with correct ownership metadata
before its first commit is merged.

## 2. Require an owner, not a team name in a text field

"Owned by platform-team" written as free text is not queryable, not pageable, and not enforceable.
Ownership metadata needs to resolve to a real identity — a group that maps to an actual on-call
rotation and a real access-control group, not a label. This is what lets ownership metadata drive
paging automatically instead of requiring a human to translate "team name" into "who do I actually
call." See `on-call-management` for wiring that owner field into the paging path itself.

```yaml
# bad: a string, unqueryable and unenforceable
owner: "the payments folks"

# good: resolves to a real group backing access control and paging
owner: team-payments
tier: 1
pagerduty_service: payments-api
```

**Done when:** every entry's owner field resolves to a real group that shows up in both the
identity provider and the paging system — not a free-text string.

## 3. Fail CI on missing or stale metadata

A catalog that relies on developers remembering to update it degrades at a predictable, steady
rate. Add a CI check that fails a service's pipeline if its catalog entry is missing required
fields (owner, tier, repo link, on-call) or hasn't been reviewed past a staleness threshold. This
turns "someone should update the catalog" into an enforced gate, the same way `pipeline-security`
turns security review from a suggestion into a required check.

**Done when:** a service with a missing owner field fails its CI pipeline, not just a quarterly
audit spreadsheet.

## 4. Make discovery the default reason people open it

A catalog only survives if people open it to find things, not just to satisfy an audit. Index
service dependencies, API contracts, and runbook links alongside ownership, so "what does this
depend on" and "how do I call this service" are answered in the same place as "who owns it." A
catalog that only answers ownership questions gets bookmarked by one team and forgotten by
everyone else.

- **Link runbooks directly on the service page** — see `runbooks` for what belongs in them.
- **Surface deployment status and recent incidents** inline, not in a separate tool nobody
  cross-references.
- **Make search actually fast** — a catalog developers can't find things in gets abandoned within
  a month.

**Done when:** a developer unfamiliar with a service can find its owner, dependencies, and
runbook in under thirty seconds without asking anyone.

## 5. Audit for orphans on a schedule, not by accident

Teams get reorged, services get deprecated, and the catalog entry outlives both unless something
actively checks. Run a scheduled audit that flags services with no recent deploys, an owner group
that no longer exists, or a tier mismatched to actual traffic, and route those flags to a real
person, not a dashboard nobody watches.

**Done when:** every catalog entry has been touched or reviewed within the audit's staleness
window, with zero entries pointing to owner groups that no longer exist.

## Report

State how many services are registered, what percentage have complete and current ownership
metadata, and what CI gate enforces that. Name any services you know exist but haven't been
registered yet, and any orphaned entries still pointing at disbanded teams — that's the honest
coverage gap, and naming it beats claiming the catalog is complete.
