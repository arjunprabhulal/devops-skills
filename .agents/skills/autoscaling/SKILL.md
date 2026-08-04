---
name: autoscaling
description: Covers scaling Kubernetes workloads and nodes to demand — HPA on the right metric, VPA, cluster autoscaler, custom/external metrics, avoiding thrash with stabilization windows, and requests as the foundation underneath it all. Use this whenever the user is configuring an HPA, deciding between HPA and VPA, debugging autoscaling that flaps, or sizing a cluster autoscaler. For the requests/limits autoscaling depends on use `kubernetes-operations`; for cost tradeoffs use `cost-optimization`.
license: MIT
---

# Autoscaling

Autoscaling in Kubernetes is a control loop stacked on a control loop: the HPA watches a metric and
adjusts replica count, the scheduler places those replicas, and the cluster autoscaler watches for
unschedulable pods and adds nodes. Every layer depends on the one below reporting truthfully — an
HPA scaling on a metric that doesn't reflect real load, or replicas whose requests don't reflect
real usage, produces scaling decisions that look active but don't fix anything.

Autoscaling amplifies whatever signal you point it at — a good signal gives you elastic capacity, a
bad one gives you expensive noise. **Get requests right first; every autoscaler downstream is only
as accurate as the numbers it's reading.**

## 1. Scale on the metric that actually predicts saturation

CPU utilization is the default HPA metric because it's always available, not because it's usually
the right one. A queue-processing service saturates on queue depth; an API saturates on
request latency or in-flight requests; a memory-bound service doesn't reflect load in CPU at all.
Scaling on the wrong metric means the HPA reacts late or not at all to the thing that's actually
hurting users.

- **CPU/memory (`autoscaling/v2` resource metrics)** work when the workload's bottleneck genuinely
  is CPU or memory — verify this, don't assume it.
- **Custom and external metrics** (via a metrics adapter — Prometheus Adapter, KEDA, cloud-provider
  metrics) let you scale on queue depth, request rate, or a business metric — worth the setup cost
  when the resource metrics don't correlate with actual saturation.
- **Target utilization should leave headroom** for the scale-up lag — if pods take 30s to become
  Ready, targeting 90% CPU means you're already in trouble before new replicas can help.

**Done when:** the HPA's target metric has been checked against real saturation data, not chosen by
default.

## 2. Don't run HPA and VPA on the same metric for the same workload

HPA changes replica count; VPA changes each replica's requests/limits. Pointed at the same resource
dimension on the same workload, they fight — VPA resizing a pod's CPU request changes the value
HPA's percentage target is computed against, producing scaling decisions neither system intended.

- **HPA for horizontal, request-driven load** — the normal case for stateless services that can add
  replicas to absorb more traffic.
- **VPA for right-sizing requests over time**, especially for workloads that can't scale
  horizontally (a single-writer StatefulSet member) or where initial request values were guessed —
  VPA in recommendation-only mode is a safe way to gather that data before trusting it to auto-apply.
- **If both are needed**, split dimensions: VPA on memory, HPA on a custom/CPU metric, or run VPA in
  `Off`/recommend mode and apply its suggestions manually on a schedule.

**Done when:** no workload has both HPA and VPA actively adjusting the same resource dimension
simultaneously.

## 3. Give the HPA a stabilization window before you trust its behavior

Reactive scaling without dampening thrashes: a load spike triggers scale-up, the spike passes,
replicas scale back down, then the next spike scales up again — each transition has cost (new pod
startup time, connection draining) that adds latency and instability for users riding through it.

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300   # require 5 min of sustained low load before scaling down
  scaleUp:
    stabilizationWindowSeconds: 0     # scale up fast, scale down cautiously
```

Asymmetric stabilization — fast up, slow down — is usually the right default: the cost of scaling up
a beat late is worse than the cost of carrying a few extra replicas for a few more minutes.

**Done when:** replica count graphed over a real traffic day shows smooth transitions, not a sawtooth.

## 4. Remember the cluster autoscaler is scaling nodes, not pods

HPA can request more replicas than the cluster has room for; the cluster autoscaler only adds nodes
in response to pods that are actually `Pending` due to insufficient resources — it does not look
ahead. That gap between "HPA wants 10 more replicas" and "nodes exist to run them" is exactly where
users experience the worst of an unhandled spike.

- **Node provisioning takes real minutes**, not seconds — for latency-sensitive spiky workloads,
  consider over-provisioning a small buffer (placeholder pods that get evicted first) rather than
  relying purely on reactive node scale-up.
- **Pod requests must be schedulable on some node type** the cluster autoscaler can actually add —
  a request shape (e.g. huge memory, tiny CPU) that doesn't match any available instance type will
  stay Pending forever, autoscaler or not.
- **Bin-packing and node group choice** affect both cost and scale-up latency — that tradeoff is
  covered from the cost angle in `cost-optimization` and `rightsizing`.

**Done when:** you've confirmed, under a load test, that the cluster autoscaler actually adds
capacity fast enough for the workload's real spike shape.

## 5. Never autoscale on top of wrong requests

Every HPA percentage target and every cluster autoscaler bin-packing decision is computed relative
to the pod's requests. If requests were copy-pasted from another service or set once years ago,
"scale at 70% CPU" is scaling at 70% of a fictional number — the autoscaler will be confidently
wrong.

**Done when:** the requests underneath every autoscaled workload have been validated against
observed usage within the last release cycle, not inherited indefinitely.

## Report

State which metric each HPA scales on and why it was chosen over CPU-by-default, whether HPA and VPA
overlap on any workload, the stabilization windows set, and whether cluster autoscaler capacity was
validated against a real spike. Call out any workload still autoscaling against unverified or stale
requests — naming that gap is more useful than reporting the scaling policy as tuned.
