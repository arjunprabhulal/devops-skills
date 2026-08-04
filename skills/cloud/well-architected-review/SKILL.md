---
name: well-architected-review
description: Runs a structured audit against the standard pillars — reliability, security, cost, performance, operational excellence, sustainability — producing prioritized, actionable findings, not a checklist tick. Use this whenever the user asks for an architecture review, a well-architected assessment, a pre-launch readiness check, "is this built right," or wants pillar tradeoffs reconciled into a decision. For fixing one pillar in depth use `cost-optimization` or `disaster-recovery` directly — this is the cross-cutting audit that finds where to point them.
license: MIT
---

# Well-Architected Review

A well-architected review is worthless if it produces a scored checklist nobody acts on. The
pillars — reliability, security, cost, performance, operational excellence, sustainability — exist
in tension with each other, and the point of the review is to surface where a system has silently
picked a tradeoff nobody signed off on, then rank what to fix.

Treat the review as a prioritization exercise, not a grading exercise. **A review that doesn't end
in an ordered, owned list of changes was not worth running.**

For the full pillar-by-pillar question checklist, read `references/review-checklist.md`.

## 1. Scope the review to a system, not the whole estate

A review of "everything" produces shallow findings on everything and depth on nothing. Pick one
system or one bounded set of services, understand its actual traffic and failure history, and
review that deeply. Repeat for other systems on a cadence rather than trying to cover the whole
estate in one pass.

**Done when:** the review's scope and boundary are written down before the first pillar is
assessed.

## 2. Assess each pillar against evidence, not intent

For each pillar, ask what actually happens, not what the design intends:

- **Reliability** — has the stated failure domain (see `cloud-architecture`) actually been tested,
  and does `disaster-recovery` and `chaos-engineering` coverage exist for it?
- **Security** — is access scoped by `iam-access-management`, are secrets handled per
  `secrets-management`, has `vulnerability-management` run recently?
- **Cost** — does spend match the `cost-optimization` and `resource-tagging` expectations, or has
  it drifted?
- **Performance** — is there `load-testing` evidence at expected peak, not just steady state?
- **Operational excellence** — do `runbooks` exist and match reality, is `on-call-management`
  sane for this system's incident volume?
- **Sustainability** — is compute and storage rightsized (`rightsizing`), or is idle capacity
  running because nobody's looked?

**Done when:** every pillar's finding is backed by an artifact (a test result, a dashboard, a
runbook) rather than a stakeholder's confidence.

## 3. Surface the tradeoffs the system already made silently

Every real system trades one pillar against another — extra reliability spend that hurt cost
efficiency, a security control skipped for launch speed. The review's job is to find these and
make them explicit decisions instead of accidents. A system that scores well on every pillar
independently but has an unowned tradeoff between two of them has not actually been reviewed.

**Done when:** each identified cross-pillar tradeoff has a named owner who either accepts it or
schedules a fix.

## 4. Rank findings by risk times cost to fix, not by pillar

A long, flat list of findings across six pillars gets ignored. Rank findings by the product of
how bad the outcome is and how likely it is, weighed against how cheap the fix is — a
one-line IAM policy fix that closes a real exposure outranks a theoretical performance tweak that
would take a quarter, even though the tweak "sounds" more technical.

| Priority | Criteria |
|---|---|
| Now | High likelihood, high impact, cheap fix |
| Next | High impact, expensive fix, or moderate likelihood |
| Later | Low likelihood or low impact, regardless of fix cost |

**Done when:** every finding has a priority tier and nothing is left unranked as "also noted."

## 5. Route each finding to an owner and a sibling skill, don't fix it inline

The review identifies problems; it is not the place to solve deep pillar-specific work. A
reliability gap goes to whoever owns `disaster-recovery` or `capacity-planning`; a cost finding
goes to whoever owns `cost-optimization`. Handing off with the specific skill and finding attached
is what turns a review into action instead of a document that gets filed away.

**Done when:** every "Now" and "Next" finding has an assigned owner and a target date, not just a
description.

## 6. Re-run on a cadence, and track whether prior findings closed

A one-time review captures a moment; the system keeps changing after it. Re-review on a fixed
cadence (or after a major architecture change) and open by checking whether the prior review's
"Now" items actually closed — a review whose own findings never close is a sign the process, not
the system, is broken.

**Done when:** the previous review's findings have a closed/open status before the current review
starts.

## Report

State the system reviewed, the pillar-by-pillar evidence-backed findings, and the priority-ranked
action list with owners. Name any pillar that couldn't be assessed for lack of evidence (no
load-test data, no DR drill history) — an unassessed pillar is not a passing grade, it's an
unknown, and saying so is more honest than defaulting it to green.
