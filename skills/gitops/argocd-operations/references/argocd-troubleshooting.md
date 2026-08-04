# Argo CD Troubleshooting

## Contents

- Synced vs Healthy, again, because it's the root of most confusion
- Common stuck states
- Sync waves and phase hooks
- App-of-apps and ApplicationSets in practice
- `argocd app` command reference
- Drift and self-heal
- Finalizers and pruning gotchas

## Synced vs Healthy, again, because it's the root of most confusion

Two independent fields, two independent questions:

- **Sync status** (`Synced` / `OutOfSync` / `Unknown`) — does the live cluster state match what's in
  Git? This is a diff, nothing more.
- **Health status** (`Healthy` / `Progressing` / `Degraded` / `Suspended` / `Missing` / `Unknown`) —
  does Argo CD's health check for each resource pass? This is a judgment about whether the thing you
  applied is actually working.

`argocd app get <name>` prints both at the top. If you only read one field and act on it, you will
either chase a phantom "sync" problem that's really a broken health check, or declare victory on an
Application that's Synced but serving 500s. Every state below is a combination of the two.

## Common stuck states

**OutOfSync, sync never triggers.** Auto-sync is off, or it's on but `selfHeal` is off and a manual
cluster edit is being tolerated instead of reverted — check `argocd app get <name> -o json | jq
'.spec.syncPolicy'` first. If automation is enabled and it's still OutOfSync, something is failing
silently on each attempt; look at `.status.operationState` for the last error before re-running sync.

**Progressing forever.** Usually a health check waiting on a condition that will never become true:
a readiness probe pointed at a dependency that's down, a `PodDisruptionBudget` blocking the rollout,
or a `Job` that never completes. Argo CD is reporting the Kubernetes-level truth, not inventing a
problem — drill into the resource tree for the specific resource stuck Progressing, then treat it as
a normal Kubernetes debugging problem. See `kubernetes-operations` for pod-level state once located.

**Unknown health.** Either a custom resource with no registered health check (Argo CD defaults CRDs
to `Healthy` unless one is written — "Unknown" shows up mid-transition), or the application
controller lost connectivity to the target cluster. Check `argocd cluster list` for the target
cluster's connection state before assuming the resource itself is the problem.

**SharedResourceWarning.** Two Applications both claim the same live resource (same GVK, namespace,
name) — almost always a copy-pasted manifest or an app-of-apps child accidentally targeting the same
path as another Application. Find the other owner via the resource's own annotations
(`kubectl get <kind> <name> -n <ns> -o jsonpath='{.metadata.annotations}'`) and remove it from one
Application's manifest set; don't just ignore the warning.

**Sync stuck on a hook.** A PreSync or Sync hook Job is still running, failed, or stuck Pending (same
scheduling problems as any other pod). Argo CD will not proceed past a hook that hasn't reported
success. Find it in the resource tree — hooks show up there like any managed resource — and check
its own logs (`kubectl logs job/<hook-job-name> -n <ns>`), not the Application's. If it's failed and
you need to unblock without fixing the root cause immediately, delete the hook resource and re-sync;
Argo CD recreates and re-runs it. Don't repeat this blindly — an intermittently failing hook is
usually a symptom.

## Sync waves and phase hooks

Sync waves order resources within a single sync operation using the
`argocd.argoproj.io/sync-wave` annotation — lower numbers first, default is `0`, negative and
positive both valid. Argo CD waits for everything in a wave to be `Synced` and `Healthy` before
starting the next wave, which is why a health check that never passes doesn't just degrade one
resource — it blocks every wave after it.

Phase hooks are a different, orthogonal mechanism using `argocd.argoproj.io/hook`:

- **PreSync** — runs before the sync starts applying resources. Use for schema migrations,
  pre-flight checks.
- **Sync** — runs interleaved with the normal apply, ordered by wave like anything else. Rarely
  needed; most things belong in PreSync or PostSync instead.
- **PostSync** — runs after all resources are Synced and Healthy. Use for smoke tests, cache
  warmup, notifications.
- **SyncFail** — runs only if the sync fails. Use for cleanup or alerting, not for anything the
  next sync depends on.

Hooks and waves compose: a PreSync hook can carry its own `sync-wave` annotation to order multiple
PreSync hooks against each other. `hook-delete-policy` (`HookSucceeded`, `HookFailed`,
`BeforeHookCreation`) controls whether the hook resource is cleaned up automatically — without it,
failed hook Jobs pile up across repeated syncs.

