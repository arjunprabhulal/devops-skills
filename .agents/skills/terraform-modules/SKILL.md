---
name: terraform-modules
description: Covers designing Terraform modules that are reusable and composable rather than copy-pasted or over-engineered — clean input/output interfaces, version pinning, and knowing when abstraction earns its complexity. Use this whenever the user is writing a new module, designing variables and outputs, deciding whether to nest modules, pinning a module source to a version, or debating whether shared logic should become a module yet. For state and plan discipline see `infrastructure-as-code`, for blocking bad module usage before apply use `policy-as-code`.
license: MIT
---

# Terraform Modules

A module is a promise: call it with these inputs and it gives you these outputs, and you never
need to read its internals to trust it. That promise only holds if the interface is deliberately
designed, not just whatever variables happened to exist when the code was extracted from a
working root module.

The failure mode isn't usually too few modules — it's modules built too early, from a single
use case, whose interface is a guess dressed up as an abstraction.

**A module's job is to hide detail behind an interface, not to hide detail behind a maze.**

## 1. Wait for the third repetition before you extract

The first time you write a VPC config, it's a root module. The second time, resist the urge — you
don't yet know which parts vary and which are load-bearing constants. By the third real call
site, the variance is visible: you know what actually needs to be a parameter versus what was
just an artifact of one environment's choices.

- **Extracting from one example bakes in that example's assumptions** as if they were general
  requirements.
- **Extracting from three exposes the real interface** — the inputs that differ are the ones that
  need to be variables; everything else can be a sane default or hardcoded.

**Done when:** the module's variable list was derived from comparing multiple real call sites,
not authored speculatively for cases that don't exist yet.

## 2. Design the interface like a public API, not an implementation detail

Every variable and output is a contract with every future caller. A module with forty required
variables and no defaults isn't flexible — it's a burden that guarantees every caller gets it
slightly wrong.

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment: dev, staging, or prod."
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}
```

- **Give every variable a description and, where possible, a sane default** — required inputs
  should be the genuinely essential ones, not everything the resource block happens to expose.
- **Validate inputs at the module boundary** rather than letting a bad value surface as a cryptic
  provider error three resources deep.
- **Expose outputs callers actually need**, not every attribute of every internal resource —
  a wide output surface leaks implementation and makes refactors breaking changes.

**Done when:** a new caller can use the module correctly by reading `variables.tf` and
`outputs.tf` alone, without opening `main.tf`.

## 3. Pin versions, don't float on `main`

A module source pointing at a Git branch or an unpinned registry version means every consumer
gets whatever the module author pushed today, including bugs, silently, on their next `init`.
That's the same class of risk as an unpinned base image — see `immutable-infrastructure` for the
image-side version of this problem.

- **Pin to an exact version or Git tag**, never a floating branch reference.
- **Bump deliberately**, reading the module's changelog, not as a side effect of an unrelated
  `terraform init -upgrade`.
- **Tag module releases with semver** if you're the one publishing them, and treat a breaking
  interface change as a major version bump.

**Done when:** every module source in the codebase resolves to a pinned, immutable version, not
a mutable ref.

## 4. Keep nesting shallow

A module that calls a module that calls a module is hard to debug — a plan error three layers
down forces the reader to trace variables through every intermediate layer to find where a value
actually originates. Depth doesn't buy reuse; it buys indirection.

- **Prefer a flat set of focused modules composed at the root** over deeply nested hierarchies.
- **If a module only ever wraps a single other module with no added logic**, it's not adding
  value — inline it or delete it.
- **Two levels of nesting is a reasonable ceiling** for most estates; a third level needs a
  specific justification, not just "it seemed organized."

**Done when:** tracing any output back to its source resource takes at most two hops through
module boundaries.

## 5. Separate the module registry from the environment wiring

A module should have no idea whether it's being called for dev or prod — that distinction belongs
in the calling root module's `.tfvars`, not baked into conditional logic inside the module
itself. A module littered with `count = var.environment == "prod" ? 1 : 0` is really two modules
pretending to be one.

**Done when:** no module source file references an environment name directly — all
environment-specific behavior comes in through variables set by the caller.

## 6. Test modules the same way you test code

A module without a test is only validated by whoever calls it first, in whatever environment
they happen to be applying to — often production. Use `terraform test`, Terratest, or a
plan-only CI check against a fixed set of example inputs before publishing a change. See
`infrastructure-testing` for the broader discipline this belongs to.

**Done when:** every published module has at least one automated test that applies it with
representative inputs and asserts on the resulting plan or real resources.

## Report

State which modules exist, what real call sites justified each one, and whether their sources are
version-pinned across the codebase. Name the honest gap — usually a module extracted too early
from a single caller, an unpinned source still floating on a branch, or a module with no test —
rather than presenting the module library as fully mature.
