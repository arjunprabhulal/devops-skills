---
name: self-service-infrastructure
description: Lets developers provision databases, queues, and environments themselves through guardrailed templates instead of filing a ticket and waiting on a platform team. Use this whenever the user designs a self-service provisioning flow, decides what needs manual approval versus auto-approval, replaces ticket-based infrastructure requests, or worries self-service will let someone provision something dangerous or expensive. For the IaC modules provisioned use `terraform-modules`; for the guardrail logic use `policy-as-code`; for the templates surfaced to developers use `golden-paths`.
license: MIT
---

# Self-Service Infrastructure

Ticket-ops — a developer files a request, a platform engineer manually provisions it two days
later — doesn't make infrastructure safer, it just makes it slower while creating a new failure
mode: the manual step where a tired engineer clicks the wrong region or forgets a tag. Self-service
done well replaces the slow human gate with a fast automated one that's actually more consistent
than the human was.

The goal isn't zero approval, it's approval only where it earns its cost. **A guardrail that blocks
everything is not safer than no guardrail — it just pushes people back to manual workarounds that
have no guardrail at all.**

## 1. Default to auto-approve, escalate by blast radius

Most infrastructure requests are low-risk and repetitive: a dev-environment database, a staging
queue, a preview namespace. Requiring human sign-off on these teaches people that approval is
theater, and theater gets rubber-stamped without being read. Reserve actual human review for what
genuinely warrants it — production data stores, anything crossing a compliance boundary, anything
above a cost threshold — and auto-approve everything else through policy checks instead of a
person.

- **Tier requests by blast radius**, not by resource type — a dev Postgres instance and a prod
  Postgres instance are not the same request even though they use the same module.
  See `terraform-modules` for how the underlying module itself should be parameterized to make
  this tiering mechanical rather than manual.
- **Auto-approve within guardrails**: size limits, allowed regions, required tags, budget caps
  enforced by `policy-as-code`, not by a reviewer reading a form.
- **Route only the exceptions to a human** — anything outside the guardrails, not everything.

**Done when:** the majority of infrastructure requests provision without a human touching them,
and every one that does need a human has a clear reason why.

## 2. Bound the blast radius before you widen access

Self-service without limits is not self-service, it's an outage generator with a friendly UI. Every
template needs hard caps baked in before it's offered — max instance size, allowed regions,
mandatory encryption, network isolation defaults — so the worst a developer can do by clicking
through the form is bounded and known in advance, not discovered after the fact.

```hcl
# the template enforces the ceiling; the developer only picks within it
variable "instance_size" {
  type    = string
  default = "db.t3.medium"
  validation {
    condition     = contains(["db.t3.small", "db.t3.medium", "db.t3.large"], var.instance_size)
    error_message = "Instance size must be one of the approved self-service tiers."
  }
}
```

**Done when:** you can state the maximum possible cost and blast radius of any single self-service
request without needing to check what a specific developer actually requested.

## 3. Make the request path the only path

If the CLI, console, or raw Terraform apply still works alongside the self-service portal, people
will use whichever is faster in the moment, and the guardrails only protect the path nobody's
actually using. Lock down direct provisioning access so the self-service flow is the path of least
resistance, not just an option competing with the old one.

**Done when:** provisioning outside the self-service flow requires an explicit, logged, break-
glass exception — not a standing credential anyone can reach for.

## 4. Show cost and ownership before provisioning, not after the bill

A developer who doesn't see the projected monthly cost of what they're about to create has no way
to make a good decision, and finds out three weeks later from `cloud-budgeting` instead. Surface
estimated cost and require an owner and cost-center tag at request time, before the resource
exists, so accountability is attached at creation instead of reconstructed later during an audit.

**Done when:** every self-service request shows a cost estimate and requires an owner tag before
it can be submitted.

## 5. Log every request and its guardrail decision

When something does go wrong — an over-provisioned instance, a resource in the wrong region — the
first question is always "how did this get approved." If auto-approval decisions aren't logged
with the policy that allowed them, you can't answer that question and you can't tell whether the
guardrail itself needs tightening. Treat the approval log as an audit trail, not just a debugging
convenience.

**Done when:** for any provisioned resource, you can show which guardrail rule approved it and
when, without asking the requester.

## Report

State what percentage of requests auto-approve versus route to a human, the hard caps baked into
each template, and how cost and ownership are captured at request time. Name any provisioning path
that still bypasses self-service entirely — that standing exception is the real blast-radius risk,
and naming it beats claiming everything now goes through the guardrails.
