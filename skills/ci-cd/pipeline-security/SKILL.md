---
name: pipeline-security
description: Secures the CI/CD pipeline itself as an attack surface — least-privilege runners, protecting secrets, preventing poisoned-pipeline execution, pinning third-party actions by SHA, and preferring OIDC over long-lived keys. Use this whenever the user configures CI runner permissions, stores secrets for a pipeline, reviews a workflow file for security issues, or sets up cloud credentials for a deploy job. For scanning produced artifacts use `image-scanning`; for the wider software supply chain use `supply-chain-security`.
license: MIT
---

# Pipeline Security

CI/CD pipelines are one of the highest-leverage attack targets in most organizations, and
defended far less than production itself: a compromised pipeline can push malicious artifacts
straight to production, exfiltrate every secret it touches, and do it with legitimate-looking
commits and green checkmarks. Treat the pipeline with the same rigor as production infrastructure
— because functionally, it has more power than production, it's what *creates* production.

If your pipeline can deploy to production, your pipeline security posture is your production
security posture.

**A pipeline that can push to production must be defended as rigorously as production itself — it
is a privileged system, not a convenience layer.**

## 1. Give runners the least privilege the job actually needs

A CI job that only runs unit tests has no business holding cloud credentials capable of deploying
to production, yet shared runner configurations often grant broad permissions "for convenience"
across every job type. Scope credentials per job: test jobs get no cloud access at all, build
jobs get registry push access and nothing else, deploy jobs get deploy-scoped credentials to
exactly the environment they target. A compromised test-stage dependency should not be able to
reach production.

- **Test/lint jobs:** no cloud credentials, no network egress beyond package registries.
- **Build jobs:** registry push, nothing broader.
- **Deploy jobs:** scoped to one environment, ideally via short-lived, environment-specific
  credentials.

**Done when:** no single CI job holds credentials for more than the one environment or system
it's actually responsible for touching.

## 2. Use OIDC federation instead of long-lived static credentials

A long-lived cloud access key stored as a CI secret is a standing liability — it doesn't expire
on its own, it can leak through logs or a misconfigured job, and revoking it requires someone to
notice and act. OIDC federation (GitHub Actions ↔ AWS/GCP/Azure via workload identity) issues
short-lived, scoped credentials per job run, tied to verifiable claims about which repo and
workflow requested them — nothing persists to leak after the job ends.

```yaml
# OIDC-based auth: no long-lived secret stored anywhere,
# credentials are minted per-run and expire with the job
permissions:
  id-token: write
steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/ci-deploy
      aws-region: us-east-1
```

**Done when:** no pipeline stores a static, long-lived cloud credential as a secret — deploy
credentials are minted per-run via OIDC.

## 3. Protect secrets from both exposure and exfiltration

Secrets in CI face two distinct risks: accidental exposure (printed to logs, echoed in a debug
step, exposed to a forked-PR workflow that shouldn't have them) and deliberate exfiltration
(malicious code in a dependency or PR reads the secret and sends it somewhere). Mask secrets from
logs by default, scope which workflows and branches can access which secrets, and never expose
secrets to workflows triggered by pull requests from forks — that's a well-known path for a
malicious PR to steal a secret it should never see.

- **Never grant secrets to fork-triggered PR workflows** by default — this is the single most
  common secret-leak vector in public and semi-public repos.
- **Mask and never log** secret values, and audit that debug/verbose flags don't defeat masking.
- **Scope secrets per environment**, not one giant shared secret bag every job can read.

**Done when:** a malicious pull request from an outside contributor cannot access any production
secret, even if it fully controls the PR's own workflow run.

## 4. Prevent poisoned-pipeline execution

A poisoned pipeline attack modifies pipeline *configuration* (the workflow YAML, a build script,
a Makefile) rather than application code, so it executes with the pipeline's privileges rather
than the application's — often bypassing code review entirely if the CI config itself isn't
reviewed with equal rigor. Require review for changes to pipeline definitions with the same or
greater scrutiny as production code, disable auto-run of pipeline changes proposed by untrusted
contributors until reviewed, and treat any script the pipeline executes (build scripts,
Makefiles, pre-commit hooks) as part of the trusted codebase, not incidental tooling.

**Done when:** a change to the pipeline configuration itself requires the same review gate as a
change to production code, and untrusted contributors' pipeline changes don't auto-execute with
privileged credentials.

## 5. Pin third-party actions and dependencies by SHA, not by tag

A workflow that references `uses: some-action@v1` trusts that the tag `v1` will always point at
the same, safe code — but tags are mutable, and a compromised or malicious action maintainer can
repoint `v1` to something else entirely, and every pipeline using that tag inherits the change on
the next run with no review. Pin to a commit SHA, which is immutable, and update deliberately
with a reviewed diff rather than silently trusting whatever the tag currently resolves to. This
is the CI-specific instance of a pattern this collection also covers for container base images in
`image-scanning`.

```yaml
# fragile: v4 can be repointed by the action's maintainer, or their compromised account
- uses: actions/checkout@v4

# durable: this exact commit's code, verified once, never silently changes
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

**Done when:** every third-party action or reusable workflow the pipeline depends on is pinned to
a commit SHA, not a mutable tag.

## 6. Sign what the pipeline produces

Signed commits and signed artifacts let anyone downstream verify that what they're looking at
actually came from the pipeline it claims to, rather than trusting the chain of custody
implicitly. Sign build artifacts (cosign for container images, in-toto/SLSA attestations for
provenance) as a pipeline step, and require verification of that signature before deploy — this
closes the loop with `artifact-management`'s provenance tracking by making provenance
cryptographically checkable, not just recorded metadata someone could tamper with.

**Done when:** the deploy stage refuses to deploy an artifact whose signature doesn't verify
against the pipeline's known signing identity.

## Report

State runner privilege scoping per job type, whether cloud credentials are OIDC-issued or static,
how secrets are scoped and masked against fork PRs, and whether third-party actions are pinned by
SHA. Name the honest gap: usually it's at least one long-lived credential still in use, one
action still pinned to a mutable tag, or artifact signing that's configured but not yet enforced
as a deploy gate.
