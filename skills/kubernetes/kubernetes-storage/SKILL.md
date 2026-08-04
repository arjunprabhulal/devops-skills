---
name: kubernetes-storage
description: Covers persistent data in the cluster — PersistentVolumes/Claims, StorageClasses and dynamic provisioning, access modes, StatefulSets, volume lifecycle, and reclaim policy so data survives rescheduling. Use this whenever the user is provisioning a PVC, choosing a StorageClass or access mode, running a stateful workload, or debugging a Pending PVC or stuck volume attach. For the database engine's own concerns use `database-operations`; for backup mechanics use `backup-and-restore`.
license: MIT
---

# Kubernetes Storage

Kubernetes was designed for stateless, disposable pods, and storage is the layer where that
assumption breaks down and has to be bolted back on carefully. A pod can be rescheduled to any node
at any time; the volume it depends on has to either follow it there or already be reachable from
there — get this wrong and a routine reschedule becomes a data-loss incident.

Treat every PVC as a promise about what happens when the pod above it dies, not just where the bytes
live today. **The reclaim policy and access mode you pick now decide what happens the day something
goes wrong, not the day it's created.**

## 1. Understand the claim as a request, not a guarantee

A PVC asks for a certain size, access mode, and StorageClass; the PV that satisfies it is either
pre-provisioned or, more commonly now, dynamically created by the StorageClass's provisioner. A
`Pending` PVC almost always means no StorageClass/provisioner can satisfy what was asked for —
capacity, access mode, or a zone constraint that doesn't match available storage.

```bash
kubectl get pvc <name>                       # Pending? check events
kubectl describe pvc <name>                  # provisioning failure reason
kubectl get storageclass                     # is the referenced class real, and is one default?
```

- **No default StorageClass** and no `storageClassName` specified means the PVC has nothing to bind
  to — this is a common first-cluster surprise.
- **Zonal mismatch**: many cloud provisioners create volumes in a specific zone; if the pod gets
  scheduled to a different zone, attachment fails even though the PV exists.

**Done when:** every PVC is `Bound`, or the Pending reason is identified from `describe`, not
guessed.

## 2. Match access mode to what the workload actually does

`ReadWriteOnce` (single node), `ReadWriteMany` (multiple nodes, needs a filesystem-based backend
like NFS/EFS/Filestore), and `ReadOnlyMany` are not interchangeable, and picking RWX by default
"just in case" often forces a slower, more expensive storage backend than the workload needs.

- **RWO is the default for databases** and most stateful apps — one pod owns the volume, which is
  also usually what you want for write consistency.
- **RWX is for genuinely shared access** — multiple pods writing/reading the same files
  concurrently (shared media, some ML pipelines) — and its backend is a real architectural choice,
  not a checkbox.
- **A ReadWriteOnceOd** volume (single pod, not just single node) is worth knowing about for
  workloads that must never have two writers even during a rolling update overlap.

**Done when:** the access mode matches a concrete concurrent-access requirement you can name, not
the most permissive option by default.

## 3. Use StatefulSets when identity matters, Deployments when it doesn't

The distinguishing feature of a StatefulSet isn't just stable storage — it's stable network identity
and ordered, one-at-a-time rollout. Reach for it specifically when pods are not interchangeable:
each replica needs its own persistent volume and a predictable hostname (database nodes, message
queue brokers), not just because the workload happens to write data.

- **`volumeClaimTemplates`** give each StatefulSet replica its own PVC, created and kept as pods are
  recreated — replica-2 always reattaches to replica-2's volume, not a random one.
- **Ordered rollout** (one pod at a time, waiting for Ready) is a feature, not a limitation, for
  workloads with quorum or leader-election semantics.
- **A stateless app that merely writes to a shared volume** doesn't need a StatefulSet — a
  Deployment with a single shared RWX-backed PVC, or better, no persistent local state at all, is
  simpler.

**Done when:** you can state why each replica needs its own identity-bound volume, or you've used a
Deployment instead.

## 4. Set reclaim policy on purpose, not by inheriting the StorageClass default

`Retain`, `Delete`, and (rarely) `Recycle` decide what happens to the underlying storage when the
PVC is deleted. Most dynamic StorageClasses default to `Delete` — convenient for ephemeral
workloads, catastrophic if it's silently deleting a production database's volume the moment someone
deletes the wrong PVC.

- **`Delete` for anything truly disposable** — CI scratch volumes, caches you can rebuild.
- **`Retain` for anything you cannot regenerate** — the volume survives PVC deletion and becomes
  `Released`, requiring manual intervention to reuse or clean up, which is the point: it forces a
  human decision instead of an automatic one.
- **This is not a backup strategy** — Retain prevents accidental deletion via the PVC lifecycle, it
  does nothing for corruption, node loss, or the underlying disk failing; see `backup-and-restore`
  for actual recovery guarantees.

**Done when:** every StorageClass backing non-disposable data is explicitly set to `Retain`, and
that decision is documented, not inherited by accident.

## 5. Assume the volume, not the pod, is what needs the reschedule guarantee

When a node fails, Kubernetes reschedules the pod elsewhere, but the volume has to actually be
detachable from the dead node and attachable to the new one — with `ReadWriteOnce` volumes and some
CSI drivers, this can stall for minutes waiting for a force-detach, which shows up as a pod stuck in
`ContainerCreating`.

- **Check CSI driver behavior for your platform** on ungraceful node loss — force-detach timeouts
  vary widely and directly determine your worst-case recovery time.
- **Don't assume local storage (hostPath, local PVs) survives rescheduling at all** — it's
  node-bound by definition; only use it when the workload's own replication handles node loss.

**Done when:** you know, for the specific CSI driver in use, how long a volume takes to reattach
after an ungraceful node failure.

## Report

State the StorageClass and access mode chosen and why, whether the workload needed a StatefulSet or
a Deployment sufficed, the reclaim policy set on each class, and any known reattachment delay on
node failure. Call out any PVC still relying on an inherited `Delete` policy for non-disposable data
— naming that risk is more useful than assuming the default was fine.
