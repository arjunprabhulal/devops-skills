# Security Policy

This repository ships Markdown instructions for AI agents, plus two Python scripts — a validator
and a build script. It runs no service, exposes no network surface, and has no runtime
dependencies. The threat model is
therefore about the content itself and what an agent does after reading it.

## What counts as a security issue here

- **A skill that instructs an agent to do something destructive.** For example, a `SKILL.md` step
  that deletes state, force-pushes, disables a safety control, or runs a command whose blast radius
  is wider than the text implies.
- **A skill that instructs an agent to do something insecure.** For example, guidance that
  disables TLS verification, hardcodes a credential, grants a wildcard IAM policy, or recommends a
  pattern that silently weakens an existing control.
- **A real credential in the repository.** Any live token, key, certificate, or connection string
  in a `SKILL.md`, a `references/` file, or an `evals/<skill>.json` case. Examples must be
  obviously fake.
- **A malicious or unsafe change to `scripts/`.** `scripts/check-skills.py` and
  `scripts/build-antigravity.py` run locally and in CI (`.github/workflows/ci.yml`). A pull request
  that makes either execute untrusted input, reach the network, or write outside the repository is
  a security issue.

Ordinary content errors — a wrong flag, an outdated API, a stale link — are not security issues.
Open a normal issue for those.

## Reporting

Report privately through GitHub Security Advisories:

<https://github.com/arjunprabhulal/devops-skills/security/advisories/new>

Include the file path, the specific text, and what an agent following it would do. Do not open a
public issue or pull request for an exposed credential; report it privately so it can be revoked
first.

## Response

Reports are reviewed on a best-effort basis by a single maintainer. There is no service level
agreement and no guaranteed response time. Confirmed issues are fixed on `main`. An exposed
credential must be treated as compromised and rotated, regardless of when the file is removed.

## Supported versions

`main` is the only supported branch. Fixes land there and are not backported. Tags and forks are
not maintained.
