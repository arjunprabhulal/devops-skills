---
name: gitops
description: Establishes Git as the single source of truth for deployed state, with a pull-based controller reconciling the cluster to match a repo instead of humans or pipelines pushing changes via kubectl or helm. Use this whenever the user designs a deployment repo layout, asks how environments should be promoted, debates config repo vs app repo, wants rollback to mean "revert a commit," or decides what belongs in Git versus a secret store. For the controller itself use `argocd-operations`; for canary mechanics use `progressive-delivery`; for building images use `ci-pipelines`.
license: MIT
---

# GitOps

GitOps is not "we keep our YAML in Git." It is a specific operational model: a controller inside
the cluster continuously pulls desired state from a repo and reconciles reality toward it, so the
repo is not documentation of what was deployed — it is the only correct description of what should
be deployed, and anything else is drift waiting to be corrected. That shift from push to pull is
what makes the rest of the practice fall into place: audit trail, rollback, and promotion all
become Git operations instead of pipeline scripts.

**If the cluster state and the repo disagree, the cluster is wrong, not the repo.**

## 1. Separate the app repo from the config repo

The repo where application code lives and the repo the reconciler watches should not be the same
repo, and should almost never be the same commit. CI in the app repo builds an image, pushes it to
a registry, and then makes a small, automated commit to the config repo bumping an image tag — it
never touches the cluster directly. This split matters because it lets you reason about "what is
deployed" by reading one small, low-churn repo instead of grepping application history, and it lets
the config repo have its own review rules (e.g. required approval for prod) independent of code
review norms. See `ci-pipelines` for the build side and `artifact-management` for where the image
actually lives.

**Done when:** deploying a new version never requires a human to run a deploy command by hand.

## 2. Model environments as directories or branches promoted by merge

Represent each environment (dev, staging, prod) as its own path or overlay, and promote a change by
merging or copying it forward — not by re-running a pipeline with a different target flag. A pull
request from `staging/` into `prod/` is a promotion event with a diff, a reviewer, and a timestamp,
which is a far stronger artifact than a Jenkins job log claiming the same thing happened. Kustomize
overlays or Helm values-per-environment both work; what matters is that the *mechanism* of promotion
is a Git operation everyone can see. See `environment-management` for how environments are defined
and `release-management` for gating promotion on approvals or criteria.

**Done when:** you can answer "what's different between staging and prod" with a single git diff.

## 3. Never let anyone or anything run kubectl apply against these clusters

The moment a human or a CI job applies manifests directly, the repo stops being the source of
truth and starts being a suggestion. Every path to changing cluster state — including emergency
fixes — must go through a commit, even if that commit is made and merged in under a minute during
an incident. Lock this down with cluster RBAC that denies write access to everyone except the
reconciler's service account. The discipline pays for itself the first time someone asks "who
changed this and why" and the answer is a commit message instead of a shrug. For the controller
enforcing this, see `argocd-operations`; for the RBAC mechanics see `kubernetes-security`.

**Done when:** no human credential in the system can mutate cluster state directly.

## 4. Make rollback mean "revert," not "remember what we did"

If promotion is a merge, rollback is a revert: `git revert` the bad commit, push, and let the
reconciler pull the previous known-good state back down. This only works if manifests are fully
declarative and self-contained — no imperative migration steps hiding outside the diff, no
"also run this script" in a runbook. Treat any deploy that can't be undone by reverting its commit
as a bug in the manifests, not an acceptable exception. This is also why rollback should be tested
before it's needed, not discovered live during an incident.

```
git revert <bad-commit> && git push   # reconciler pulls this within its sync interval
```

**Done when:** the last rollback in this repo was a plain revert with no manual cleanup afterward.

## 5. Keep secrets out of Git entirely

Config belongs in Git; secret values do not, even encrypted-at-rest-in-a-private-repo is not good
enough once you consider history, forks, and CI log leakage. Reference secrets from Git — a
`SealedSecret`, an `ExternalSecret` pointing at a vault, an SOPS-encrypted file if you truly must
commit ciphertext — rather than storing plaintext or something trivially reversible. The rule is
simple: a leaked clone of this repo should leak zero credentials. See `secrets-management` for the
storage and rotation mechanics this skill deliberately does not cover.

**Done when:** cloning this repo and reading every file yields no usable credential.

## 6. Treat drift as a signal, not noise

Drift — cluster state diverging from the repo — will happen: a debugging `kubectl edit`, a
mutating webhook, an autoscaler writing back replica counts. Configure the reconciler to detect and
either auto-heal or loudly flag drift rather than silently tolerating it, and exclude only the
specific fields (like HPA-managed replicas) that are expected to diverge. Undetected drift is how
"the repo is the source of truth" quietly becomes false over weeks. See `observability` for
alerting when reconciliation itself falls behind or fails.

**Done when:** any out-of-band cluster change is either corrected automatically or surfaced as an
alert within one reconciliation cycle.

## Report

State the repo layout chosen (app/config split, directory-per-environment or branch-per-environment),
how promotion and rollback are performed, and where secrets are referenced from. Call out any
remaining path where someone can still apply changes outside Git — that gap, if it exists, is the
actual state of your source of truth, and naming it beats claiming the model is fully enforced.
