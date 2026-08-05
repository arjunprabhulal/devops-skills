---
name: helm-charts
description: Covers packaging and templating Kubernetes manifests with Helm — chart structure, values design and environment overrides, releases and revisions, upgrade/rollback semantics, avoiding template sprawl, and choosing Helm versus Kustomize. Use this whenever the user is writing a Helm chart, designing a values.yaml hierarchy, debugging a failed `helm upgrade`, or deciding between Helm and Kustomize. For rollout mechanics on the cluster use `kubernetes-operations`; for GitOps delivery of charts use `gitops`.
license: MIT
---

# Helm Charts

Helm exists to solve one problem: the same application needs slightly different manifests in dev,
staging, and prod, and copy-pasting YAML across environments guarantees drift. A chart is a
template plus a values contract — the moment the templates start encoding environment-specific
logic instead of taking it as input, the chart has stopped doing its job.

The values file is the API of the chart; everyone who consumes it, including future-you, should be
able to configure the workload without reading the templates. **A chart is good if you can predict
its rendered output from `values.yaml` alone.**

## 1. Design values.yaml as a contract, not a dump

Every value you expose is something a consumer now depends on — expose too little and people fork
the chart to add one setting; expose too much and every value becomes load-bearing forever. The
right test: does this need to vary by environment or by deployer? If not, it's a template default,
not a value.

- **Group by concern**, not by template file — `resources`, `ingress`, `image` as top-level keys
  that read naturally, matching how consumers think about the workload.
- **Document every value's type and default** in `values.yaml` comments or a schema
  (`values.schema.json`) — undocumented values get set wrong silently.
- **Never require a values override just to make the chart install** — sane defaults should produce
  a working (if minimal) deployment with zero overrides.

**Done when:** someone unfamiliar with the templates can configure the chart correctly using only
`values.yaml` and its comments.

## 2. Layer environment overrides, don't fork the chart

The failure mode past "quick chart" is a `values-prod.yaml` that has silently drifted from
`values-dev.yaml` in ways nobody can diff meaningfully, or worse, three near-identical chart copies.
Helm's `-f` flag composes multiple values files in order — use that composition instead of
duplicating the whole file per environment.

```bash
helm upgrade myapp ./chart -f values.yaml -f values-prod.yaml --install
```

Keep `values.yaml` as the full default contract and environment files as small diffs on top —
if `values-prod.yaml` is nearly as long as `values.yaml`, the base defaults are wrong, not the
environment.

**Done when:** an environment-specific values file is a short diff, not a near-duplicate of the
base.

## 3. Treat every upgrade as something you will roll back

`helm history` and `helm rollback` only work if releases are tracked cleanly — a chart with
`--wait` omitted, hooks that aren't idempotent, or a values change bundled with an unrelated image
bump makes rollback unpredictable exactly when you need it least.

- **Use `--atomic --wait`** on upgrade so a failed rollout auto-rolls-back instead of leaving the
  release half-applied.
- **One logical change per release** — don't bundle an image bump with a values schema change; if
  the rollback needs to undo only one of them, a mixed release can't do that cleanly.
- **Hooks (`pre-upgrade`, `post-install`) must be idempotent** — Helm may retry or re-run them, and
  a migration hook that isn't safe to re-run will corrupt state on the second attempt.

**Done when:** `helm rollback` to the prior revision has been exercised and produces a known-good
state.

## 4. Stop templates from becoming a second programming language

Go templates in Helm support enough logic (`if`, `range`, `with`, named templates) to build
something unreadable fast. The tell that a chart has gone too far: nested `if`s controlling whether
whole resources exist, values that configure the shape of the template rather than its content, or
helpers (`_helpers.tpl`) that need their own comments to follow.

- **Named templates for repeated structure** (labels, common annotations), not for control flow —
  keep control flow visible in the resource file it affects.
- **If a chart needs to conditionally render 10 different resource combinations**, that's a sign it's
  actually several charts, or that a library chart / subchart split is overdue.
- **Lint and render before every commit**: `helm lint` and `helm template` catch broken YAML from
  whitespace/indentation errors that only surface at `helm install` time otherwise.

**Done when:** `helm template` renders valid manifests for every supported values combination, and
that rendered output is checked in CI rather than only at install time.

## 5. Choose Helm over Kustomize for packaging, not patching

Helm and Kustomize solve overlapping but different problems: Helm is a templating and packaging
system with releases, versioning, and a values contract for consumers who don't read the manifests;
Kustomize is patch-based overlay composition for teams who prefer editing plain YAML directly and
don't need a distributable package. Picking the wrong one shows up as fighting the tool for the
project's entire lifetime.

- **Choose Helm** when you're distributing to other teams/consumers, need parameterization deeper
  than field patches, or want release/rollback tracking baked in.
- **Choose Kustomize** when the team wants to read and patch plain manifests without a templating
  layer, and environment differences are small structural patches, not deep parameterization.
- **They compose**: `helm template | kustomize build -` is a legitimate pattern when you need Helm's
  packaging but Kustomize's patch ergonomics for final environment tweaks.

**Done when:** the choice is written down with the actual reason, not defaulted to whichever the
last project used.

## Report

State the chart's values contract shape, how environment overrides are layered, whether
`--atomic --wait` is used and rollback has been tested, and the Helm-vs-Kustomize decision if one was
made. Call out any template logic still hard to predict from values alone, or any values file that's
still a near-duplicate of another — naming that sprawl is more useful than calling the chart clean.
