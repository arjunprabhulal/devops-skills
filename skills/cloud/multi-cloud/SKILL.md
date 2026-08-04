---
name: multi-cloud
description: Covers running across cloud providers on purpose — portability vs managed services, the real operational cost of a second provider, avoiding accidental multi-cloud, and where the abstraction is worth it. Use this whenever the user is considering a second provider, evaluating a portability layer like Kubernetes across clouds, discovering their stack already spans providers without a plan, or asking whether to abstract away managed services. For the shape within one provider use `cloud-architecture`; for moving a workload use `cloud-migration`.
license: MIT
---

# Multi-Cloud

Multi-cloud is usually sold as risk reduction and delivered as a tax: a second provider means a
second set of IAM models, networking primitives, billing dashboards, and on-call runbooks to
maintain, permanently, whether or not you ever use the failover it was meant to provide. The
question is never whether multi-cloud is possible — it always is — but whether the ongoing
operational cost buys something the business actually needs.

Most teams that end up multi-cloud didn't decide to; they acquired a company, or a team picked a
different provider, or a vendor tool only ran on one cloud. **Multi-cloud should be a decision
with a stated reason, not something you discover you're already doing.**

## 1. Name the reason before building anything

The legitimate reasons are narrow: a regulatory requirement to avoid a single vendor, genuine
negotiating leverage at large spend, a specific managed service only one provider offers, or
disaster-recovery requirements that mandate provider diversity. "Just in case we need to switch"
is not on that list — it's a hedge against a risk that's rarely priced against the daily cost of
carrying it.

**Done when:** the reason for running on more than one provider is written down and would survive
someone asking "why not just use one?"

## 2. Separate true portability from lowest-common-denominator design

Building only on the intersection of features every provider supports means giving up each
provider's best managed offerings — a managed database with strong consistency guarantees, a
purpose-built queue — in favor of something you self-run so it's portable. That trade is
sometimes right and often isn't; know which one you're making. A portability layer like Kubernetes
gets you portable compute, not portable everything — data services, IAM, and networking still
differ underneath. See `kubernetes-operations` for running that layer, and `cloud-architecture`
for the managed-vs-self-run tradeoff this decision is really an instance of.

**Done when:** the design's portability boundary — what's portable and what isn't — is explicit,
not assumed.

## 3. Budget the operational headcount, not just the cloud bill

Every additional provider means another IAM model to secure correctly, another network model to
reason about, another set of quotas and outage patterns to learn, and another on-call rotation
that needs to know all of it. This cost shows up as engineer-hours and incident response quality,
not as a line item — which is exactly why it's the cost teams underestimate before committing.

**Done when:** the ongoing staffing cost of the second provider has been estimated and accepted
by whoever owns the budget, not just the migration cost.

## 4. Audit for accidental multi-cloud regularly

Multi-cloud creeps in through acquisitions, a team standing up a proof-of-concept that never got
decommissioned, or a SaaS vendor's infrastructure counting as a dependency. Each of these carries
the same operational cost as a deliberate multi-cloud decision without anyone having made the
decision. Periodically inventory what's actually running where, including vendor and third-party
dependencies.

**Done when:** every provider workloads or critical dependencies run on is a known, current
entry in an inventory — not a surprise found during an audit.

## 5. Keep provider-specific abstractions thin and swappable, not universal

If portability across providers is a genuine requirement, build the abstraction at the boundary
where you actually need to swap — an interface around a queue, not a homegrown cloud-agnostic
platform that reimplements every provider's primitives. A thin, honest abstraction is
maintainable; a universal one becomes its own product with its own bug backlog. Manage the
underlying infrastructure per-provider with `infrastructure-as-code` and `terraform-modules`
rather than inventing a meta-layer above them.

**Done when:** any cross-provider abstraction is scoped to the specific component that needs to
move, not applied blanket across the stack.

## 6. Test the failover you're paying for

If disaster recovery across providers is the stated reason for multi-cloud, that failover must be
exercised, not assumed to work because it's architecturally possible. An untested cross-provider
failover is a more expensive version of an untested single-provider one, and multi-cloud DR that's
never been drilled is the most common way the "reason" from step 1 turns out to be fiction.

**Done when:** cross-provider failover has been executed in a drill within the last review cycle.

## Report

State the written reason for running on more than one provider, what is and isn't portable across
them, and the estimated ongoing operational cost. Name any workload or dependency running on a
second provider without a clear reason — that's the accidental multi-cloud the audit should have
caught, and it is more expensive than it looks.
