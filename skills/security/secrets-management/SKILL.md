---
name: secrets-management
description: Keeps credentials, API keys, and certificates out of code, images, and logs, and moves them into a real secret store with tight, scoped runtime injection. Use this whenever the user is hardcoding a password or token, asking how to store an API key, setting up a CI pipeline that needs credentials, configuring a secret store like Vault or a cloud KMS, or responding to a leaked secret. For who is allowed to fetch those secrets use `iam-access-management`; for scanning dependencies and images for other flaws use `vulnerability-management`.
license: MIT
---

# Secrets Management

A secret in source control is compromised the moment it is committed, regardless of whether the
repo is public — history, forks, CI logs, and local clones all outlive the "private" label. The
fix is not discipline, because discipline does not scale past one careless commit. The fix is
making it structurally hard to commit a secret and structurally easy to fetch one at runtime
from somewhere that isn't a text file.

Treat every credential as a liability with a lifecycle: issued, scoped, rotated, and revocable.
A secret with no expiry and no owner is not a convenience, it is deferred incident.

**A secret you cannot rotate in minutes is not a secret, it is a permanent liability.**

For step-by-step zero-downtime rotation and a leaked-secret response checklist, read
`references/rotation-playbook.md`.

## 1. Block secrets before they're committed

Pre-commit hooks and CI-stage scanners (gitleaks, trufflehog, detect-secrets) catch the AWS key
pasted into a config file before it becomes permanent history. Run the same scan in CI as a
required check, not just locally, because local hooks get skipped with `--no-verify` under
deadline pressure and nobody reverts that later.

- **Fail the build, don't just warn**: a warning in build logs that nobody reads is not a
  control.
- **Scan history on onboarding a repo**, not just new commits — old leaks are still live
  credentials until rotated.
- **Allowlist by pattern, not by file**, so a real secret added later to an allowlisted file
  still gets caught.

**Done when:** a test commit containing a fake credential is rejected by both the pre-commit
hook and the CI pipeline.

## 2. Put secrets in a store, reference them by name

Vault, AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault exist so that "where is the
database password" has one answer instead of one answer per environment file. Application
config should hold a reference — a secret path or ARN — never the value. This also means
rotating a secret doesn't require a code change or redeploy, just an update at the source.

```yaml
# good: config holds a pointer, not a value
database:
  password_from: secret/prod/db/password
```

**Done when:** grepping the entire codebase and container images for the literal secret value
returns nothing.

## 3. Inject at runtime, scoped to what actually needs it

A secret baked into an image layer or a global environment variable available to every process
on a host is available to every process that gets compromised, not just the one that needed it.
Prefer sidecar injection, short-lived environment population at container start, or workload-
identity-based fetch, so the secret exists only in the memory of the process that needs it and
only for as long as that process runs.

- **Scope by workload, not by cluster or account**: a payments service and a marketing site
  should not be able to read each other's secrets even if they share infrastructure.
- **Never bake secrets into image layers** — `docker history` and layer inspection will find
  them even after a later layer deletes the file. See `containerization` for build hygiene that
  prevents this.
- **Avoid secrets in CI logs**: mask output, and don't `echo` a variable to debug it.

**Done when:** no secret value appears in `docker inspect`, image layer history, or a build
log.

## 4. Rotate on a schedule, not just on suspicion

A secret that has never rotated has been silently trusted by everyone with access since day
one, including people who left the team. Automated rotation (store-managed, short expiry, or a
scheduled job) keeps the blast radius of any future leak small by construction, independent of
whether anyone notices a leak happened.

- **Short-lived over static wherever possible**: prefer credentials that expire in hours over
  ones that expire never. See `iam-access-management` for the broader case for short-lived
  access.
- **Rotate immediately on any personnel change** with access to a shared secret.

**Done when:** every credential in the store has a defined rotation interval and an owner.

## 5. Revoke first, investigate second, when a secret leaks

The instinct to figure out blast radius before acting costs exactly the time an attacker needs.
On confirmed exposure, revoke or rotate the credential immediately, then investigate what it
touched and whether it was used. A false alarm costs a rotation; a real one caught late costs
much more. Coordinate the timeline and postmortem with `incident-response`.

- **Rotate the secret** at the source of truth first.
- **Audit access logs** for the credential's actual usage window, not just its existence
  window.
- **Purge from history** (e.g. `git filter-repo`) only after rotation — cleaning history
  without rotating leaves the same key valid elsewhere.

**Done when:** the exposed credential no longer authenticates, verified by attempting to use
the old value.

## Report

State which scanner runs at commit time and which runs in CI, which store now holds production
secrets, and the rotation interval assigned to each credential class. Name any secret that is
still static or still injected as a wide-scoped environment variable rather than scoped to its
workload — that gap is the next incident waiting to happen, and naming it beats claiming full
coverage.
