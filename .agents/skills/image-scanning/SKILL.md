---
name: image-scanning
description: Finds vulnerabilities, misconfiguration, and embedded secrets in container images before they ship — CVE scanning in the pipeline, gate-versus-warn policy, base image freshness, and separating fixable findings from noise. Use this whenever the user asks about CVEs, Trivy, Grype, or Snyk scans, wants a pipeline to block on critical vulnerabilities, is triaging a scan report, or asks if an image is safe to deploy. For fixing image structure use `containerization`; for the org-wide vulnerability program use `vulnerability-management`; for signing use `container-registry`.
license: MIT
---

# Image Scanning

A scanner that reports everything is indistinguishable from one that reports nothing — teams stop
reading a 400-line CVE list after the first week. The job of scanning is not to find every issue,
it's to find the ones worth someone's attention and force a decision on them before the image
ships.

**A finding without a decision (fix, accept, or block) is just noise with a CVE number attached.**

## 1. Scan at build time, not just at rest

A scan that runs only against images already sitting in the registry catches problems after
they've potentially been deployed. Scan in the CI pipeline immediately after build, before push,
so a critical finding blocks promotion rather than triggering a retroactive scramble. Also
re-scan images already in the registry periodically — a base image with zero known CVEs today can
have a new one disclosed next week against the same digest, so freshness at build time is not
sufficient on its own.

**Done when:** every image is scanned before it is pushed to a registry other images pull from.

## 2. Gate on severity and exploitability, not raw CVE count

Blocking a deploy on every CVE, including ones with no known exploit and no reachable code path,
trains engineers to route around the scanner rather than fix things. Set a gate policy by
severity (block critical and high with a known fix available, warn on medium, log low) and by
whether the vulnerable package is actually reachable at runtime — a CVE in an unused transitive
dependency is a different risk than one in your entry point.

| Severity | Fix available | Action |
|---|---|---|
| Critical/High | Yes | Block the build |
| Critical/High | No | Warn, track, time-box a decision |
| Medium/Low | Either | Log, review on a cadence |

**Done when:** the pipeline's block/warn behavior matches a written policy, not an ad hoc
threshold someone picked once.

## 3. Distinguish fixable from noise before triaging

A finding with no available patched version is not actionable today no matter how severe it is —
flagging it the same way as a one-line dependency bump wastes triage time. Sort findings by
"upgrade available" first; those are cheap wins. For the rest, check whether the vulnerable code
path is reachable at all — many scanners can filter to only what's actually imported or invoked,
cutting a long CVE list down to the handful that matter. Suppress the remainder with a documented,
expiring exception, not a silent ignore rule that nobody revisits.

- **Triage fixable-first**: an available patch is the cheapest possible remediation.
- **Filter by reachability** where the scanner supports it, to cut noise from unused code paths.
- **Time-box exceptions** with an expiry and an owner, never a permanent suppression.

**Done when:** every suppressed finding has a documented reason and a review date.

## 4. Keep base images current on a schedule, not a trigger

Most CVEs found in a scan trace back to an outdated base image, not application code — rebuilding
against a refreshed base silently fixes a large fraction of findings without touching a line of
your own code. Automate base image bumps (Renovate, Dependabot, or a scheduled rebuild job) so the
image is never more than a few weeks stale, rather than waiting for a scan failure to prompt an
update.

**Done when:** the base image digest in use is never more than the team's agreed staleness window
behind upstream.

## 5. Scan for embedded secrets, not only CVEs

A vulnerability scanner and a secret scanner look for different things and most tools need both
enabled explicitly. A committed API key or private key baked into a layer is a more immediate risk
than most CVEs, and it survives even a later `RUN rm` (see `containerization` on why). Run
secret-detection as part of the same pipeline step, and treat any hit as an automatic block plus
a credential rotation, not just a finding to triage.

**Done when:** the scan pipeline checks for embedded secrets in addition to package
vulnerabilities, and a hit blocks the build.

## 6. Feed results into supply-chain evidence, not a dead-end report

A scan result that lives only in a CI log disappears the moment anyone asks "was this image
scanned before it deployed six weeks ago." Attach scan results and pass/fail status to the image
as attestations or in an artifact store tied to the image digest, so provenance and audit
questions can be answered later. Broader supply-chain provenance and signing live in
`supply-chain-security` and `container-registry`; this step is only about not losing the scan
evidence you already generated.

**Done when:** a scan result for any deployed image digest can be retrieved after the fact.

## Report

State which scanner and policy gated the build, the count of critical/high findings with fixes
available versus without, and whether secret scanning ran. Name any suppressed finding still
outstanding and its review date — an unreviewed suppression is the honest gap, not a clean-looking
pass/fail.
