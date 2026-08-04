---
name: resource-tagging
description: Builds a tag taxonomy for cost, ownership, and automation, enforces it at provision time so it never depends on discipline after the fact, and uses it to drive cost allocation, showback, and the hunt for untagged waste. Use this whenever the user is designing tag keys or naming conventions, asking who owns a resource or why a bill can't be attributed to a team, setting up cost allocation, or finding resources that escaped a tagging policy. For turning tags into dollar decisions use `cost-optimization`, and for the budgets tags feed into use `cloud-budgeting`.
license: MIT
---

# Resource Tagging

A tag is metadata that answers a question someone will ask later: who owns this, what does it
cost, can it be deleted, does it run in production. Most tagging efforts fail not because tags are
hard to write but because they're optional — added when someone remembers, skipped under deadline
pressure, and drifted from reality within a quarter. A tag that isn't enforced is a suggestion, and
a suggestion doesn't survive contact with a deadline.

The payoff for tagging discipline isn't the tags themselves — it's every downstream capability
that depends on them: cost allocation, ownership lookup, automated cleanup, and policy scoping all
break silently when tags are missing or wrong.

**A tag that isn't enforced at creation time will be missing by the time you need it.**

## 1. Design a small taxonomy before you enforce anything

A taxonomy with twenty required keys guarantees a low compliance rate, because every optional
field is a place for a provisioning pipeline to skip a step under time pressure. Start with the
handful of keys that answer the questions actually asked — owner, cost center, environment,
service — and add more only when a real use case demands it.

| Key | Answers |
|---|---|
| `owner` | Who to page or ask before deleting this |
| `cost-center` | Which budget this rolls up to |
| `environment` | prod / staging / dev — safe to tear down? |
| `service` | Which system this belongs to |

**Done when:** the required tag set is short enough that no team has a plausible excuse for
skipping one.

## 2. Enforce tags at provision time, not after the fact

A tagging policy that's checked by a nightly report finds violations a day late, after the
resource is already running untracked. Enforcing required tags in the provisioning path — Terraform
policy checks, admission control, or the cloud provider's native tag policies — rejects the
untagged resource before it exists rather than flagging it after the fact.

- **Fail the provisioning step**, don't just warn, when a required tag is missing.
- **Default where safe** — an environment tag can often be inferred from the pipeline that
  deployed it, reducing what a human has to type.
- **Apply the same enforcement to manual console changes** as to automated pipelines, or the
  policy only covers the traffic that was already disciplined.

See `policy-as-code` for how to express and gate on rules like this.

**Done when:** a resource missing a required tag cannot be created through any normal path.

## 3. Make cost allocation and showback the payoff, not the goal

Tagging for its own sake doesn't motivate anyone to keep it accurate. Tagging that visibly drives
"here's what your team spent this month" gives every tagged team a reason to keep their tags
correct, because inaccurate tags now cost them a wrong number on their own dashboard.

- **Publish per-team or per-service cost views** derived directly from tags, not from a
  separately-maintained spreadsheet.
- **Route the untagged-and-unattributed bucket to a visible owner** — someone should feel the pain
  of the resources nobody claimed.

**Done when:** every team can see a cost view of their own resources, derived from tags, without
asking finance to run a special report.

## 4. Hunt down untagged and mistagged resources on a schedule

Enforcement at provision time stops new drift but does nothing for what predates the policy, and
enforcement itself will have gaps — a manual change, an API call outside the normal path, an
acquired account. A recurring sweep for untagged and inconsistently-tagged resources is what
catches what enforcement missed.

- **Scan for missing required tags** and for tag values that don't match the taxonomy (`Prod` vs
  `production`).
- **Assign an expiry to remediation**, not an open-ended backlog item nobody owns.

**Done when:** the untagged-resource count is tracked over time and trending down, not discovered
fresh in every audit.

## 5. Treat tag values as data with an owner, not free text

Free-text tag values fragment into synonyms — `prod`, `Production`, `PROD` — that break every
downstream rollup relying on exact matches. Constraining values to an enumerated list, validated
at provision time, keeps the taxonomy usable years later instead of decaying into a pile of
near-duplicates nobody trusts enough to query.

**Done when:** every required tag key has an enumerated or validated value set, not free text.

## Report

State the taxonomy's required keys, the enforcement mechanism used, and the current tag-compliance
rate across the estate. Name the honest gap — usually a class of resource the provisioning
enforcement doesn't reach yet (manually-created resources, an acquired account, a legacy system)
— rather than claiming full coverage.
