---
name: ci-pipelines
description: Designs continuous integration pipelines that give a fast, honest merge signal — stage ordering, reproducibility, safe caching, and required checks that actually gate merges. Use this whenever the user is writing or debugging a CI workflow (GitHub Actions, GitLab CI, Jenkins), complaining that CI is slow or flaky, adding a required status check, or asking how to structure test stages. For what happens after merge use `continuous-delivery`; for making the underlying build itself faster use `build-optimization`; for securing the pipeline's runners and permissions use `pipeline-security`.
license: MIT
---

# CI Pipelines

The purpose of CI is to answer one question as fast and as truthfully as possible: is this change
safe to merge? Every design decision — stage order, what runs in parallel, what blocks merge —
should be judged against that question. A pipeline that is fast but lies (flaky,
non-deterministic, skips real checks) is worse than no pipeline, because people stop trusting it
and start merging past red.

A pipeline that takes twenty minutes but never lies beats one that takes two minutes and is wrong
once a week.

**A CI pipeline exists to produce a merge signal that is fast, deterministic, and trusted — in
that order of what you sacrifice first.**

For concrete GitHub Actions patterns — caching, matrix builds, SHA pinning, OIDC, reusable
workflows — read `references/github-actions.md`.

## 1. Order stages cheapest-and-most-likely-to-fail first

Lint and type-check fail faster than unit tests, which fail faster than integration tests, which
fail faster than end-to-end tests. Run them in that order and fail fast on the first red stage
instead of running everything to completion. This isn't just about total wall-clock time — it's
about the time a developer waits for the *first* useful signal, since that's when they
context-switch back to the PR.

- **Static checks first:** formatting, linting, type-checking — seconds, and catch the most
  common mistakes.
- **Unit tests second:** no network, no containers, fully parallelizable.
- **Integration/e2e last:** slowest, most infrastructure-dependent, most prone to flakiness.

**Done when:** a developer gets their first CI failure signal in under two minutes for the common
case (lint or unit test failure).

## 2. Pin everything the pipeline touches

A pipeline that produces a different answer on a re-run of the same commit is not a merge signal,
it's a random number generator. Pin the CI runner image, the language/toolchain version, and
every dependency via a lockfile (package-lock.json, poetry.lock, go.sum, Gemfile.lock). "Latest"
tags for base images and unpinned action versions (`uses: actions/checkout@v4` vs `@sha256:...`)
are the two most common sources of a pipeline that passed yesterday and fails today for no code
reason.

```yaml
# bad: floats with upstream changes, breaks reproducibility
- uses: actions/setup-node@v3
  with:
    node-version: latest

# good: pinned toolchain, lockfile installs exact deps
- uses: actions/setup-node@v3
  with:
    node-version: '20.11.1'
- run: npm ci   # not `npm install` — respects the lockfile exactly
```

**Done when:** re-running the same commit's pipeline twice, a week apart, produces the same
pass/fail result.

## 3. Cache aggressively, but never let the cache change the answer

Dependency and build caches are the biggest lever on CI wall-clock time, but a cache keyed wrong
silently serves stale artifacts and turns a real failure into a false pass (or vice versa). Key
the cache on a hash of the lockfile, not on branch name or "latest" — if the lockfile hasn't
changed, the cache is valid regardless of which branch produced it. See `build-optimization` for
the deeper mechanics of cache layering and remote caches; here the concern is narrower:
correctness before speed.

- **Cache inputs, not outputs of the thing under test.** Caching `node_modules` is fine; caching
  test results is not — that's the thing you're trying to verify.
- **Invalidate on lockfile hash**, never on a manually bumped cache version that someone forgets
  to bump.
- **Treat cache misses as normal**, not an error — a cold cache should still produce a correct,
  just slower, result.

**Done when:** deleting the cache entirely and re-running produces the identical pass/fail result
as a cache hit, only slower.

## 4. Make required checks a deliberate, reviewed list

Every check that blocks merge is a tax on every future PR, forever. Add a required check only
when its failure means "do not ship this," not "someone should look at this eventually." Flaky or
advisory checks (a nightly-only integration suite, a slow visual regression test) belong as
non-blocking reports, not required statuses — a required check that's flaky trains people to
click "re-run" without reading the failure, which defeats the entire point of requiring it.

- **Audit required checks quarterly** — delete ones nobody remembers the purpose of.
- **A flaky required check gets fixed or demoted within days**, not left flaky indefinitely.
- **New required checks get introduced as non-blocking first**, promoted to required once they've
  proven stable for real PRs.

**Done when:** every required check on the default branch has an owner who can explain why it
blocks merge.

## 5. Keep CI's job separate from CD's job

CI answers "is this change correct." CD answers "should this change go live, and where."
Conflating them — deploying to a shared staging environment as part of the same workflow that
runs unit tests — means a deploy failure blocks unrelated PRs, and a slow deploy step makes every
contributor wait for infrastructure that has nothing to do with their code's correctness. Keep
the boundary at the merge: CI runs on every push and PR; CD triggers on merge to main (or on tag)
and is a separate pipeline. See `continuous-delivery` for what happens on the far side of that
boundary.

**Done when:** a developer can get a full green CI signal on a PR without anything being deployed
anywhere.

## 6. Promote the exact artifact you tested, never rebuild it

If CI builds artifact X and CD rebuilds "the same" artifact from source for deployment, you've
tested something you're not shipping. Compilers, dependency resolution, and even timestamps can
make two builds of the "same" commit different. Build once in CI, publish it with a
content-addressed or immutable version, and have every later stage pull that exact artifact.
Details on where and how to store it belong to `artifact-management`.

**Done when:** the SHA/digest of the artifact deployed to production matches the SHA/digest of
the artifact that passed CI, byte for byte.

## Report

State the pipeline's stage order and roughly how long each stage takes, what's pinned (runner
image, toolchain version, action SHAs), how the cache is keyed, and the current list of required
checks with owners. Call out any check that's flaky or any stage still rebuilding instead of
promoting an artifact — those are the honest gaps, and naming them beats claiming a green
pipeline means the system is fully trustworthy.
