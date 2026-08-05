---
name: stateful-workloads
description: Covers running stateful systems — databases, queues, search indexes — on Kubernetes, including StatefulSets and stable identity, durable storage, backup and failover built into the platform rather than bolted on, and the tradeoff between self-managing a stateful service and paying for a managed one. Use this whenever the user deploys a database or queue on Kubernetes, picks a StorageClass, debugs a pod that lost data on restart, or debates self-hosting versus managed. For volume mechanics use `kubernetes-storage`, and for restore discipline use `backup-and-restore`.
license: MIT
---

# Stateful Workloads

Kubernetes and most modern orchestration platforms were designed around the assumption that
any instance can be killed and replaced without consequence. That assumption is exactly wrong
for stateful systems — a database pod is not interchangeable with a fresh one, because the
data lives on that one pod's storage and nowhere else until you've deliberately made it
otherwise.

Running state on infrastructure built for stateless workloads works, but only if you actively
undo the platform's default assumptions: give the workload stable identity, give it storage
that outlives the pod, and give it a recovery story that does not depend on the pod ever
coming back the way it left.

**The platform will happily reschedule, evict, and recreate your stateful pod exactly like a
stateless one — unless you've told it not to, in writing, ahead of time.**

## 1. Use StatefulSets for identity, not for magic

A StatefulSet gives each pod a stable name, stable network identity, and a stable claim on its
own volume across restarts — that is the entire value it adds over a Deployment. It does not
make the workload stateful-aware, backed up, or replicated on its own.

- **Use ordinal, stable pod names and DNS** when the stateful system needs to know which
  member is which — cluster formation, primary election, and shard assignment all depend on
  identity that a Deployment's interchangeable pods cannot provide.
- **Do not expect a StatefulSet to handle replication, quorum, or failover logic** — that is
  the stateful application's own responsibility, or an operator's (see `operators-and-crds`)
  built specifically for that system.
- **Scale StatefulSets deliberately, not automatically** — adding or removing a stateful
  member usually requires a rebalance or resync that autoscaling logic knows nothing about.

**Done when:** each stateful pod has a stable identity the application actually depends on, not
just a default StatefulSet used out of habit for something that could be a Deployment.

## 2. Provision storage that survives the pod

The single most common way to lose data on Kubernetes is storage that is tied to the node
instead of the cluster — when the node dies, the data dies with it, regardless of how the pod
gets rescheduled.

- **Use a StorageClass backed by network-attached, replicated storage** for anything that must
  survive a node failure, not local/ephemeral volumes unless the application itself replicates
  data elsewhere. See `kubernetes-storage` for the volume provisioning mechanics.
- **Set the reclaim policy to Retain for critical data**, so a deleted PersistentVolumeClaim
  does not silently delete the underlying volume along with it.
- **Verify the storage's own durability and IOPS characteristics** match what the workload
  needs — a database on undersized network storage will show up as mysterious latency, not an
  obvious storage error.

**Done when:** a node failure or pod rescheduling event does not result in data loss, verified
by an actual test, not just the StorageClass configuration.

## 3. Build backup and failover into the platform, not bolted on

Treating backup and failover as an afterthought added after the workload is already running in
production means finding out they do not work at the worst possible time. Both need to be part
of the initial deployment, not a follow-up ticket.

- **Automate backups from day one**, using the mechanisms in `backup-and-restore`, rather than
  deferring backup setup until after the workload is handling real traffic.
- **Use an operator where one exists for the workload** (for Postgres, Kafka, Elasticsearch,
  and similar systems) — mature operators encode failover and backup logic that is genuinely
  hard to reproduce correctly by hand.
- **Test pod disruption explicitly** — cordon a node, delete a pod, force a rescheduling event
  — and confirm the stateful system recovers the way its documentation claims it will.

**Done when:** backup and failover have both been exercised against this specific deployment,
not assumed to work because the underlying software supports them in general.

## 4. Weigh self-managed against managed honestly

Running a database or queue yourself on Kubernetes is not free just because the compute is
"already there" — it trades a monthly bill for ongoing operational burden: patching, failover
tuning, backup verification, and being the one paged when it breaks at 3am.

- **Count the operational hours realistically**, not just the infrastructure cost, when
  comparing self-managed to a managed service — the comparison is rarely apples to apples if
  only compute cost is counted.
- **Self-manage when you need control the managed offering does not provide** — a specific
  extension, a topology the managed product does not support, or genuine cost at a scale where
  the math clearly favors it.
- **Default to a managed service for anything without a specific reason not to** — the
  operational discipline in this skill still applies to a managed offering's client-side
  configuration, but the hardest failure modes become someone else's job.

**Done when:** the self-managed-versus-managed decision for this workload is written down with
its actual reasoning, not left as an unexamined default.

## 5. Plan capacity before you are paged for it

Stateful systems degrade differently than stateless ones when they run out of room — a full
disk on a database can corrupt state or halt writes entirely, not just slow down under load.

- **Alert on storage growth trend, not just current usage**, so there is lead time to expand
  before a volume fills — see `capacity-planning` for the broader forecasting discipline.
- **Know whether the storage backend supports online expansion** before you need it; some
  StorageClasses require a pod restart or manual intervention to grow a volume.

**Done when:** storage headroom and growth rate are both visible on a dashboard, with an alert
before the volume is projected to fill.

## 6. Keep state out of things that do not need it

The most reliable way to reduce stateful operational burden is to have less state to operate.
Components that could be stateless but accumulate local state by accident inherit all of this
skill's obligations without anyone deciding they should.

- **Push session state, caches, and temp files to a dedicated stateful backend** rather than a
  local volume on an otherwise stateless service's pod.
- **Question any local PersistentVolumeClaim on a service that is not, in its core purpose, a
  stateful system** — it is often accidental scope creep rather than a real requirement.

**Done when:** every component with a PersistentVolumeClaim is listed with what state it holds and
why that state cannot live in a shared backend instead.

## Report

State which components are genuinely stateful, whether each uses an operator or hand-rolled
failover logic, and the result of the most recent disruption test (node failure, pod deletion).
Name the honest gap — usually a storage backend never tested against actual node failure, or a
self-managed-versus-managed decision that was never explicitly made — rather than presenting
the deployment as production-hardened.
