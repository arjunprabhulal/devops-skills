---
name: infrastructure-as-code
description: Treats infrastructure changes as version-controlled, reviewable configuration instead of manual clicks or SSH sessions — Terraform state, plan review, environment parity, and guardrails against irreversible changes. Use this whenever the user is writing or reviewing Terraform, CloudFormation, or Pulumi code, applying infrastructure changes, managing remote state, or asking why an environment drifted from what's declared. For module design use `terraform-modules`, for blocking bad changes before apply use `policy-as-code`, for dev/staging/prod differences use `environment-management`.
license: MIT
---

# Infrastructure as Code

The value of IaC isn't that it's faster than clicking through a console — it's that the
configuration file is the single source of truth, and anyone can read it to know what the
system actually is without logging into anything. The moment someone makes a change out of
band, that promise breaks, and every plan after it lies a little.

Terraform is the default lens here because it's the common ground across clouds, but the
discipline applies equally to CloudFormation, Pulumi, or Bicep.

**If the state of the system can't be reconstructed by reading the repo, it isn't infrastructure
as code — it's infrastructure with extra steps.**

For Terraform specifics — plan symbols, state operations, backends, forced replacement, and drift
detection — read `references/terraform.md`.

## 1. Read every plan before you apply it

`terraform plan` exists so nobody has to trust their own diff — read the actual output, every
time, even for changes that feel trivial. The plan is the one place a typo becomes visible before
it becomes an incident: a renamed resource that Terraform reads as destroy-then-create, a
provider default that shifted, a variable that resolved to something unexpected.

- **Look for destroy and replace, not just create** — those are the operations with a blast
  radius, and they hide easily in a long plan.
- **Treat "no changes" as a result to verify, not skip** — if you expected a change and got none,
  something upstream is wrong.
- **Never apply a plan you didn't personally read**, even in CI — a human or a policy gate (see
  `policy-as-code`) should see the diff before it lands.

**Done when:** every apply was preceded by a plan that a person actually read, not just approved
by habit.

## 2. Protect state like it's a production database, because it is

Terraform state is the map between your configuration and real-world resource IDs. Lose it, and
you haven't lost a file — you've lost the ability to manage anything without manual reconciliation.
Corrupt it with a concurrent write, and two applies can fight over the same resource.

- **Store it remotely**, never on a laptop or in the repo, so it survives any one machine.
- **Lock it** so two applies can't run against the same state simultaneously and corrupt it.
- **Encrypt it at rest** — state routinely contains secrets in plaintext (database passwords,
  keys) even when the source config never does.
- **Keep one state file per environment**, not one giant state shared across dev, staging, and
  prod — a bad apply in dev should never be able to touch prod's resources.

**Done when:** state is remote, locked, encrypted, and scoped one-per-environment, with no
history of a local `.tfstate` file ever being committed or emailed around.

## 3. Make environments differ by values, not by forking the code

The first time someone copies a module directory to make a "staging version," the two copies
start drifting the moment either one is edited alone. The environments are supposed to be the
same system at different sizes — the code should say so.

```hcl
# environments/staging.tfvars
instance_count = 2
instance_type  = "t3.medium"
# environments/prod.tfvars
instance_count = 6
instance_type  = "m5.xlarge"
```

One module, one set of `.tf` files, and a `.tfvars` file per environment. See
`environment-management` for the fuller promotion and parity story — this is the mechanical
enabler of it.

**Done when:** creating a new environment means adding a values file, not copying and editing a
directory of resource definitions.

## 4. Put a manual gate in front of anything irreversible

Most changes — adding a server, resizing a queue — are cheap to undo if wrong. A few are not:
dropping a database, deleting a bucket with `force_destroy`, or shrinking a cluster below what a
stateful workload needs. Automation should treat those differently from everything else.

- **Require explicit human approval** for any plan containing a destroy of stateful resources.
- **Set `prevent_destroy` on anything that can't be cheaply recreated** — primary databases,
  KMS keys, anything holding data with no upstream source of truth.
- **Never let a routine pipeline run `terraform destroy` unattended**, even in non-prod, without
  a separate confirmation step.

**Done when:** every irreversible resource has a lifecycle guard or a required manual approval
standing between a plan and its apply.

## 5. Extract a module only once repetition proves it, not before

Copy-pasting the same 20 lines into a third resource is the signal to modularize — not the first
time you write it, and often not even the second. A module built from one use case guesses at an
interface; a module built from three real ones has an interface backed by evidence. See
`terraform-modules` for how to design the interface once you're actually there.

**Done when:** every module in the repo can point to at least two real call sites that justified
its extraction, not a single speculative one.

## 6. Run drift detection on a schedule, not just when something breaks

Config declares the intended state, but consoles, CLIs, and other teams' scripts can still change
the real one. Without a scheduled `plan` run comparing intent to reality, drift accumulates
silently until an apply surfaces it as a surprise diff touching things nobody meant to change.

- **Run a read-only plan on a cron** (daily is reasonable) against every environment's state.
- **Alert on any non-empty diff**, not just failures — an unexpected diff is itself the finding.
- **Reconcile drift by importing or by re-applying**, but always investigate who or what caused it
  before just overwriting it away.

**Done when:** a scheduled job reports diff-or-clean on every environment, and someone actually
looks at the diffs.

## Report

State which environments have remote, locked, encrypted state, whether irreversible resources are
guarded, and the outcome of the most recent scheduled drift check. Name the honest gap — usually
an environment still on local state, a lifecycle guard that was never added, or drift detection
that isn't wired up yet — rather than implying the whole estate is fully reconciled.
