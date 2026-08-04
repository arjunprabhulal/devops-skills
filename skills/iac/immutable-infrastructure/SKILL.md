---
name: immutable-infrastructure
description: Covers replacing servers wholesale instead of patching them in place — baking golden images, treating instances as disposable cattle rather than nursed pets, rebuilding to make any change, and the rollback simplicity that buys. Use this whenever the user is deciding whether to SSH into a running instance to fix it, building an AMI or container image as a deployment unit, debugging config drift on a long-lived server, or arguing for or against in-place patching. For hosts that must stay mutable use `configuration-management`, for image build mechanics use `containerization`.
license: MIT
---

# Immutable Infrastructure

Every server that's ever been SSH'd into to fix something is now a unique, undocumented artifact
— its actual state exists only on that machine, not in any repo. Multiply that by a fleet and
you get servers that have quietly diverged from each other in ways nobody can enumerate,
discovered only when one of them fails differently than the rest.

Immutable infrastructure closes that gap by removing the option: nothing is ever changed on a
running instance. To make a change, you build a new image and replace the instance that's
running the old one. There is no in-place path, so there's no drift to accumulate.

**Servers are cattle, not pets — you don't nurse a sick one back to health, you replace it and
move on, and the fact that you can tell them apart at all is the bug.**

## 1. Bake the change into the image, never onto the running instance

The rule is absolute, not a preference: if a change needs to happen, it happens in the image build
pipeline, and a new instance rolls out. SSH access for routine changes shouldn't just be
discouraged — the access itself should be hard to get, because the two-second fix under pressure
is exactly how drift gets reintroduced.

- **Remove standing SSH access for config changes** — break-glass access for genuine incident
  debugging is different from routine access for "quick fixes."
- **Automate every provisioning step in the image build**, so nothing about a running instance
  depends on a human having remembered to run a command against it.
- **Treat any manual change discovered on a running instance as an incident**, not a shortcut that
  saved time — it means the image no longer describes reality.

**Done when:** no instance in the fleet has ever received a change that isn't also in the image it
was built from.

## 2. Build the golden image the same way every time, from a pipeline

A golden image is only trustworthy if it's reproducible — built by a pipeline from a versioned
definition (Packer template, Dockerfile, or equivalent), not assembled once by hand and then
snapshotted. A hand-built image is a pet wearing a cattle costume.

```hcl
# packer template excerpt
source "amazon-ebs" "app" {
  ami_name      = "app-{{timestamp}}"
  instance_type = "t3.medium"
  source_ami_filter { ... }
}
build {
  sources = ["source.amazon-ebs.app"]
  provisioner "shell" { script = "provision.sh" }
}
```

- **Version every image build** and tag it with the commit it was built from, so any running
  instance can be traced back to exact source.
- **Rebuild from a clean base every time**, never by patching a previous image in place — the same
  cattle principle applies one level up, to the image itself.
- **Scan the image before it's promoted** — see `image-scanning` for the vulnerability-scanning
  step this pipeline should include.

**Done when:** every image in use can be traced to a specific pipeline run and source commit, and
rebuilding from that commit reproduces an equivalent image.

## 3. Replace instances to deploy, don't reconfigure them

Deploying a change means launching new instances from the new image and retiring the old ones —
via a rolling update, blue-green swap, or autoscaling group refresh — not pushing new config to
instances that keep running. See `deployment-strategies` for the mechanics of how that rollout
happens safely at the traffic-shifting level.

- **Let the orchestrator (ASG, Kubernetes, managed instance group) drive the replacement**,
  rather than scripting instance-by-instance in-place updates.
- **Terminate old instances only after new ones pass health checks**, never on a timer that
  assumes success.

**Done when:** a deploy is observable as a set of new instance IDs replacing a set of old ones,
with no instance ID persisting across a deploy that changed its content.

## 4. Treat rollback as re-deploying the previous image, nothing more

The biggest practical payoff of immutability is that rollback stops being a special, scary
procedure — it's the same replace-the-fleet mechanism, pointed at the previous known-good image
instead of the new one. There's no "undo the last three config changes" reasoning to do, because
there were never in-place changes to undo.

**Done when:** rolling back to the prior release requires no more than re-triggering the same
deploy path against the previous image tag.

## 5. Externalize anything that must persist

Instances are disposable, but data usually isn't — a database, uploaded files, or session state
baked into local disk vanishes the moment the instance is replaced. Push persistent state onto
managed, externally-attached storage (a managed database, object storage, a network volume) so
replacing the compute layer never risks the data layer. See `stateful-workloads` for handling the
minority of components that genuinely can't be made stateless this way.

**Done when:** terminating any instance in the fleet, without warning, causes no data loss.

## 6. Know when a host genuinely needs to stay mutable

Not everything belongs on this model — a handful of legacy systems or specialized appliances
can't be cleanly re-imaged on every change without disproportionate cost. For those, converge
them deliberately with configuration management instead of pretending they're immutable while
secretly patching them by hand. See `configuration-management` for that model and how to choose
between the two honestly.

**Done when:** every host that isn't immutable has been explicitly designated as such, with a
config-management process, rather than being an accidental exception nobody decided on.

## Report

State which fleets are fully immutable, how images are built and versioned, and what (if
anything) still receives in-place changes. Name the honest gap — usually a lingering SSH access
path used "just this once," a legacy host quietly mutated outside the image pipeline, or state
that isn't yet externalized off an instance that gets replaced — rather than claiming the whole
estate is cattle.
