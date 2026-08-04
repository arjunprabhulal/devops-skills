---
name: multi-tenancy
description: Covers safely sharing a Kubernetes cluster across teams or customers — namespace isolation, ResourceQuota and LimitRange, NetworkPolicy tenant boundaries, per-tenant RBAC, noisy-neighbor control, and soft versus hard multi-tenancy. Use this whenever the user is onboarding a team onto a shared cluster, setting quotas per namespace, or debugging one tenant starving another's resources. For RBAC verbs and admission hardening use `kubernetes-security`; for isolation mechanics use `kubernetes-networking`.
license: MIT
---

# Multi-Tenancy

A namespace is an organizational boundary in the Kubernetes API, not a security or resource
boundary by itself. Left alone, tenants in different namespaces on the same cluster can still see
each other's Services via DNS, exhaust shared node capacity, and — depending on RBAC — read each
other's resources entirely. Multi-tenancy is the work of turning that organizational boundary into
an actual isolation boundary, one control at a time.

Decide up front how much isolation each tenant actually needs, because that decision changes
everything downstream — quotas, network policy, and whether namespaces are even enough.
**Namespaces are the unit of ownership; isolation has to be built on top of them deliberately.**

## 1. Decide soft or hard multi-tenancy before you provision anything

Soft multi-tenancy assumes tenants are mutually trusted (different teams in the same org) and
namespaces plus quotas/RBAC are sufficient. Hard multi-tenancy assumes tenants are mutually
untrusted (external customers, regulated separation requirements) and needs isolation namespaces
can't provide alone — separate node pools, or separate clusters entirely, because a shared kernel
and shared control plane are themselves an attack surface between untrusted tenants.

- **Soft tenancy**: namespace-per-tenant + ResourceQuota + RBAC + NetworkPolicy is a legitimate,
  well-trodden pattern.
- **Hard tenancy**: needs kernel-level isolation (dedicated nodes via taints/tolerations, or gVisor
  /Kata sandboxing) at minimum, and often separate clusters — the blast radius of a container
  escape or control-plane compromise has to stop at the tenant boundary.
- **This decision drives cost directly** — hard tenancy's dedicated infrastructure is real spend;
  see `cost-optimization` for that tradeoff once the isolation requirement is fixed.

**Done when:** the tenancy model is written down as a decision (soft or hard) with the trust
assumption that justifies it, not left implicit.

## 2. Give every tenant a ResourceQuota before their first workload

Without a ResourceQuota, one tenant's runaway Deployment can consume all schedulable capacity on
shared nodes, starving every other tenant — this is the single most common multi-tenancy incident
and it's entirely preventable with a quota set at namespace creation, not after the first incident.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: team-a
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    pods: "50"
```

- **Quota on both requests and limits** — requests-only quota still lets a tenant's limits balloon
  unboundedly, hurting burst headroom for everyone else.
- **Pair with a `LimitRange`** so pods that specify no resources at all get sane per-container
  defaults instead of being unbounded — a missing request in a quota-bound namespace fails to
  schedule confusingly otherwise.

**Done when:** every tenant namespace has both a ResourceQuota and a LimitRange applied before the
first workload is deployed into it.

## 3. Isolate tenants at the network layer explicitly

Kubernetes' flat pod network means, absent NetworkPolicy, every tenant can reach every other
tenant's pods by IP or Service DNS regardless of namespace boundaries. This is the same
default-deny pattern covered in `kubernetes-networking`, applied specifically per-tenant: each
tenant namespace gets a default-deny policy plus explicit allows only for its own traffic and
whatever shared platform services (ingress controller, DNS, observability agents) it legitimately
needs.

- **Default-deny cross-namespace by default**, then allow only named exceptions — never the
  reverse.
- **Shared platform services need their own explicit allow rules** in every tenant namespace, or
  onboarding a policy will silently break logging/metrics agents.

**Done when:** a pod in one tenant's namespace cannot reach a pod in another tenant's namespace
except through an explicitly allowed, documented path.

## 4. Scope RBAC per tenant, and don't let cluster-scoped resources leak across

Namespaced RBAC (Role + RoleBinding) keeps a tenant's permissions inside their own namespace, but
cluster-scoped resources — CustomResourceDefinitions, StorageClasses, ClusterRoles, some CRD
instances themselves — aren't namespace-bound and need a separate answer, usually a platform team
owning them exclusively and tenants only referencing them, not modifying them.

- **No tenant gets `ClusterRole` bindings** unless the resource genuinely requires cluster scope and
  the tenant is trusted for it — this repeats the least-privilege rule from `kubernetes-security`
  but is worth re-checking specifically at tenant onboarding time, since it's the easiest guardrail
  to skip under time pressure.
- **Admission policy (OPA/Kyverno) can enforce naming/labeling conventions per tenant** so quota and
  network policy selectors stay reliable as tenants scale beyond what manual review can track.

**Done when:** no tenant's service account or user role has cluster-scoped write access.

## 5. Control noisy neighbors beyond just CPU/memory quota

Quota bounds compute, but shared control-plane resources — API server request rate, etcd write
throughput, DNS query volume — aren't covered by ResourceQuota at all, and one tenant's
misbehaving controller or CRD watch loop can degrade the API server for everyone on the cluster.

- **API Priority and Fairness (APF)** lets you isolate tenant request flows so one tenant's
  API-hammering client doesn't starve others' `kubectl` responsiveness.
- **Watch for a tenant's controller/operator** (see `operators-and-crds`) doing excessive reconciles
  — this is a common, easy-to-miss source of control-plane load in shared clusters.

**Done when:** you've confirmed no single tenant's workload can degrade API server responsiveness
for other tenants, either by APF configuration or by architectural separation.

## Report

State the tenancy model chosen (soft or hard) and the trust assumption behind it, the quota and
LimitRange applied per tenant, the NetworkPolicy default-deny posture, and whether any tenant holds
cluster-scoped RBAC. Call out any shared control-plane resource (API server, etcd, DNS) still
unprotected against one tenant's excess load — naming that shared-fate risk is more useful than
declaring tenants fully isolated.
