---
name: environment-management
description: Covers keeping dev, staging, and prod as the same system at different sizes rather than forked copies that drift apart — parity via values not branches, ephemeral preview environments per pull request, and keeping non-prod cheap without making it useless as a signal. Use this whenever the user provisions a new environment, sets up preview environments for pull requests, debugs a bug that only happens in prod, or decides what should differ between environments. For one module with per-environment values use `terraform-modules`, for gating risky promotions use `policy-as-code`.
license: MIT
---

# Environment Management

"It worked in staging" loses all meaning the moment staging is a different system than prod —
different topology, different config format, a manually patched box nobody touched since it was
built. Staging's entire job is to be a trustworthy predictor of what will happen in prod. Every
divergence between them is a bug in that predictor, whether or not anyone notices it before the
next incident.

The only differences that should exist between environments are the ones you'd defend out loud:
scale, non-critical data, cost. Everything else — topology, versions, how config is structured —
should be identical.

**Environments should differ by the values you feed the same code, never by forking the code
itself.**

## 1. Make the difference a values file, not a branch

The moment staging and prod are separate directories or separate branches, they will diverge —
someone fixes a bug in one and forgets the other, or adds a resource to prod under deadline
pressure and never backports it. One codebase, one set of modules, environment-specific
`.tfvars` or equivalent values files is the only structure that makes divergence visible in a
diff instead of invisible until it breaks something.

See `terraform-modules` for the module-interface side of this and `infrastructure-as-code` for
the state-isolation side — each environment still needs its own state file even though it shares
code.

**Done when:** the diff between any two environments is fully expressed in their values files,
with zero resource-definition files that exist in one environment's directory and not another's.

## 2. Give every pull request its own throwaway environment

A shared staging environment queues every team behind whoever's currently testing something in
it, and a broken staging blocks everyone at once. Ephemeral, per-PR preview environments — spun
up on open, torn down on merge or close — remove the queue and catch integration bugs before
merge instead of after, when they're entangled with everyone else's changes.

- **Provision automatically from the same IaC used for permanent environments**, not a
  hand-maintained parallel setup that inevitably drifts from what prod actually looks like.
- **Tear down aggressively on merge or close** — an orphaned preview environment is pure cost with
  no one watching it, and they accumulate fast if cleanup isn't automatic.
- **Seed with representative, non-sensitive data**, not empty tables that hide entire classes of
  bugs a real dataset would surface.

**Done when:** opening a pull request produces a working, isolated environment automatically, and
closing or merging it tears the environment down automatically too.

## 3. Decide deliberately what's allowed to differ

Everything should be identical by default; every exception should be a conscious, documented
choice, not an accident of how the environment happened to get built.

| Dimension | Prod | Non-prod (reasonable to differ) |
|---|---|---|
| Topology / architecture | source of truth | identical |
| Software versions | source of truth | identical |
| Instance count / size | full scale | smaller, still multi-instance |
| External integrations | real | sandboxed or mocked third parties |
| Data | real, sensitive | synthetic or scrubbed |

Anything outside this table that differs between environments is drift, not a deliberate
decision — go find out how it happened.

**Done when:** every difference between staging and prod can be pointed to in this kind of table
and defended, with no undocumented divergence left over.

## 4. Keep non-prod cheap without making it a lie

Running every non-prod environment at full production scale is expensive and rarely necessary —
but shrinking it so far that it stops catching real bugs (single-instance when prod is clustered,
no autoscaling when prod scales) makes staging a false signal that's worse than no staging at
all. The goal is the cheapest version that still exercises the architecture prod actually runs.
See `cost-optimization` for the broader spend-control discipline this borrows from.

- **Scale down instance count and size**, not the topology itself — a single node standing in for
  a cluster hides every clustering bug.
- **Turn off or schedule down environments outside working hours** if nothing depends on 24/7
  availability there.

**Done when:** non-prod cost is materially lower than prod, and the team can still name a real bug
that staging caught before it reached production.

## 5. Make promotion between environments a pipeline step, not a person

Manually re-running `terraform apply` against prod with hand-edited variables is how "it worked in
staging" and "what actually got applied to prod" quietly diverge. Promotion should be the exact
same artifact and the exact same apply mechanism moving forward through environments, with only
the values file changing — tie this to `continuous-delivery` for the pipeline mechanics.

**Done when:** the artifact or plan applied to prod is provably the same one that was validated in
staging, not a re-generated or hand-edited copy.

## Report

State which environments exist, whether preview environments are automated end to end, and where
the documented, deliberate differences from prod are. Name the honest gap — usually a staging
environment shrunk enough that it no longer catches real bugs, a preview environment that isn't
torn down reliably, or a promotion path that still involves a manual apply — rather than claiming
full parity.
