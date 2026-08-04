---
name: infrastructure-testing
description: Covers testing infrastructure and config before it ships — validate-and-plan checks, policy enforcement, unit and integration tests for IaC modules, ephemeral test environments, and a testing pyramid sized for infrastructure. Use this whenever the user adds tests for Terraform or Kubernetes manifests, asks why a plan applied cleanly but broke production, wants a policy check to block a risky change, or is deciding what needs a full environment versus a fast local check. For the policy rules use `policy-as-code`, and for module structure use `terraform-modules`.
license: MIT
---

# Infrastructure Testing

Infrastructure changes fail differently than application code — a syntactically valid Terraform
plan can still delete a production database, and a Kubernetes manifest that passes schema
validation can still deploy a container that can't reach anything it needs. "It applied without
error" is not evidence of correctness; it's evidence the tool understood the syntax.

Most infrastructure testing gaps come from treating `plan` output as sufficient review, when a plan
only tells you what will change, never whether that change is safe. **Test infrastructure changes
against the same rigor as application code — fast local checks first, real environments before
production, no exceptions for "it's just config."**

## 1. Build a testing pyramid sized for infrastructure

Application testing pyramids assume unit tests are cheap and environment tests are expensive; for
infrastructure the same shape holds but the layers look different — a fast static check catches
most mistakes, and a real environment is reserved for what nothing else can validate.

| Layer | What it catches | Speed |
|---|---|---|
| Lint / format | Syntax, style, drift from conventions | Seconds |
| Validate / plan | Type errors, what would actually change | Seconds–minutes |
| Policy check | Violations of security or cost rules | Seconds |
| Unit test (module) | A module produces correct output for given inputs | Seconds–minutes |
| Integration test | Real resources actually work together | Minutes–hours |

- **Push failures as far left as possible** — a mistake caught by a linter costs nothing; the same
  mistake caught by a failed production apply costs an incident.
- **Reserve the expensive layers for what only they can catch** — real network reachability, real
  IAM behavior, real cross-resource interaction.

**Done when:** every change passes lint, validate, and policy checks before it reaches a step that
provisions anything real.

## 2. Never trust a plan you haven't diffed against intent

A `terraform plan` or `kubectl diff` tells you what will change, not whether that change is what
you meant. The dangerous failure is a plan that's technically correct but does something the
author didn't intend — a renamed resource that Terraform reads as delete-then-recreate, a changed
selector that silently orphans running pods.

- **Read plan output for resource replacement, not just resource count** — a "2 to change" summary
  can hide a destructive replace next to a harmless in-place update.
- **Require a human to review plan output on anything touching stateful resources**, even when
  policy checks pass — policy catches known bad patterns, not every unintended consequence.
- **Treat "no changes" on an unexpected apply as a signal to investigate**, not a relief — it can
  mean the plan is targeting the wrong state.

**Done when:** every apply against a stateful or production resource has had its plan output
reviewed by a human against what the change was intended to do.

## 3. Enforce policy checks as a required gate, not a report

A policy check that runs and reports violations without blocking the change is documentation, not
enforcement — it gets ignored under deadline pressure exactly when it matters most. See
`policy-as-code` for writing the rules; this skill is about making sure they actually stop a bad
change rather than just noting it happened.

- **Block the pipeline on a policy failure** for anything above a defined severity — no public S3
  buckets, no unencrypted volumes, no unbounded security group rules.
- **Give policy failures a clear, specific message** naming the rule and the resource, not a raw
  error dump — a check nobody can interpret gets bypassed, not fixed.
- **Version and test the policies themselves** — a policy with a bug either blocks everything or
  blocks nothing, and both failure modes erode trust in the gate.

**Done when:** a change violating a required policy cannot merge or apply without an explicit,
logged override, not just a warning in CI output.

## 4. Unit test modules the same way you'd unit test a function

An IaC module that's reused across a dozen environments deserves the same input-output testing
discipline as a shared library — feed it a set of inputs, assert the plan or rendered output looks
right, without provisioning anything real. See `terraform-modules` for the module structure this
tests against.

- **Assert on generated configuration or plan output**, not on live infrastructure, for fast
  feedback on every commit.
- **Cover the module's documented input combinations**, especially optional variables and their
  defaults — the untested default is where drift hides.
- **Run these on every module change**, since a module used in ten places breaks ten places at once
  when it regresses.

**Done when:** every reusable module has tests covering its documented inputs that run without
provisioning real infrastructure.

## 5. Reserve ephemeral environments for what only a real environment proves

Some things — actual network reachability, real IAM policy evaluation, an autoscaler's real
behavior under load — can't be validated by static analysis. An ephemeral environment, spun up per
change and torn down after, gives you that proof without the cost or drift risk of a permanent
shared test environment.

- **Spin up per-change, tear down on completion** — a long-lived "test" environment accumulates
  drift and stops representing what production will look like.
- **Scope it to what static checks can't cover** — running a full integration suite here for
  something a linter already catches wastes the most expensive layer of the pyramid.
- **Match its topology to production closely enough** that a pass here is meaningful — see
  `environment-management` for keeping environments consistent.

**Done when:** every change that can't be fully validated statically runs against a fresh, isolated
environment before reaching production, and that environment is torn down afterward.

## Report

State which pyramid layers are enforced as required gates, whether policy failures block or just
report, and what ephemeral-environment coverage exists for changes static checks can't validate.

Name the honest gap — usually a policy check that reports but doesn't block yet, or a module with
no input-coverage tests — rather than claiming the pipeline fully prevents bad infrastructure
changes from shipping.
