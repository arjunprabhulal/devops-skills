---
name: kubernetes-networking
description: Explains how traffic reaches and moves between pods — Services (ClusterIP/NodePort/LoadBalancer), Ingress and controllers, cluster DNS, NetworkPolicy default-deny, and debugging selector mismatches or empty endpoints. Use this whenever the user asks why a Service has no endpoints, why a request 502s inside the cluster, how to expose an app externally, or how to write a NetworkPolicy. For readiness-driven endpoint removal use `kubernetes-operations`; for mTLS at L7 use `service-mesh`.
license: MIT
---

# Kubernetes Networking

Every networking problem in Kubernetes is a chain: client → DNS → Service → Endpoints → pod IP →
container port. When something doesn't connect, the fix is to walk that chain in order instead of
guessing at layer seven first. Most "the app is broken" tickets are actually a label selector typo
two links up the chain.

Services are not load balancers in the traditional sense — they're a label query that produces a
list of IPs, continuously recomputed. **If a Service has no endpoints, nothing downstream matters
yet.**

## 1. Check endpoints before you check anything else

`kubectl get endpoints <svc>` (or `endpointslices`) tells you immediately whether the Service's
selector is matching any Ready pods. An empty list is the single most common root cause of
"connection refused" or 502s inside the cluster, and it's a one-command diagnosis.

```bash
kubectl get svc <name> -o yaml | grep -A3 selector
kubectl get pods --show-labels -l <same-selector>
kubectl get endpoints <name>
```

- **Selector typo or label drift**: the Service's `selector` must exactly match pod labels — a
  deploy that changed a label without updating the Service breaks silently.
- **No Ready pods**: a pod can be Running but not Ready, and not-Ready pods are excluded from
  endpoints by design — check readiness probes, covered in `kubernetes-operations`.
- **containerPort mismatch**: the Service's `targetPort` must match what the container actually
  listens on, not just what's documented.

**Done when:** `kubectl get endpoints` shows the expected pod IPs, or you've identified exactly why
it doesn't.

## 2. Pick the Service type for the audience, not the convenience

`ClusterIP` is the default and correct choice for anything internal — don't expose things
externally because `LoadBalancer` was easier to type. Each type answers a different "who can reach
this": ClusterIP is cluster-internal, NodePort exposes a port on every node (rarely what you want in
production), LoadBalancer provisions a cloud LB per Service (expensive at scale), and Ingress is the
only one built to multiplex many HTTP services behind one entrypoint.

- **Default to ClusterIP** and put Ingress in front for anything HTTP(S) that needs external access.
- **LoadBalancer per Service** doesn't scale cost-wise past a handful of services — that's what
  Ingress controllers and, if you need L4 too, an `api-gateway` are for.
- **headless Services** (`clusterIP: None`) exist for direct pod-to-pod discovery, notably
  StatefulSets — see `kubernetes-storage`.

**Done when:** you can justify why this specific Service type was chosen over ClusterIP+Ingress.

## 3. Treat the Ingress controller as the thing that actually terminates traffic

An `Ingress` object is only routing rules; nothing happens without a controller (nginx, ALB, Envoy,
etc.) actually watching and programming a proxy. Debugging Ingress means checking both layers: is
the rule correct, and did the controller's proxy actually reload with it.

- **Path and host rules** are matched by the controller's implementation, not a universal spec —
  regex support, path type strictness, and default-backend behavior differ by controller.
- **TLS termination** usually happens at the controller; check the controller's logs, not the
  application's, when TLS handshakes fail.
- **Annotations are controller-specific** — an nginx annotation silently does nothing on an ALB
  controller.

**Done when:** you've confirmed the controller's own logs show the rule was accepted and programmed.

## 4. Don't debug DNS by trusting the client's resolver blindly

Cluster DNS (CoreDNS) resolves `<service>.<namespace>.svc.cluster.local`, and most failures are
either a wrong namespace assumption, CoreDNS pods under resource pressure, or `ndots`-driven
search-domain amplification making every external lookup try five suffixes first.

- **Cross-namespace lookups** need the namespace qualifier — `myservice` alone only resolves within
  the calling pod's own namespace.
- **`ndots:5` default** means a single-label external hostname triggers multiple failed internal
  lookups before succeeding — a real latency cost for chatty external calls.
- **Test from inside**, not outside: `kubectl exec` into a pod and run `nslookup`/`getent hosts`
  against the actual in-cluster resolver.

**Done when:** a DNS failure is traced to CoreDNS health, search-domain config, or the actual record
— not assumed.

## 5. Default-deny NetworkPolicy, then open explicit holes

With no NetworkPolicy, every pod can reach every other pod in the cluster — that's the insecure
default. The pattern that actually works is a namespace-wide default-deny, then narrow allow rules
per legitimate traffic path, because allow-only-what-you-list is the only version of this that
degrades safely when someone forgets a rule.

- **Default-deny both directions** (`policyTypes: [Ingress, Egress]`) — an ingress-only deny still
  lets a compromised pod exfiltrate freely.
- **Label pods and namespaces deliberately** — NetworkPolicy selectors depend entirely on label
  hygiene; unlabeled pods silently fall outside intended rules.
- **NetworkPolicy requires a CNI that enforces it** — Flannel in its default mode does not; verify
  the cluster's CNI actually implements policy before trusting one exists.

**Done when:** a default-deny policy is in place per namespace and every legitimate path has an
explicit allow rule you can name.

## Report

State the Service types in use and why, whether endpoints were empty and what fixed it, which layer
a DNS or Ingress failure was actually traced to, and the current NetworkPolicy posture (default-deny
or open). Call out any namespace still without a NetworkPolicy — naming that open surface is more
useful than implying the cluster is segmented when it isn't.
