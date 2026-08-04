# kubectl Debugging Playbook

The control loop always knows more than you do at the start of an incident. The scheduler and
kubelet already tried to do what you asked and left a record of why they couldn't — your job is to
read that record before you start guessing or log-diving.

## Contents

- The first four commands
- Pod state signatures
- Reading `describe` Events correctly
- Getting a shell when there isn't one
- Resource pressure
- Service has no endpoints: the selector-mismatch walkthrough

## The first four commands

Run these in order, every time, before forming a theory:

```bash
kubectl get pod <name> -o wide                 # node, IP, phase, restart count
kubectl describe pod <name>                    # Events: scheduling, pulls, probes, OOM
kubectl logs <name> --previous                 # the crashed container's own output
kubectl get events --sort-by='.lastTimestamp'  # cluster-wide, chronological
```

- `-o wide` first because restart count and node assignment already narrow the search — a pod
  bouncing between nodes points at resource pressure or taints, not app code.
- `describe` before `logs` because Kubernetes' own diagnosis (Events) is usually faster to read
  than an application's stack trace, and it catches failures that never produced a log line at all
  (ImagePullBackOff, FailedScheduling).
- `logs --previous` because the current container may be a fresh restart with nothing useful yet —
  the crash you care about is in the previous instance.
- `get events --sort-by='.lastTimestamp'` when the problem isn't scoped to one pod, or when
  `describe`'s event list has already scrolled past the root cause. Namespace-scope it
  (`-n <ns>`) or you'll drown in noise.

## Pod state signatures

| State | Signature | Common cause | Fix |
|---|---|---|---|
| `CrashLoopBackOff` | Restart count climbing, `Back-off restarting failed container` in Events | App exits on start; exit code 137 = SIGKILL (often OOM), exit code 1 = app error | Read `logs --previous`; if 137, check memory limit vs actual usage; if 1, fix the app or its config/env |
| `OOMKilled` | `describe pod` shows `Last State: Terminated, Reason: OOMKilled`, exit code 137 | Container exceeded its memory limit | Raise the limit against profiled usage, or fix a leak — don't raise the limit blind |
| `ImagePullBackOff` / `ErrImagePull` | Events show `Failed to pull image`, `pull access denied`, or `manifest unknown` | Typo'd tag, private registry without imagePullSecrets, or registry rate limit | Verify the tag exists, check `imagePullSecrets`, see `container-registry` |
| `Pending` | Pod never gets a node, no `Started` event | Scheduler can't place it: insufficient CPU/memory on any node, unsatisfied node affinity/taint, or an unbound PVC | `describe pod` Events show the exact scheduling failure; check `kubectl get nodes` capacity and `kubectl describe pvc` |
| `CreateContainerConfigError` | Pod stuck before containers even start, Events show `Error: configmap "x" not found` or similar | Referenced ConfigMap, Secret, or key doesn't exist in the namespace | `kubectl get configmap/secret <name> -n <ns>`; fix the reference or create the missing object |
| `Init:Error` / `Init:CrashLoopBackOff` | Pod stuck at `Init:N/M`, main containers never start | An init container is failing — check it independently, it has its own logs | `kubectl logs <name> -c <init-container-name> --previous`; init containers run to completion, so any nonzero exit blocks the pod forever |

## Reading `describe` Events correctly

Events are ordered oldest to newest and each has a `Reason` field that's more reliable than the
free-text `Message` — grep for `Reason` when scripting, read `Message` when reading by eye:

```bash
kubectl describe pod <name> | sed -n '/^Events:/,$p'
```

- **Multiple events with the same Reason and a growing count** (e.g. `Back-off pulling image` x12)
  means the condition is persistent, not transient — don't wait it out.
- **`FailedScheduling`** always states the specific predicate that failed: `Insufficient cpu`,
  `node(s) had untolerated taint`, `node(s) didn't match Pod's node affinity/selector`. Copy that
  line verbatim into your diagnosis; don't paraphrase it.
