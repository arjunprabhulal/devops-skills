---
name: security-scanning
description: Places SAST, DAST, and dependency scanning at the right stage of the pipeline, tuned to gate or merely inform depending on confidence, without turning every merge into a wall of unreviewed findings. Use this whenever the user is adding a security scanner to CI, choosing between SAST and DAST, deciding whether a scan should block a merge, tuning scanner noise, or complaining that a pipeline is full of findings nobody triages. For deciding what to do with the findings once they exist use `vulnerability-management`; for the pipeline infrastructure running these scans use `pipeline-security`.
license: MIT
---

# Security Scanning

Three different scan types answer three different questions, and using the wrong one
at the wrong stage either misses real issues or floods the team with noise. SAST
looks at source code for known-bad patterns before anything runs. Dependency
scanning checks what you pulled in against known vulnerability databases. DAST
attacks a running instance the way an external attacker would. None of them replaces
the others, and none of them should gate a merge on day one with default settings.

The recurring failure isn't picking the wrong tool, it's turning every scanner on
with default sensitivity and mandatory blocking before anyone has tuned it — which
trains developers to route around the gate instead of trusting it.

**A scanner that blocks merges before it's tuned teaches the team to bypass it, not
to fix findings.**

## 1. Match the scan type to what it can actually see

SAST catches injection patterns, hardcoded secrets, and unsafe API usage in source,
fast and pre-deploy — but it doesn't know how the app behaves at runtime and
produces real false positives on code that's actually safe in context. Dependency
scanning (SCA) catches known CVEs in third-party packages, which is where most real-
world exploited vulnerabilities live. DAST catches what only shows up when the app
is actually running — auth bypass, misconfigured headers, live injection — but it's
slower and needs a running environment.

- **Run SAST and SCA on every commit**: they're fast enough not to slow anyone down.
- **Run DAST against staging, not every commit**: it needs a live target and takes
  longer, so
nightly or pre-release is usually the right cadence.

**Done when:** each scan type runs at the pipeline stage where its output is
actually actionable.

## 2. Gate on high-confidence findings, inform on the rest

Blocking a merge for every finding, including low-severity and unconfirmed ones, is
how a security gate becomes the thing everyone routes around with an override.
Reserve hard blocking for findings with high confidence and high severity —
confirmed secrets, critical known- exploited CVEs, confirmed injection. Everything
else should surface as a visible, tracked finding that doesn't stop the merge,
feeding into the triage process owned by `vulnerability- management`.

**Done when:** a developer can name which finding types block their merge and which
don't, without checking documentation.

## 3. Tune out the noise before you turn on blocking

A fresh scanner against an existing codebase produces hundreds of findings, most of
them false positives or accepted risk in that specific context. Turning on blocking
mode against that raw output guarantees the team disables the check within a week.
Run new scanners in report-only mode first, triage the initial backlog, suppress
what's not real with a documented reason, and only then flip to blocking for new
findings going forward.

**Done when:** the false-positive rate on blocking findings is low enough that
developers trust a failure means a real problem.

## 4. Keep scan results close to the code, not in a separate portal

A finding that requires logging into a different tool to see file and line number
gets ignored. Surface results as PR comments, inline annotations, or IDE
integration, wherever the tooling supports it, so fixing a finding is as close to
zero-friction as raising it.

**Done when:** a developer can see and act on a new finding without leaving their
normal PR review flow.

## 5. Revisit scanner coverage as the stack changes

A scanner configured for the stack as it existed a year ago silently misses new
languages, new frameworks, or new deployment targets added since. New services, new
languages, and new dependency ecosystems need scanner coverage added deliberately —
it doesn't happen automatically just because a scanner exists somewhere in the org.

**Done when:** every language and package ecosystem in active use has an assigned
scanner covering it.

## Report

State which scan types are wired into which pipeline stage, which finding classes
currently gate a merge versus just inform, and the current false-positive rate on
blocking checks. Name any language, service, or ecosystem still without scanner
coverage — that blind spot is real risk, and naming it beats reporting the pipeline
as fully covered.
