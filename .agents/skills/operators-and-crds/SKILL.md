---
name: operators-and-crds
description: Covers extending Kubernetes with CustomResourceDefinitions and controllers — the reconciliation pattern, a CRD as an API contract, why controllers must be level-triggered not edge-triggered, and when to build an operator versus buy one versus not bother. Use this whenever the user is designing a CRD's schema, writing a controller's reconcile loop, or evaluating an off-the-shelf operator. For the RBAC an operator's service account needs use `kubernetes-security`; for storage an operator manages use `kubernetes-storage`.
license: MIT
---

# Operators and CRDs

A CustomResourceDefinition extends the Kubernetes API with a new resource type; an operator is the
controller that watches instances of it and reconciles reality toward what's declared. Together
they let you express operational knowledge — "how to safely upgrade this database," "how to
provision this cloud resource" — as a Kubernetes-native API instead of a runbook a human executes by
hand. That's real leverage, and it's also a commitment: you're now maintaining a piece of
distributed systems software, not a script.

The value of an operator is entirely in how well it encodes the operational knowledge a human would
otherwise apply manually — a thin operator that just creates a Deployment isn't worth the
complexity. **Build an operator only when the reconciliation logic is genuinely nontrivial, not
because CRDs feel more "cloud native" than a ConfigMap.**

## 1. Design the CRD schema as a stable public API

A CRD's spec is a contract every consumer (humans, GitOps tooling, other controllers) writes
against. Changing field names or semantics after adoption is a breaking change exactly like an
external API's, and Kubernetes gives you real tools for this — use them, don't wing the schema.

- **Use `apiVersion` versioning (`v1alpha1` → `v1beta1` → `v1`) deliberately** — alpha/beta signal
  "may change," and only promote to a stable version once the schema has stopped shifting.
- **Validate with OpenAPI schema (`x-kubernetes-validation` / CEL rules) at the API server**, not
  just in the controller — rejecting a bad spec at `kubectl apply` time is far better UX than a
  reconcile loop silently failing later.
- **Status is not spec** — `status` reflects observed state and should only ever be written by the
  controller, never by the user; conflating the two is the most common CRD design mistake.

**Done when:** a consumer can write a valid custom resource from the schema and docs alone, without
reading the controller's source.

## 2. Write the reconcile loop to be level-triggered, not edge-triggered

Kubernetes controllers are built around the level-triggered pattern: reconcile is "given the current
observed state, make it match the desired state," runnable idempotently at any time, not "react to
this specific change event." Any controller that assumes it saw every event in order, or that skips
work because "nothing changed since last time" based on the event itself, will drift out of sync the
first time it misses an update — and it will miss updates, because that's normal operation
(restarts, watch reconnects, rate limiting).

```go
func Reconcile(ctx context.Context, req Request) (Result, error) {
    current := fetchActualState(req)
    desired := fetchSpec(req)
    if !equal(current, desired) {
        return applyDiff(current, desired) // safe to re-run from scratch, any time
    }
    return Result{}, nil
}
```

- **Re-running reconcile with no changes must be a safe no-op** — this is what makes periodic
  resync intervals (not just event-driven triggers) a correctness mechanism, not just a fallback.
- **Never rely on receiving every intermediate state** — only the current state and the last-seen
  state at reconcile time are guaranteed available.

**Done when:** the controller produces the same end state whether it processes every event
individually or is restarted and runs one reconcile against final state.

## 3. Buy before you build

An operator for Postgres, Redis, cert-management, or most other common infrastructure almost
certainly already exists, is battle-tested against failure modes you haven't hit yet, and is
maintained by people who will keep it working against new Kubernetes versions. Writing your own is
justified only when the operational logic is specific to your organization in a way no published
operator captures.

- **Evaluate maturity honestly**: CNCF graduation status, real production adoption, how the project
  handles CVEs and version support — not just GitHub stars.
- **A thin custom operator that wraps an existing one's CRD** to add your org's specific policy
  layer is often the right middle ground, rather than reimplementing the whole reconciliation logic.
- **Sometimes the answer is neither**: a scheduled Job or a CI pipeline step handles genuinely
  one-shot operational tasks better than a long-running controller watching for a rare event — see
  `scheduled-jobs` and `workflow-automation`.

**Done when:** you can name the specific gap an existing operator didn't cover, if you built one, or
name which existing operator you adopted instead of building.

## 4. Scope the operator's RBAC to exactly what it reconciles

An operator's service account typically needs broad-looking permissions (watch/create/update across
its managed resource types), which makes it a high-value target if compromised — the same
least-privilege discipline from `kubernetes-security` applies, but with an operator-specific twist:
scope by resource type and, where the operator supports it, by namespace, rather than granting
cluster-wide access because the CRD itself is cluster-scoped.

**Done when:** `kubectl auth can-i --list --as=<operator-sa>` shows only the resource types and
verbs the reconcile loop actually touches.

## 5. Handle finalizers so deletion is as safe as creation

If the operator provisions anything outside Kubernetes' own garbage collection (cloud resources,
external DNS records, data in another system), deleting the custom resource without a finalizer
orphans that external state permanently. A finalizer blocks deletion until the controller has
confirmed cleanup succeeded — skipping this is the most common way operators leak cost or create
dangling resources.

**Done when:** deleting a custom resource is verified to also clean up everything it provisioned
outside the cluster, or the finalizer blocks deletion until it does.

## Report

State whether the CRD's schema is versioned and validated, confirm the reconcile loop is idempotent
and level-triggered, name the build-vs-buy decision and its reasoning, the operator's actual RBAC
scope, and the finalizer/cleanup behavior on deletion. Call out any external resource the operator
provisions but doesn't yet clean up on deletion — naming that leak is more useful than calling
lifecycle management complete.
