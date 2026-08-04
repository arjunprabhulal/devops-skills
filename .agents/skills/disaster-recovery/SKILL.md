---
name: disaster-recovery
description: Prepares a system to survive a total, catastrophic failure — a lost region, a corrupted database, a deleted cloud account — through defined RTO/RPO targets, backups that have actually been restored, and tested failover, not a backup cron job someone set up once. Use this whenever the user asks about disaster recovery, region failover, RTO or RPO, "what if we lost the whole database," or is designing for a failure bigger than a single pod. For live coordination once disaster strikes use `incident-response`; for backup/restore mechanics use `backup-and-restore`.
license: MIT
---

# Disaster Recovery

Most reliability work assumes the system is basically intact — a pod crashed, a node drained,
traffic spiked. Disaster recovery assumes it is not: the region is gone, the primary database
is corrupted, someone ran the wrong migration against production. This is a different design
problem, and treating it as "just bigger backups" is how organizations discover, mid-disaster,
that their backups don't actually restore.

A backup you have never restored is not a backup — it is an unverified belief. The only thing
that counts as disaster recovery is a *tested* path from "everything is gone" to "the business
is running again," with a number attached to how long that takes.

**A backup you haven't restored is a hope, not a plan.**

## 1. Set RTO and RPO before you design anything

Recovery Time Objective (how long you're down) and Recovery Point Objective (how much data you
can lose) are business decisions, not engineering ones — and they should come from someone who
owns the cost of downtime, not from whatever the backup tool defaults to. Every architecture
choice downstream — backup frequency, standby infrastructure, failover automation — is a
direct consequence of these two numbers.

| Target | Drives |
|---|---|
| RTO (time to recover) | Standby infra, automation level, runbook complexity |
| RPO (data loss tolerance) | Backup/replication frequency, write durability |

- **Different systems can have different targets** — the payments database and the internal
  wiki do not need the same RTO.
- **A tight RTO without a tested failover path is fiction** — don't let a number on a slide
  substitute for a rehearsed procedure.
- **Revisit targets when the business changes**, not on a fixed schedule alone — a new region,
  a new compliance requirement, or new revenue exposure all move the number.

**Done when:** every critical system has an explicit, business-approved RTO and RPO written
down, not implied.

## 2. Restore from backup on a schedule, not on faith

The only valid test of a backup is restoring it into a working environment and verifying the
data is actually usable. Backup jobs fail silently constantly — permissions drift, storage
fills, encryption keys rotate and break decryption, schemas change and the restore script
doesn't know about the new table. None of that shows up as a red X in the backup dashboard.

- **Automate a periodic restore-and-verify**, not just a backup — restore into an isolated
  environment and run a real query or checksum against it.
- **Alert on restore failure as loudly as on backup failure** — a silent restore failure is
  the worst possible time to discover it.
- **Test restoring to a different account/region than the backup lives in** — a backup that
  only restores where it was taken doesn't help if that whole account is the thing you lost.

**Done when:** the last successful, verified restore test is recent enough that you'd trust it
during a real disaster.

## 3. Design failover for the thing you're actually afraid of

Failover architecture should match the failure mode you're protecting against — region loss,
cloud provider outage, a bad actor with delete permissions. A hot standby in the same region
doesn't help against a regional outage; a nightly snapshot doesn't help against ransomware
that's been quietly encrypting data for two weeks before anyone notices.

- **Active-passive** buys you a known-simple recovery path at the cost of idle standby spend.
- **Active-active** buys you near-zero RTO at the cost of real complexity in data consistency
  — see `multi-cloud` and `cloud-networking` for the networking implications.
- **Immutable, offline, or delayed-deletion backups** are the only real defense against
  credential compromise or accidental mass-deletion — a backup an attacker with your cloud
  credentials can also delete is not a disaster recovery plan against that attacker.

**Done when:** the chosen failover pattern is matched, on paper, to a named failure scenario
it's meant to survive.

## 4. Run the drill as if it's real

A DR drill announced a week in advance, run by the person who built the system, tested against
a system everyone already knows is about to be tested, tells you nothing about whether
recovery works under real conditions. The value of the drill is entirely in how close it comes
to the surprise and confusion of the real thing.

- **Rotate who runs the drill** — if only the architect can execute the failover, the plan
  doesn't survive their vacation.
- **Time it end-to-end** against the stated RTO, and treat a miss as a finding, not a
  footnote.
- **Include the boring parts** — DNS cutover, cert reissuance, dependent service
  reconfiguration — these are where real recoveries actually stall, not the database restore
  itself.

**Done when:** a DR drill has been run within the target window by someone other than the
system's primary owner, and it hit the stated RTO.

## 5. Document the recovery plan for the state you'll actually be in

During a real disaster, the wiki might be down too — if the DR plan lives only in the same
system that just failed, it's inaccessible exactly when needed. Write it like a `runbooks`
entry: concrete, ordered, and reachable from outside the blast radius.

- **Store the plan somewhere independent of the primary infrastructure** — a different cloud
  account, a printed copy, a separate provider entirely.
- **Include access recovery**, not just data recovery — who can grant emergency credentials if
  the identity provider is also down.
- **Name explicit decision owners** for triggering failover — "declare disaster" is a judgment
  call that needs an authorized human, not an automatic threshold alone.

**Done when:** the recovery plan is accessible and executable even if the primary environment,
including its docs and identity provider, is completely unreachable.

## Report

State the RTO/RPO for the systems in scope, when the backups were last restore-tested and what
that test verified, and when the last full failover drill happened and whether it met the
target. Name explicitly which systems still have untested backups or an unrehearsed failover
path — an unverified DR plan is the single most expensive thing to discover is broken only
during the actual disaster.
