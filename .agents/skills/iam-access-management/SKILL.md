---
name: iam-access-management
description: Grants least-privilege access to systems and cloud resources through roles rather than individual permissions, short-lived credentials, and regular review, so standing access doesn't accumulate unnoticed. Use this whenever the user is granting cloud or system access, designing IAM roles or policies, setting up break-glass procedures, reviewing who has access to what, or asking why a person or service still has a permission nobody remembers granting. For where the credentials themselves live use `secrets-management`; for enforcing identity-based access on the network itself use `zero-trust`.
license: MIT
---

# IAM & Access Management

Access accumulates and almost never gets removed on its own. Someone needs prod database access
for one incident and keeps it for two years; a service gets an admin role because scoping it
down "later" was never a priority. Every one of those grants is a standing liability whether or
not it's ever misused, because it's one more credential an attacker can compromise and one more
thing an auditor has to explain.

The fix isn't better memory, it's a system where access is granted through roles with a defined
scope and a defined lifetime, reviewed on a cadence, and revoked by default when it's no longer
actively used.

**Access that nobody remembers granting is access nobody is defending.**

## 1. Grant through roles, not individual permissions

Individual grants ("give Priya S3 read on this bucket") don't scale and don't survive personnel
changes — six months later nobody remembers why Priya has it or whether she still needs it.
Roles ("data-analyst-readonly") bundle a reviewed, intentional set of permissions that can be
assigned and revoked as a unit, audited as a unit, and reasoned about independent of who
currently holds them.

- **Name roles by function, not by person or team**, so the role outlives org changes.
- **Review role definitions**, not just role assignments — permission creep happens inside
  roles too, as "just one more permission" gets added over time.

**Done when:** no individual has a permission granted outside of a role assignment.

## 2. Prefer short-lived credentials over static ones

A static access key is valid until someone remembers to rotate or revoke it — which in practice
means indefinitely. Short-lived, dynamically issued credentials (STS tokens, workload identity
federation, Vault dynamic secrets) expire on their own, so a leaked credential has a small,
bounded blast radius instead of an unbounded one. This is the same rotation principle as
`secrets-management`, applied to identity and access rather than application secrets.

**Done when:** human and service access to production defaults to credentials that expire in
hours, not credentials that never expire.

## 3. Review access on a real cadence, not just at offboarding

Offboarding revokes access for people who left; it does nothing for the much larger set of
people who stayed but no longer need what they were granted. A quarterly access review — who
has what, do they still need it — catches the slow accumulation that offboarding never touches.
Automate the review report; don't make a human manually cross-reference an IAM console against
an org chart.

**Done when:** a scheduled review process has run at least once and produced revocations, not
just a report nobody acted on.

## 4. Give break-glass access an audit trail, not a standing door

Emergency access to production needs to exist, but it should be an event, not a permanent open
door. A break-glass path should require explicit invocation, log who used it and when, expire
automatically, and trigger a mandatory post-use review — the access itself is fine, the silence
around its use is the risk.

| Property | Standing admin access | Break-glass access |
|---|---|---|
| Duration | Indefinite | Minutes to hours, auto-expires |
| Trigger | Granted once, forgotten | Explicit invocation per use |
| Review | Rare | Mandatory after every use |

**Done when:** every break-glass invocation in the last quarter has a logged reason and a
completed post-use review.

## 5. Remove standing access by default, grant on demand

The safest permission is the one that doesn't exist until it's needed. Just-in-time access —
request, approve, time-box, auto-revoke — replaces the default of "keep access forever in case
it's needed again" with "grant it in the two minutes it takes to approve." This inverts the
usual failure mode: instead of access silently accumulating, it silently expires, which is the
direction you want the default to fail in.

**Done when:** the default state for sensitive production access is "not granted," with a
request path that grants it temporarily.

## Report

State how access is currently granted (individual vs. role-based), the credential lifetime for
both human and service access, and when the last access review ran and what it revoked. Name
any system still using static, long-lived credentials or individual grants outside a role —
that's the exception carrying the most risk, and naming it is more honest than reporting the
review as complete.