## App-of-apps and ApplicationSets in practice

App-of-apps is just an Application whose manifests are other Application objects — it has its own
sync status and health like any Application, so a broken child can show up as the parent being
Degraded even though the parent's own "resource" (the child Application CRs) applied fine. Check the
child, not the parent, when this happens.

ApplicationSets generate Applications from a generator plus a template — list, cluster, git
directory/file, matrix, and pull request generators are the common ones. Debug generation issues
against the ApplicationSet controller, not the child Applications:
`kubectl get applicationset <name> -n argocd -o yaml` and
`kubectl logs -n argocd deploy/argocd-applicationset-controller`. A child Application that exists but
is empty or wrong is a template bug; one that's simply missing is a generator bug — that split tells
you which half to read first.

## `argocd app` command reference

```bash
argocd app get <name>                       # sync + health status, resource tree, params
argocd app get <name> --show-operation      # detail on the currently running or last sync operation
argocd app get <name> --hard-refresh        # force Argo CD to re-diff against a fresh git fetch and live state
argocd app diff <name>                      # exact fields that differ between Git and live cluster
argocd app sync <name>                      # trigger a sync now, regardless of automation policy
argocd app sync <name> --resource <kind>:<name>   # sync one resource only, not the whole app
argocd app sync <name> --dry-run            # show what would change without applying it
argocd app history <name>                   # past sync revisions, newest last
argocd app rollback <name> <history-id>     # revert live state to a prior recorded sync (not a git revert)
argocd app resources <name>                 # flat list of every managed resource and its individual health
argocd app wait <name> --health --timeout 300   # block until Healthy, useful in CI after a sync
```

`argocd app diff` before `argocd app sync` is the single habit that prevents most "why did that
change" surprises — it's the same discipline as `terraform plan` before `apply`, and for the same
reason: the diff is cheap, the surprise is not.

`argocd app rollback` moves the live cluster state back to a previous sync's manifests but does
**not** touch Git — the tracked branch still points at the newer, presumably broken, commit. Left
alone, self-heal will notice the drift and sync forward again, undoing your rollback. Always follow
a rollback with a Git revert (or fix-forward commit) if auto-sync/self-heal is on, or the rollback
is temporary by construction.

## Drift and self-heal

With `selfHeal: true`, any manual `kubectl edit`/`patch`/`delete` against a managed resource gets
reverted on the next reconcile loop — this is intended, not a bug, and is exactly why "just kubectl
edit it to unblock things" is the wrong instinct once automation is trusted. For a genuine temporary
manual change (an incident-response scale-down, a hotfix before the PR lands), either pause
auto-sync first (`argocd app set <name> --sync-policy none`) or accept self-heal will revert it
within one reconcile interval.

Without `selfHeal`, drift just shows as OutOfSync until the next sync — more forgiving, but
"OutOfSync" then stops reliably meaning "a deploy is pending" and starts sometimes meaning "someone
hand-edited this."

## Finalizers and pruning gotchas

Argo CD adds `resources-finalizer.argocd.argoproj.io` to Applications so deleting the Application
also deletes (or, with `background`/`foreground` propagation, cascades the deletion of) everything
it manages. Delete an Application without realizing the finalizer is there and `kubectl delete
application` will hang until cleanup completes — that's expected, not a stuck controller; `kubectl
get application <name> -o yaml` shows `deletionTimestamp` set while it works through it.

`prune: true` deletes any resource that's in the live cluster but no longer in Git. Two gotchas:

- A resource removed from Git by accident (a bad rebase, a moved file) gets pruned on the very next
  auto-sync — no confirmation step. Review `argocd app diff` for unexpected deletions, not just
  additions, before merging anything that touches manifest paths.
- Resources with `argocd.argoproj.io/sync-options: Prune=false` are intentionally excluded — use
  this for anything Argo CD should manage on create/update but never delete on its own, like a PVC
  holding data you don't want wiped by a manifest typo.

Prune order follows sync waves in reverse for a full application delete; for an ordinary sync,
pruned resources are removed in the same wave-ordered pass as everything else, so a resource an
earlier wave still depends on can be pruned before that's confirmed safe if the dependency isn't
expressed in Git anymore either. Keep wave numbers meaningful in both directions, not just creation
order.
