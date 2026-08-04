---
name: backup-and-restore
description: Defines the discipline of building backups you can actually restore under pressure — RPO-driven frequency, restores rehearsed on a schedule, offsite immutable copies, encryption, and treating a backup that has never been restored as equivalent to no backup at all. Use this whenever the user sets up a backup job, chooses a retention policy, argues about RPO or RTO, asks whether current backups are enough, or plans for ransomware or accidental deletion. For the wider recovery plan use `disaster-recovery`, and for stateful platform durability use `stateful-workloads`.
license: MIT
---

# Backup and Restore

A backup is not a file sitting in object storage — it is a promise that you can get data back
in a specific amount of time, and that promise is worthless until it has been tested. Most
organizations discover their backup was broken, incomplete, or too slow to restore at the
exact moment they can least afford to learn it: during an incident.

The backup job succeeding is the least interesting fact about your backup strategy. The
interesting fact is whether a restore, run cold by someone who did not write the backup
script, gets the right data back inside the time the business can tolerate losing it.

**An untested backup is not a backup — it is an unverified hope that you will find out about
during an outage.**

## 1. Derive frequency from RPO, not from habit

Recovery Point Objective is the amount of data loss the business can tolerate, expressed as
time — "we can lose 15 minutes of orders" is a real constraint, "we back up nightly because
that's the default" is not. Backup frequency is a direct consequence of RPO, not an
independent decision.

- **State the RPO in writing for each dataset**, agreed with whoever owns the business impact
  of losing that data, before picking a schedule.
- **A nightly backup implies up to 24 hours of acceptable loss** — check that against what the
  business actually said, not what the tooling defaults to.
- **Use continuous or incremental backups (WAL shipping, binlog streaming) when the RPO is
  measured in minutes**, since a full nightly dump cannot meet that bar.

**Done when:** the backup schedule for each dataset is traceable to a stated RPO, not to the
tool's default interval.

## 2. Test restores on a schedule, not just backups

The backup job exercises one code path; the restore exercises a completely different one, and
it is the one that matters during an incident. A backup that has never been restored has an
unknown, not a known, recovery time.

- **Run a full restore into an isolated environment on a fixed cadence** — monthly is a
  reasonable default — and measure how long it actually takes, not how long you assumed.
- **Restore the way you would during a real incident** — from the actual backup artifact, by
  someone who is not the one who configured the job — to catch documentation gaps early.
- **Track Recovery Time Objective against the measured restore time**, and treat a restore
  that blows past RTO as a finding to fix, not a one-off.

**Done when:** a restore has been executed end to end within the last quarter, and its
duration is known and compared against the stated RTO.

## 3. Keep at least one offsite, immutable copy

A backup stored in the same account, region, or system as the data it protects is exposed to
the same failure — a compromised credential, a misconfigured deletion policy, or a ransomware
attack that encrypts primary and backup alike.

- **Replicate backups to a separate account or region** that a single compromised credential
  cannot reach, following the same boundary discipline as `disaster-recovery`.
- **Use object-lock or write-once storage for at least one retention tier**, so that even an
  attacker with delete permissions cannot remove backups inside the immutability window.
- **Restrict who can modify the immutable copy's retention settings** as tightly as production
  access itself — that setting is the actual line between recoverable and gone.

**Done when:** at least one backup copy is offsite and cannot be deleted or shortened in
retention by the same credentials that manage production.

## 4. Encrypt backups and control who can restore them

A backup is a full copy of production data sitting somewhere, often with weaker access
controls than the production system it came from — that gap is a common source of breaches
that have nothing to do with the primary database being compromised.

- **Encrypt at rest with keys managed separately from the storage account**, so stealing the
  storage bucket alone is not enough to read the data.
- **Encrypt in transit** during both the backup and restore operations, not just at rest.
- **Scope restore permissions as tightly as production write access** — the ability to restore
  is the ability to overwrite live data, and it deserves the same review.

**Done when:** backups are encrypted with separately-managed keys, and the list of principals
who can trigger a restore matches the list who should have that authority.

## 5. Set retention against compliance and cost, explicitly

Retention that grows without a decision behind it becomes an unbounded storage bill and, in
regulated environments, a liability — data kept past its required lifetime is data that can be
subpoenaed or breached for no benefit.

| Tier | Typical retention | Driven by |
|---|---|---|
| Point-in-time / continuous | Hours to days | RPO for operational rollback |
| Daily snapshots | Weeks | Recovering from slower-to-notice errors |
| Long-term archive | Months to years | Compliance or legal hold requirement |

**Done when:** every retention tier has an explicit reason — an RPO, a compliance requirement,
or a cost tradeoff — rather than "we've just always kept it."

## 6. Document the restore procedure as a runbook

During an actual incident, the person restoring data is often not the one who built the
backup pipeline, and they are working under time pressure with people watching. A runbook
turns institutional knowledge into something anyone on-call can execute.

- **Write the exact steps and commands**, including how to select the right restore point,
  not just a link to the backup tool's general documentation.
- **State the expected duration** so whoever is running the incident can set expectations with
  stakeholders instead of guessing.

**Done when:** a restore runbook exists that a different engineer, not its author, has
successfully followed during a drill.

## Report

State the RPO and RTO for each dataset, the date and outcome of the last full restore drill,
and whether at least one backup copy is offsite and immutable. Name the honest gap — usually
a restore that has never been fully rehearsed, or a retention policy kept out of habit rather
than a stated requirement — rather than presenting backup coverage as proven.
