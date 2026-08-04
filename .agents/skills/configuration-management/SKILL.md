---
name: configuration-management
description: Covers Ansible, Chef, and Puppet for managing mutable systems declaratively — idempotent tasks, convergence toward desired state instead of one-off scripts, inventory organization, and roles. Use this whenever the user is writing a playbook, cookbook, or manifest, debugging why a run isn't converging, organizing hosts into an inventory, or deciding whether a fleet should be config-managed or replaced wholesale. For replacing servers instead of mutating them use `immutable-infrastructure`, for provisioning the underlying resources use `infrastructure-as-code`.
license: MIT
---

# Configuration Management

A shell script installs a package. A configuration management tool declares that the package
should be installed — and then checks, every time it runs, whether that's already true before
doing anything. That distinction is the entire value: a script run twice can fail or duplicate
work, but a well-written playbook run a hundred times against a host that's already correct does
nothing at all, safely.

Ansible, Chef, and Puppet exist to describe *desired state*, not a sequence of steps. The moment
a task is written as an imperative command instead of a declared outcome, that guarantee is gone.

**If running the same playbook twice changes anything the second time, it isn't idempotent — and
if it isn't idempotent, it isn't safe to run in a hurry, which is exactly when you'll need to.**

## 1. Write tasks that declare an outcome, not a command

`command: apt-get install -y nginx` runs every time, whether or not nginx is already there, and
Ansible has no way to know if it changed anything. The `apt` or `package` module, by contrast,
checks state first and reports back "changed" or "ok" honestly.

```yaml
- name: Ensure nginx is installed and running
  apt:
    name: nginx
    state: present
- name: Ensure nginx is enabled and running
  service:
    name: nginx
    state: started
    enabled: true
```

- **Prefer the module over the raw shell command** whenever one exists for the resource type —
  package, file, service, user — because the module already encodes the idempotency check.
- **When a shell command is unavoidable**, add an explicit `creates:`, `changed_when:`, or
  equivalent guard so the run can still report truthfully.
- **Treat every "changed" in a run against an already-configured host as a bug to investigate**,
  not background noise.

**Done when:** running the playbook twice in a row against the same host reports zero changes on
the second run.

## 2. Model the fleet as an inventory, not a list of one-off hosts

Configuration management earns its keep at scale, and that requires hosts to be grouped by role
and environment so a change can target "all web servers in staging" instead of a hand-maintained
list of IPs someone has to update every time a server is added or removed.

- **Use dynamic inventory** sourced from the cloud provider or CMDB wherever possible, so the
  inventory can't drift from what actually exists.
- **Group by function and environment**, and layer variables accordingly — defaults at the group
  level, overrides only where a specific host genuinely needs one.
- **Never hardcode a host's role into a play** — the inventory group should carry that meaning,
  so the same play works unchanged as the fleet grows.

**Done when:** adding or removing a host requires no edit to any playbook, only an inventory
change.

## 3. Package reusable logic as roles, and give each role one job

A role that configures nginx, sets up log rotation, and hardens SSH all at once can't be reused
for a host that needs only one of those things, and it's harder to test in isolation. Roles are
the module system of configuration management — see `terraform-modules` for the equivalent
discipline in Terraform, though the composition mechanics differ.

- **One role, one responsibility** — `nginx`, `log-rotation`, `ssh-hardening` as separate roles
  composed together on a host, not merged into one.
- **Parameterize with role variables that have sane defaults**, so applying a role without
  overrides still produces a working, sensible result.
- **Version and share roles that are genuinely reused** across projects via Galaxy, Puppet
  Forge, or an internal registry, pinned the same way you'd pin a Terraform module source.

**Done when:** each role can be applied to a fresh host on its own and produce a correct,
working result without depending on another role having already run.

## 4. Converge toward state, don't script a migration path

The instinct when a host is in an unknown state is to write a script that walks it from wherever
it is to where it should be. Configuration management inverts that: declare where it should end
up, and let the tool figure out what, if anything, needs to change. This is what makes it safe to
run against a fleet in mixed, unknown states — a freshly imaged host and a three-year-old one
converge to the same result from the same playbook.

**Done when:** the same playbook can be run unmodified against a brand-new host and an
existing, drifted one, and both end up in the identical target state.

## 5. Know when config management is the wrong tool

Configuration management manages long-lived, mutable hosts well. It manages the problem of "this
host has drifted and I need to reconcile it" — a problem that doesn't exist at all if hosts are
never mutated after boot. If the fleet is autoscaled, frequently replaced, or the goal is a
byte-identical fleet, baking a golden image and replacing rather than converging is usually
simpler and more reliable. See `immutable-infrastructure` for that model and how to decide
between the two.

**Done when:** the choice between config management and image-baking for this fleet is a
documented decision, not a default nobody reconsidered.

## 6. Test playbooks against a real target before trusting them in production

A playbook that's only ever been run manually against production is a playbook that's never
actually been tested — it's been performed. Run it in CI against a container or ephemeral VM,
asserting both that the first run converges and the second run is a no-op. See
`infrastructure-testing` for the broader pattern this fits into.

**Done when:** every playbook change runs through an automated convergence test before it's
applied to a real fleet.

## Report

State which roles and playbooks exist, what inventory groups they target, and whether idempotency
was verified with a two-run test. Name the honest gap — usually a play still using raw shell
commands without change guards, an inventory that's manually maintained instead of dynamic, or a
fleet that was never evaluated against the immutable-infrastructure alternative — rather than
implying the whole fleet reliably converges.
