---
name: database-operations
description: Covers the operational discipline of running databases in production — connection pooling and exhaustion, online schema changes, replication topology and read scaling, failover and promotion, and the runbook habits that keep an outage from becoming data loss. Use this whenever the user is sizing a connection pool, adding an index to a live table, setting up read replicas, debugging replication lag, or planning a failover drill. For the step-by-step mechanics of a specific schema or data change use `data-migration`, and for restore testing use `backup-and-restore`.
license: MIT
---

# Database Operations

A database is the one component in most systems that cannot simply be redeployed when
something goes wrong — it holds state that no other system has a copy of. That changes the
math on every operational decision: a connection leak that would be a shrug in a stateless
service can take down every service sharing that database, and a "quick" index build can
lock a table your whole product depends on.

The job is not keeping the database running — it mostly runs itself. The job is making sure
every change to it, and every failure mode around it, has already been thought through before
it happens under pressure.

**Treat the database as the one thing you cannot roll back to a clean slate — every operation
against it should assume that.**

## 1. Treat the connection pool as a shared, finite resource

Every connection costs the database memory and a backend process, and the limit is far lower
than the number of application instances that want one. The default failure mode is each
service opening its own pool sized for its own convenience, and the sum quietly exceeding
what the database can hold.

- **Size pools from the database's max-connections budget backward**, divided across every
  service and environment that connects, not from a single service's guess at its own needs.
- **Use a connection pooler** (PgBouncer, ProxySQL, RDS Proxy) in front of the database when
  many short-lived clients connect, so the database sees a stable, small number of backends.
- **Alert on pool saturation before the database rejects connections**, since by the time
  connections are refused, requests are already failing.

**Done when:** the sum of every service's max pool size is known and stays under the
database's connection limit with headroom.

## 2. Make schema changes online by default

A migration that locks a table is a maintenance window nobody scheduled. Most modern
databases support adding columns, indexes, and constraints without blocking reads and writes,
but only if you use the online variant and avoid the naive one.

- **Build indexes concurrently** rather than with a default blocking build, even though the
  concurrent path takes longer and can fail partway, leaving an invalid index to clean up.
- **Add columns without a default value**, or with one the engine can apply without rewriting
  every row, and backfill the value separately in batches.
- **Never run an untested migration directly against production** — replay it against a
  production-sized copy first so lock duration and table rewrite time are known quantities.

For the full multi-phase pattern of changing a schema without downtime, including backfills
and dual-writes, see `data-migration` — this section is about the mechanics of one statement,
not the sequencing of a whole change.

**Done when:** the migration's lock behavior has been verified on a realistic data volume
before it runs against production.

## 3. Design replication for read scaling, not just redundancy

A replica that only exists for failover is doing half its job. Routing read-heavy traffic to
replicas takes load off the primary, but it only works if the application tolerates the
replication lag that comes with it.

- **Route reads that can tolerate slight staleness to replicas** — dashboards, reports, list
  views — and keep reads that must be immediately consistent on the primary.
- **Monitor replication lag as a first-class metric**, since an application silently reading
  stale data after a write is a correctness bug, not a performance quirk.
- **Know your replication topology** — single primary with async replicas is simplest; sync or
  quorum-based replication trades write latency for a stronger consistency guarantee.

**Done when:** every read query has a documented tolerance for staleness, and its target
(primary or replica) matches that tolerance.

## 4. Rehearse failover before you need it

A failover procedure that has only ever been diagrammed will surprise you the first time it
runs for real — DNS caches, stale connection pools, and application retry logic all behave
differently than the diagram assumed.

- **Run a scheduled failover drill** against a non-production or clearly-communicated
  production window, and time how long clients take to reconnect to the new primary.
- **Automate promotion where the tooling supports it** (Patroni, RDS Multi-AZ, Cloud SQL
  failover) so a 3am failover does not depend on someone remembering the manual steps.
- **Verify the application's retry and reconnect logic**, not just the database's promotion —
  a database that fails over cleanly still causes an outage if clients never notice.

**Done when:** a failover has been executed end to end, including client reconnection, within
the last quarter.

## 5. Watch leading indicators, not just uptime

By the time a database is down, it is too late to prevent the incident — the useful signals
are the ones that predict trouble minutes or hours ahead.

- **Long-running and idle-in-transaction sessions** hold locks and block vacuum/cleanup work;
  alert on their duration, not just their existence.
- **Lock wait time and queue depth** reveal contention before it becomes visible latency.
- **Disk growth rate**, not just current usage, gives you lead time to act before a full disk
  turns into an outage.

**Done when:** an alert exists for at least long-running transactions, lock contention, and
disk growth rate — not only for the database being unreachable.

## 6. Give every database a named owner and a runbook

A database with no owner accumulates configuration drift and unreviewed changes until someone
has to reverse-engineer it during an incident. Ownership is what makes the previous five
sections actually happen instead of staying aspirational.

- **Name a team or person responsible** for capacity, upgrades, and drills for each database.
- **Write down the connection topology, failover procedure, and backup schedule** somewhere
  the on-call engineer can find at 3am without asking anyone.

**Done when:** every production database has a named owner and a runbook that a different
engineer could follow unassisted.

## Report

State the connection pool budget and current headroom, the replication topology and its
measured lag, and the date of the last failover drill. Name the honest gap — usually a
failover procedure that has never been tested end to end, or an owner that exists on paper but
has not touched the database's runbook in months — rather than presenting the setup as
fully rehearsed.
