---
name: policy-as-code
description: Covers enforcing infrastructure and cluster rules automatically, before a bad change ever reaches production — OPA, Sentinel, and Kyverno policies evaluated against the plan or admission request, and testing those policies like real code. Use this whenever the user is writing a Rego or Sentinel policy, adding an admission controller, wiring a policy check into a pipeline, or deciding whether a rule should be enforced or just audited. For the Terraform plan those policies gate use `infrastructure-as-code`, for Kubernetes-specific admission enforcement use `kubernetes-security`.
license: MIT
---

# Policy as Code

A wiki page that says "all S3 buckets must be private" prevents nothing — it's read once, if
ever, and forgotten by the next person who copies an old module. A policy written as code and
evaluated automatically against every plan or admission request prevents the violation from
landing at all, regardless of who wrote the change or whether they read the wiki.

The shift this skill is about is from *auditing* infrastructure after the fact to *rejecting*
bad infrastructure before it's ever applied. An audit finding is a cleanup task; a policy failure
is a change that never happened.

**A policy that only runs in a nightly audit report is a compliance artifact. A policy that
blocks the pipeline is a guardrail. Prefer the guardrail.**

## 1. Put the check where the change is still reversible

The cheapest place to reject a bad change is before it's ever applied — evaluate policy against
the Terraform plan output or the Kubernetes admission request, not against resources that already
exist. By the time a nightly scan finds a public bucket, it's been public for up to a day.

```rego
deny[msg] {
  input.resource_changes[_].change.after.acl == "public-read"
  msg := "S3 buckets must not be created with public-read ACL"
}
```

- **Gate the CI pipeline on the policy check**, not just the merge review — a human reviewer
  misses what an automated check catches every time.
- **Fail the pipeline, don't just warn**, once a policy is trusted — a warning nobody reads has
  the same effect as no policy.
- **Reserve runtime/admission-time enforcement for the things that slip through pre-merge**, like
  changes applied outside the pipeline entirely.

**Done when:** a plan or manifest violating a written policy cannot be applied through the normal
pipeline path, full stop.

## 2. Start every new policy in audit mode

A brand-new policy enforced immediately as a hard block will, with near certainty, break some
legitimate change nobody anticipated when writing the rule — and the first thing anyone learns
about the new policy is that it's an obstacle. Ship it as a warning first, watch what it flags
against real traffic for a stretch, then flip it to enforcing.

- **Log violations without blocking** for an initial period, and review what actually gets
  flagged before promoting the policy.
- **Communicate the promotion date** so teams have time to fix in-flight violations rather than
  getting blocked without warning.
- **Only promote to enforcing once the false-positive rate is near zero**, or the org will start
  routing around policy instead of respecting it.

**Done when:** every enforcing policy spent a defined audit-only period first, with its
audit-period findings reviewed and resolved.

## 3. Write policies against realistic inputs, not the happiest path

A policy tested only against a clean, minimal example plan will pass in testing and then choke
on the first real plan with nested modules, `for_each`, or conditional resources. Test with the
actual shape of plans and manifests this org produces.

- **Keep a library of representative plan/manifest fixtures**, including edge cases like
  `count = 0` resources and multi-provider plans, and run every policy against all of them.
- **Write both a passing and a failing fixture per rule** so a future edit to the policy can't
  silently stop enforcing anything.
- **Treat policy code with the same review rigor as application code** — a bug in a policy either
  blocks legitimate work or, worse, lets through exactly what it was meant to stop.

**Done when:** every policy has an automated test asserting both a case it correctly blocks and a
case it correctly allows.

## 4. Scope each policy to one rule, and name it for what it prevents

A policy file that checks tagging, encryption, and instance sizing together is hard to debug when
it fails, and impossible to promote to enforcing incrementally — one false positive on tagging
blocks legitimate encryption enforcement too. Keep policies narrow and composable, the same
argument made for modules in `terraform-modules`.

- **One rule per policy**, named for the specific thing it denies — `deny-public-s3-acl`, not
  `s3-policy`.
- **Compose a bundle of narrow policies per pipeline stage**, so any one can be promoted, rolled
  back, or exempted independently of the rest.

**Done when:** any single policy can be disabled or rolled back without affecting the enforcement
status of any other rule.

## 5. Build an exception path, or people will build their own

Every policy will eventually be legitimately wrong for one specific case. Without a sanctioned,
auditable way to request an exception, people will find an unsanctioned one — commenting out the
check, splitting the resource into a separate unmanaged apply, or routing around the pipeline
entirely, all of which are worse than the exception would have been.

**Done when:** there's a documented process to request a time-bound, logged exception to any
policy, and every current exception has an owner and an expiry.

## Report

State which policies are enforcing versus still in audit mode, and what each one actually
prevents. Name the honest gap — usually a policy still in audit-only mode past its promotion
date, an exception with no expiry, or a rule with no failing-case test — rather than presenting
policy coverage as complete.
