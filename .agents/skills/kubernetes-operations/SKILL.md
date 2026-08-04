---
name: kubernetes-operations
description: Covers running workloads through Kubernetes's control loop — requests/limits, liveness/readiness/startup probes, reading describe/events to debug CrashLoopBackOff, OOMKilled, Pending, or empty endpoints, safe rollouts and undo, and guardrails like PodDisruptionBudgets. Use this whenever the user is debugging a pod that won't start or keeps restarting, tuning probes or resource limits, or planning a rollout or rollback. For Service/Ingress traffic issues use `kubernetes-networking`; for scaling policy use `autoscaling`.
license: MIT
---

# Kubernetes Operations

Kubernetes does not execute your intent once — it continuously reconciles the cluster's actual
state toward your declared state, forever. Every operational problem is really a question about
that loop: what did you declare, what does the controller see, and where does the gap live. Most
outages trace back to a pod spec that never told the scheduler or kubelet what it actually needed.

The controller can only be as good as the information you give it — requests, limits, and probes
are not bureaucracy, they are the interface you use to talk to the control loop. **Debug by reading
what the control loop already told you, not by guessing.**

For a command-by-command debugging playbook and a table of pod failure signatures, read
`references/kubectl-debugging.md`.

## 1. Set requests as a promise, limits as a leash

Requests are what the scheduler uses to place a pod — they must reflect real steady-state usage or
you get either wasted nodes or overcommitted ones. Limits cap the ceiling and, for memory, define
the OOM-kill boundary; for CPU they cause throttling, not killing. Never set a memory limit without
a request, and never guess both from nothing — profile first.

- **CPU limits throttle, they don't fix**: a CPU limit that's too tight shows up as latency, not
  crashes, so check `kubectl top` and cgroup throttling stats before assuming code is slow.
- **Memory limits kill**: exceeding a memory limit is an immediate SIGKILL with reason `OOMKilled`,
  visible in `kubectl describe pod`.
- **QoS class follows from this**: requests == limits gets `Guaranteed`, which matters for eviction
  order under node pressure.

**Done when:** every container has a memory limit backed by observed usage, and CPU is only limited
if you've confirmed throttling is an acceptable tradeoff.

## 2. Separate what "alive" means from what "ready" means

Liveness, readiness, and startup probes answer three different questions and conflating them causes
the most common self-inflicted outage: a slow-starting app gets liveness-killed in a crash loop
because there's no startup probe to give it room, or a readiness probe that's really a liveness
check pulls healthy pods out of service during a blip.

- **Startup probe** protects slow boots — liveness/readiness don't start checking until it passes.
- **Liveness probe** should only fail for genuinely unrecoverable states (deadlock, corrupted
  internal state); a bad liveness probe causes crash loops that mask the real problem.
- **Readiness probe** should fail whenever the pod can't currently serve traffic — dependency down,
  cache warming — without killing the process.

**Done when:** a pod that's slow to boot doesn't get killed, and a pod with a failing dependency is
removed from Service endpoints without restarting.

## 3. Read describe and events before reading logs

`kubectl describe pod` surfaces the scheduler's and kubelet's own diagnosis in the Events section —
it is almost always faster than log-diving, because it tells you what Kubernetes itself couldn't
do, not what your application printed.

```bash
kubectl get pod <name> -o wide          # node, IP, restart count, phase
kubectl describe pod <name>             # Events: scheduling, pulls, probe failures, OOM
kubectl logs <name> --previous          # the crashed container's own output
```

- **`Pending`** with no node assigned: check Events for scheduling failures — insufficient
  resources, unsatisfied node affinity, or an unbound PVC (see `kubernetes-storage`).
- **`CrashLoopBackOff`**: the container is exiting; check `--previous` logs and exit code — 137 is
  SIGKILL (often OOM), 1 is an application error.
- **`ImagePullBackOff`**: registry auth or a typo'd tag — see `container-registry`.

**Done when:** you can state the exact Event line that explains the pod's state, not a guess.

## 4. Roll out like you expect to roll back

A rollout is not done when `kubectl apply` succeeds — it's done when the new ReplicaSet is fully
available and you've confirmed rollback works before you need it under pressure. `kubectl rollout
undo` only works cleanly if you haven't let revision history get truncated and if config changes
travel with the image tag, not around it.

- **Watch `kubectl rollout status`**, don't just fire-and-forget the apply.
- **Keep `revisionHistoryLimit`** high enough to actually roll back past a bad two-release window.
- **For anything riskier than a straight rolling update** — canary, blue/green — that's a delivery
  concern, not a cluster-ops one; see `deployment-strategies` and `progressive-delivery`.

**Done when:** you have run `kubectl rollout undo` at least once in a non-prod path and confirmed
it restores the prior working state.

## 5. Put guardrails in front of the humans, not behind them

PodDisruptionBudgets and securityContext exist because voluntary disruptions (node drains, cluster
autoscaler scale-downs) and misconfigured privilege are both preventable, not things to react to
after an incident.

- **PDB** stops a drain or autoscaler action from taking down every replica of a service at once —
  set `minAvailable` based on what quorum or capacity you can actually lose.
- **securityContext**: run as non-root, drop `ALL` capabilities and add back only what's needed,
  set `readOnlyRootFilesystem: true` where the app allows it. Deep hardening and cluster-wide policy
  belong in `kubernetes-security`.

**Done when:** every workload that can't tolerate losing all replicas at once has a PDB, and no
container runs as root without a documented reason.

## Report

State the requests/limits you set (and what usage data backed them), which probes you configured
and why each threshold was chosen, the exact Event or log line that diagnosed any failure you fixed,
and whether rollback was actually exercised. Call out any workload still missing a PDB or still
running as root — naming that gap is more useful than claiming the cluster is fully hardened.
