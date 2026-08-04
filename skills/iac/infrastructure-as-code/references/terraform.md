# Terraform / OpenTofu Specifics

Mechanics referenced from the main skill: how to actually read a plan, work with state, back it
remotely, force a deliberate replacement, and catch drift. The commands below are Terraform CLI;
OpenTofu is a drop-in swap of the binary name unless noted.

## Contents

- Reading a plan
- Saving and applying a plan file
- State operations
- Remote backend with locking and encryption
- Deliberate recreation with `-replace`
- Drift detection with `-detailed-exitcode`
- Guarding data with `prevent_destroy` and provider deletion protection
- Pinning providers, modules, and the lock file

## Reading a plan

Every line in a plan starts with a symbol. Scan for the dangerous ones first — `+` is almost
always fine to skim past, `-/+` is the one that silently destroys data if you're not paying
attention.

| Symbol | Meaning | Danger |
| --- | --- | --- |
| `+` | Create | Low — new resource, nothing existing is touched |
| `~` | Update in place | Usually low — check *which* attribute changed |
| `-` | Destroy | High — resource and its data are gone |
| `-/+` | Destroy, then create (forces replacement) | Highest — looks like an update but is a delete; state, IDs, and any data the old resource held do not survive |
| `<=` | Read (data source) | Low — no infrastructure changes, just a lookup |

`-/+` is the one that bites people, because the resource block in the diff often looks almost
identical to what's already there — a single changed argument (an AMI ID, an `availability_zone`
on an EBS-backed instance) can force a full replacement even though nothing about the *intent*
changed. Terraform tells you why with a comment on the offending attribute, not the whole block:

```
  # aws_instance.web must be replaced
-/+ resource "aws_instance" "web" {
      ~ ami = "ami-0abc" -> "ami-0def" # forces replacement
```

## Saving and applying a plan file

Never let `apply` re-plan on its own — the plan you reviewed should be the exact plan that runs.

```bash
terraform plan -out=tfplan
# ... read the output, get it reviewed ...
terraform apply tfplan
```

Applying a saved plan file skips re-evaluation, so nothing slips in between review and apply — no
changed variable, no upstream state drift, no different provider version. If too much time passes
between the two commands, Terraform refuses to apply a stale plan rather than apply something
nobody actually reviewed.

## State operations

State commands operate on the source of truth for what Terraform thinks exists — treat them as
deliberate surgery, not routine housekeeping.

```bash
terraform state list                          # every resource address in state
terraform state show aws_instance.web         # full attributes of one resource
terraform state mv aws_instance.web aws_instance.app   # rename without destroy/recreate
terraform state rm aws_instance.web           # stop tracking it — does NOT delete the real resource
terraform import aws_instance.web i-0abc123   # start tracking a resource that already exists
```

`state mv` renames a resource or moves it into a module without Terraform reading the rename as a
destroy-then-create. `state rm` only removes Terraform's *bookkeeping* — the real infrastructure is
untouched and now unmanaged, so use it for an intentional handoff, not as a shortcut past an error.
`import` is the reverse: bring something created out-of-band under management. It only populates
state — you still have to write the matching resource block, or the next plan proposes destroying
what you just imported.

## Remote backend with locking and encryption

Local state fails both rules in the main skill at once — it isn't remote and nothing stops two
applies from racing. An S3 backend with a DynamoDB lock table (or S3 native locking on newer
Terraform versions) fixes both:

```hcl
terraform {
  backend "s3" {
    bucket         = "acme-tfstate-prod"
    key            = "networking/terraform.tfstate"   # scope per component, per environment
    region         = "us-east-1"
    dynamodb_table = "tfstate-locks"   # a second apply against this key blocks, doesn't race
    encrypt        = true              # SSE on the state object itself
  }
}
```

`dynamodb_table` is the lock; `encrypt` protects the plaintext secrets that routinely end up in
state even when the source `.tf` files never mention them. Give each environment its own `key` (or
bucket), per the one-state-per-environment rule.

## Deliberate recreation with `-replace`

Sometimes you *want* the destroy-then-create — a corrupted instance, a secret that needs full
rotation, a resource stuck in a bad state no in-place update fixes. Don't hand-edit state to force
it; tell plan what to replace and read the diff like any other plan:

```bash
terraform plan -replace="aws_instance.web" -out=tfplan
terraform apply tfplan
```

This produces the same `-/+` line as an accidental forced replacement, but now it's one you asked
for and reviewed — the goal is making the destructive step visible and intentional, not a side
effect of an unrelated attribute change.

## Drift detection with `-detailed-exitcode`

A plain `plan` always exits 0 whether or not anything changed, which makes it useless for scripted
drift checks. `-detailed-exitcode` turns the exit code itself into the signal — wire it straight
into the scheduled job from the main skill's drift-detection practice:

```bash
terraform plan -detailed-exitcode -out=drift.tfplan
case $? in
  0) echo "clean" ;;                          # no changes, state matches reality
  1) echo "plan failed" >&2; exit 1 ;;         # the job itself is broken, investigate
  2) echo "drift detected" >&2; notify-team ;; # changes pending — go look before reconciling
esac
```

## Guarding data with `prevent_destroy` and provider deletion protection

Two layers, because they catch different mistakes. `prevent_destroy` stops Terraform itself from
issuing the delete; provider-level deletion protection stops anyone — Terraform, console, another
tool — from deleting the underlying resource at all.

```hcl
resource "aws_db_instance" "primary" {
  # ...
  deletion_protection = true   # AWS refuses the delete API call, full stop

  lifecycle {
    prevent_destroy = true     # terraform apply/destroy refuses to even propose it
  }
}
```

`prevent_destroy` only blocks Terraform-driven destroys — someone deleting the resource by hand in
the console isn't stopped by it. `deletion_protection` closes that gap. Use both on primary
databases, KMS keys, and anything else with no upstream source of truth to recreate from.

## Pinning providers, modules, and the lock file

An unpinned provider or module version means the exact same configuration can produce a different
plan tomorrow than it did today — the opposite of IaC's promise that the repo is the source of
truth.

```hcl
terraform {
  required_version = "~> 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"   # patch upgrades only, deliberately via `init -upgrade`
    }
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.8.1"   # exact, not a range — a third-party module's changes aren't yours to review
}
```

**Commit `.terraform.lock.hcl`.** It records the exact provider versions and checksums that were
actually used, so `init` on a teammate's laptop or in CI resolves to the identical bits, not just a
version that satisfies the same constraint. Treat it like a regular lock file — update it
intentionally via `-upgrade`, review the diff, don't hand-edit it.
