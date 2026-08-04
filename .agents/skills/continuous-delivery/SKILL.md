---
name: continuous-delivery
description: Builds the deployment pipeline that takes an artifact from a merged commit to production automatically and safely — promotion gates between environments, deploy-on-merge, and keeping main always releasable. Use this whenever the user is designing a deployment pipeline, asking how to ship changes faster, setting up dev/staging/prod promotion, or asking the difference between continuous delivery and deployment. For the merge signal that feeds this use `ci-pipelines`; for a single deploy's mechanics use `deployment-strategies`.
license: MIT
---

# Continuous Delivery

Continuous delivery means every merged change is, by default, in a shippable state — a human
decision (or, in continuous deployment, no decision at all) is the only thing standing between a
commit and production. The discipline this demands is upstream of the deploy pipeline itself: if
main isn't always releasable, "delivery" is a lie and someone will eventually hit "deploy" on a
broken build.

Most teams' real bottleneck isn't the deploy mechanics, it's the courage to trust that main is
always good enough to ship.

**Every commit on the default branch should be deployable at any moment — if it isn't, that's a
defect in the pipeline, not a reason to slow down releases.**

## 1. Make "always releasable" a property of main, not a hope

This means trunk-based development or short-lived branches, feature flags for incomplete work
instead of long-lived feature branches (see `feature-flags`), and a CI signal from `ci-pipelines`
that's trusted enough that green means go. If merging to main regularly breaks things, the fix is
smaller PRs and better CI coverage, not a slower delivery cadence — slowing down delivery treats
the symptom and lets the branch rot further between merges.

- **Small, frequent merges** beat big, infrequent ones — smaller diffs are easier to verify and
  easier to revert.
- **Incomplete features ship dark** behind a flag rather than living on a branch for weeks.
- **A red main is a stop-the-line event**, fixed or reverted before other work continues.

**Done when:** any commit on main can be deployed to production without someone first checking
"is this actually safe."

## 2. Automate promotion through environments, gate deliberately

The path from build to production usually passes through named environments (dev, staging, prod)
or through automated checks that substitute for them. Each gate should exist because it catches
something CI structurally cannot — real infrastructure, real data volumes, a human sign-off for
regulatory reasons — not as ceremony inherited from a pre-automation era. An untested manual
approval step that always gets rubber-stamped is worse than no gate: it adds latency and gives
false confidence that a human is actually checking.

```yaml
# promotion gate as an explicit, auditable pipeline step —
# not a Slack message asking "can I deploy?"
- stage: promote-to-staging
  when: ci_passed && artifact_signed
  run: deploy.sh --env staging --artifact $ARTIFACT_DIGEST
- stage: promote-to-prod
  when: staging_healthy && manual_approval(role: release-owner)
  run: deploy.sh --env prod --artifact $ARTIFACT_DIGEST
```

**Done when:** every gate between commit and production is either an automated check with a
defined pass/fail, or a named human role with real authority to say no.

## 3. Deploy on merge, decouple release from deploy

Continuous delivery deploys automatically; continuous deployment additionally releases
automatically — the two are not the same and conflating them causes needless fear. You can deploy
every merge to production instantly while still controlling *release* with a feature flag, so the
code being live and the feature being visible to users are separate decisions. This is what makes
"deploy on every merge" safe even for risky features: the deploy is reversible instantly (flag
off) without a rollback. See `feature-flags` for the mechanics.

- **Deploy** = new code is running in production.
- **Release** = users can reach the new behavior.
- Decoupling them means a bad deploy is a flag flip, not a rollback.

**Done when:** you can answer, for the last deploy, whether it was also a release — and if not,
what gates the release.

## 4. Keep the pipeline itself boring and idempotent

A deploy pipeline that behaves differently on retry, or that can't be re-run safely after a
partial failure, turns every incident into a pipeline debugging session on top of the actual
outage. Deploys should be idempotent (running the same deploy twice produces the same end state)
and the pipeline should be the *only* way production changes — no manual kubectl apply or console
click that the pipeline doesn't know about, or your "always releasable main" claim stops being
true the moment someone bypasses it.

**Done when:** re-running the last deploy pipeline job, unchanged, is safe and produces no
unintended side effects.

## 5. Instrument the pipeline itself, not just the app

Lead time (commit to production) and deploy frequency are the two numbers that tell you whether
delivery is actually continuous or just automated-but-rare. If a team ships once a week despite
having a fully automated pipeline, the bottleneck is process (approval queues, batching releases)
not tooling, and no amount of pipeline engineering fixes that. Track these numbers over time —
they're the earliest signal that delivery is regressing before anyone complains out loud.

**Done when:** you can state current lead time and deploy frequency from data, not from memory.

## Report

State how deploy is triggered (on merge / on tag / manual), how many promotion gates exist and
what each one actually checks, and current lead time / deploy frequency if known. Call out any
gate that's manual-but-always-approved (dead ceremony) or any way production can be changed
outside the pipeline — that bypass is the honest gap, since it means "main is always releasable"
isn't fully true yet.