- **`Unhealthy`** with `Liveness probe failed` vs `Readiness probe failed` tells you which of the
  two probes to look at — see SKILL.md section 2 if the wrong one is configured to do the other's
  job.
- If Events is empty or stale, the kubelet may not be reporting — check node status directly
  (`kubectl get nodes`, `kubectl describe node <node>`) before assuming the pod spec is the problem.

## Getting a shell when there isn't one

Distroless and minimal images often have no shell, no `curl`, nothing to exec into. Use an
ephemeral debug container instead of rebuilding the image with debug tools baked in:

```bash
# Attach a throwaway debug container to a running pod, sharing its network namespace
kubectl debug -it <pod> --image=nicolaka/netshoot --target=<container>

# Same idea for a Pending pod that never scheduled: create a copy with a shell for inspection
kubectl debug -it <pod> --image=busybox --copy-to=<pod>-debug --container=<container> -- sh

# Debug a node itself (privileged host access) when the problem might not be pod-scoped
kubectl debug node/<node> -it --image=busybox
```

- `--target` shares the target container's process namespace so you can see its processes and
  network from the debug container — this is the difference between poking at the pod and poking
  at empty air next to it.
- `--copy-to` is for pods that never started (Pending, CreateContainerConfigError) where there's no
  running container to attach to — it creates a new pod from the same spec plus your debug
  container.

## Resource pressure

```bash
kubectl top pod <name> --containers    # current CPU/memory vs requests/limits
kubectl top node                       # is the node itself out of capacity
```

- `kubectl top` needs metrics-server running in-cluster — if it returns nothing, that's the first
  problem, not an empty result.
- Compare `top` output against the container's own `requests`/`limits` from `describe pod`, not
  against gut feel — a container sitting at 95% of its memory limit will OOM on the next spike even
  though nothing looks "wrong" right now.
- For CPU, `top` won't show throttling directly — a container can be far under its limit in
  instantaneous usage and still be throttled in bursts. Check `container_cpu_cfs_throttled_seconds_total`
  in Prometheus/cAdvisor if latency is the symptom and `top` looks fine.

## Service has no endpoints: the selector-mismatch walkthrough

Symptom: traffic to a Service times out or connection-refuses, but the pods behind it look healthy.

```bash
kubectl get endpoints <service>                       # empty ADDRESSES column is the tell
kubectl get svc <service> -o jsonpath='{.spec.selector}{"\n"}'
kubectl get pods -l <same-key>=<same-value> --show-labels   # does this actually match anything?
```

Walk it in this order:

1. **`get endpoints <service>`** — if the `ENDPOINTS` column is empty or `<none>`, the Service has
   zero backing pods right now, full stop. This is the fastest possible confirmation that the
   problem is selector/readiness, not network policy or DNS.
2. **Compare the Service's `spec.selector` to the pod's actual labels** — the single most common
   cause is a typo or a label that changed during a refactor (`app` vs `app.kubernetes.io/name`,
   or a version label like `version: v2` left in the selector after a rollout moved pods to `v3`).
3. **If labels do match, check readiness** — `kubectl get pods -l <selector> -o wide` and look at
   `READY`. A Service only includes pods that are passing their readiness probe; a pod stuck at
   `0/1` ready is excluded from endpoints even with a perfect label match. This is often the
   readiness-vs-liveness confusion from SKILL.md section 2: a readiness probe that's too strict, or
   checking a dependency that's actually down.
4. **If it's a headless Service or you expected multiple backends**, confirm `spec.ports[].targetPort`
   actually matches a port the container listens on — a Service can have matching, ready pods and
   still misroute if the target port is wrong, though that shows up as connection-refused rather
   than empty endpoints.

**Fix is almost always one of:** correct the selector to match real labels, fix the label on the
pod template (then roll the Deployment), or fix whatever readiness probe condition is failing.
