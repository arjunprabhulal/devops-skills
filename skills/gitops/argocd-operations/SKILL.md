---
name: argocd-operations
description: Covers running Argo CD day to day — structuring app-of-apps, choosing sync policies and waves, reading health versus sync status correctly, and unsticking a degraded or hung Application. Use this whenever the user mentions Argo CD, an Application stuck "Progressing" or "OutOfSync," app-of-apps or ApplicationSets, sync waves and hooks, or asks why a deploy shows synced but the workload is unhealthy. For the underlying model this tool implements use `gitops`; for automated canary analysis on top of it use `progressive-delivery`; for the workloads it manages use `kubernetes-operations`.
license: MIT
---

# Argo CD Operations

Argo CD is the reconciler that makes `gitops` real, but knowing the GitOps model doesn't tell you
how to structure hundreds of Applications, order their rollout, or figure out why one has been
"Progressing" for twenty minutes. Most Argo CD pain is operational, not conceptual: a bad sync wave
ordering, a health check that will never pass, or a manual sync habit that defeats the point of
having a reconciler at all.

**Sync status tells you if the repo and cluster match; health status tells you if what's running
actually works — treat them as two separate questions.**

For stuck-sync states, sync waves, and the `argocd app` command reference, read
`references/argocd-troubleshooting.md`.

## 1. Manage many Applications with app-of-apps or ApplicationSets

Once you have more than a handful of Applications, don't create and wire each one by hand. A root
"app of apps" Application whose only job is to manage child Application manifests gives you one
commit to add a new service everywhere it belongs. ApplicationSets go further, generating
Applications from a template plus a generator (a Git directory list, a cluster list, a pull request
list) — use them when the same shape of Application needs to exist per-cluster or per-environment.
Reserve hand-written Applications for the genuinely one-off cases.

**Done when:** onboarding a new service to an existing environment pattern is one small commit, not
a manual `argocd app create`.

## 2. Order dependencies explicitly with sync waves, don't hope

Argo CD syncs everything in an Application concurrently by default, which breaks when a Deployment
needs a CRD, ConfigMap, or Secret to exist first. Sync waves (`argocd.argoproj.io/sync-wave`
annotations) give you explicit, numbered ordering — negative waves for CRDs and namespaces, zero for
core resources, positive for anything that depends on them. Resource hooks (PreSync, PostSync,
SyncFail) exist for genuinely imperative steps like a database migration, but every hook is a small
admission that the desired state isn't fully declarative, so keep them rare and idempotent.

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-1"   # applied before wave 0 resources
```

**Done when:** a full sync from empty succeeds in one pass with no manual re-sync required.

## 3. Read health and sync status as independent signals

"Synced" means the live manifests match Git — it says nothing about whether the Pod is crash-
looping. "Healthy" means Argo CD's health check for that resource type passed — a Deployment is
healthy when its replicas are available, a Job when it completed. An Application can be Synced and
Degraded simultaneously, which is normal right after a bad rollout, not a bug in Argo CD. For custom
resources (operators, CRDs) with no built-in health check, Argo CD reports them as "Healthy" by
default whether or not they actually are — write a Lua health check for anything that matters. See
`operators-and-crds` for what those resources are and `kubernetes-operations` for reading the
underlying workload state directly.

**Done when:** you can explain a Degraded-but-Synced Application without treating it as a sync bug.

## 4. Default to automated sync with prune and self-heal, per environment

Manual sync is a reasonable default for a first rollout to a sensitive environment, but leaving
Applications on manual sync long-term reintroduces the human-in-the-loop step GitOps exists to
remove. Turn on automated sync with `prune: true` (delete resources removed from Git) and
`selfHeal: true` (revert manual cluster edits) once you trust the pipeline, and stage that trust by
environment — automated in dev and staging, a deliberate promotion gate for prod via
`release-management` rather than disabling automation outright.

**Done when:** merging to the tracked branch deploys without anyone touching the Argo CD UI or CLI.

## 5. Diagnose stuck syncs by checking what's actually blocking, not by re-syncing blindly

A hung "Progressing" Application is usually one of: a health check waiting on a condition that will
never be true (wrong readiness probe, missing dependency), a resource stuck in a PreSync hook that
errored, or a webhook/admission controller silently rejecting part of the manifest. Re-running sync
without diagnosing just repeats the same failure. Check `argocd app get <name> --show-operation` and
the resource tree for the specific resource that isn't healthy, then look at its own events —
Argo CD is reporting the Kubernetes-level problem, not causing it. See `kubernetes-operations` for
digging into pod-level failures once you've located the stuck resource.

**Done when:** the stuck resource and its root cause are identified before any retry is attempted.

## 6. Scope access with projects, not shared admin

AppProjects restrict which repos, clusters, and namespaces an Application is allowed to target, and
which resource kinds it can create — use one per team or tenant boundary rather than letting every
Application use the `default` project with unrestricted scope. This is what turns "anyone can commit
an Application manifest" from a security risk into a bounded one. See `multi-tenancy` for the
broader cluster-sharing model and `iam-access-management` for tying projects to real identities.

**Done when:** a compromised or misconfigured Application in one project cannot deploy into another
team's namespace or cluster.

## Report

State how Applications are organized (app-of-apps, ApplicationSet generators, or flat), which
environments run automated sync with prune/self-heal versus manual, and how AppProjects bound
access. Call out any Application still relying on a custom or missing health check, or still on
manual sync out of caution rather than design — that's the honest gap in how much you can trust the
green checkmark.
