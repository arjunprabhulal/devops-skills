---
name: release-management
description: Coordinates what ships and when — semantic versioning, changelogs, release trains vs continuous release, and cutting a multi-service release safely. Use this whenever the user asks how to version a package, write release notes, cut a release, coordinate a release across services, or choose between shipping continuously versus on a schedule. For actually deploying a version use `continuous-delivery`; for how its bits are stored use `artifact-management`.
license: MIT
---

# Release Management

Release management is a coordination problem, not a technical one — the hard part is rarely
cutting the tag, it's making sure everyone (consumers of a library, downstream services, users
reading changelogs, on-call engineers) agrees on what "version 2.4.0 is live" actually means.
Teams that skip this discipline end up with versions that don't map to any coherent set of
changes, changelogs nobody trusts, and multi-service releases that go out in the wrong order.

A version number is a promise to consumers about what changed and whether it's safe to adopt —
treat it as an API, not a label.

**A release is a communication artifact as much as a deployment event — get the meaning right,
not just the mechanics.**

## 1. Use semantic versioning as a contract, not a convention

MAJOR.MINOR.PATCH only works if every consumer can trust it: major means breaking changes, minor
means backward-compatible additions, patch means backward-compatible fixes. The instant a team
bumps a patch version for a breaking change "because it was small," semver stops being a contract
and every downstream consumer has to read the diff anyway, which defeats its entire purpose. This
matters most for anything with external consumers — libraries, public APIs, CLIs; internal
services deployed continuously can often skip strict semver in favor of the git SHA or build
number as the real identity, with semver reserved for anything versioned independently of deploy
cadence.

- **Breaking change → major**, no exceptions, even if it "seems small."
- **New capability, backward compatible → minor.**
- **Fix only, no interface change → patch.**

**Done when:** a consumer can decide whether to upgrade by reading the version number alone,
without reading the diff.

## 2. Generate changelogs from the source of truth, not from memory

A changelog written by someone trying to remember what happened over the last sprint is
unreliable and always lags reality. Generate it from commit messages (conventional commits), PR
titles, or linked issues at release-cut time, and have a human edit for clarity rather than write
from scratch. The goal is a changelog a user can act on — "what do I need to know before
upgrading" — not a raw commit dump.

```
## v2.4.0
### Breaking
- Removed deprecated `--legacy-auth` flag (use `--auth-mode` instead)
### Added
- Support for OIDC token refresh (#412)
### Fixed
- Race condition in connection pool under high concurrency (#418)
```

**Done when:** someone who didn't write the code can read the changelog and know whether
upgrading requires any action.

## 3. Choose release cadence deliberately: trains vs continuous

A release train (fixed schedule — every two weeks, every month) trades speed for predictability:
consumers know when to expect changes, and a feature that misses the cutoff waits for the next
train instead of shipping half-finished. Continuous release (every merge is potentially a
release) trades predictability for speed and requires the discipline covered in
`continuous-delivery` — main is always releasable, incomplete work hides behind flags. Pick
trains when you have external consumers who need predictable upgrade windows (mobile apps,
enterprise software with change-control processes); pick continuous when you control the whole
deployment surface and speed matters more than predictability.

**Done when:** the team can state the release cadence in one sentence and explain why it matches
their consumers' needs.

## 4. Sequence multi-service releases by contract compatibility, not by convenience

When a release spans multiple services with a shared API or data contract, the deploy order
matters: if service A's new version requires service B's new field, B must deploy first, or A
must tolerate B's absence gracefully during the gap. Never rely on "we'll deploy both at the same
time" — deploys are never perfectly simultaneous, and the in-between state is exactly where
multi-service releases break. Write the sequencing down as part of the release plan, not as
tribal knowledge held by whoever's on call that day.

- **Backward-compatible producer before consumer** — the service emitting new data ships first,
  tolerating old consumers.
- **Backward-compatible consumer before contract change lands** — if a consumer needs to
  *require* new data, it must already handle it optionally before the producer stops sending the
  old shape.
- **Never assume simultaneity** — write the actual order, verify each step's health before the
  next.

**Done when:** the release plan states an explicit deploy order for every service involved and
why that order is safe.

## 5. Make cutting a release a repeatable, low-ceremony script

If cutting a release requires a person to remember seven manual steps (bump version, tag, build,
sign, push to registry, update changelog, notify), it will be done wrong under time pressure
exactly when it matters most — right before a deadline or during an incident fix. Automate the
mechanical parts into a single script or pipeline job; reserve human judgment for the parts that
actually need it, like deciding *whether* to cut a release and writing the human-readable
changelog summary.

**Done when:** cutting a release is a single command or pipeline trigger, not a checklist a human
executes by hand.

## Report

State the versioning scheme in use, how the changelog is generated, the release cadence and why
it fits the consumers, and — for multi-service releases — the deploy order and its rationale.
Name the honest gap: usually it's a changelog still partly hand-written, a semver contract that's
been broken before without anyone noticing, or a multi-service order that's tribal knowledge
rather than written down.
