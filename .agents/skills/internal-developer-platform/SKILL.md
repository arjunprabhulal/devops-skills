---
name: internal-developer-platform
description: Designs an internal developer platform (IDP) as a product for one customer — engineers — with paved roads, self-service workflows, and abstractions that speed people up without hiding the levers they need during an incident. Use this whenever the user is scoping a platform team's roadmap, deciding what to abstract versus expose, evaluating Backstage or a platform orchestrator, or arguing how much Kubernetes/Terraform detail developers should see. For what the platform hosts use `service-catalog`; for its templates use `golden-paths`; for measuring it use `developer-experience`.
license: MIT
---

# Internal Developer Platform

An IDP is not "Kubernetes with a UI bolted on." It is a product, built by a team, for one customer
segment: the engineers who have to ship through it every day. Platform teams that forget this build
infrastructure nobody asked for, then wonder why adoption stalls and shadow processes reappear.

The test of a good IDP is not how much it automates — it's whether developers choose to use it when
they don't have to. **A platform earns adoption by being the fastest path to done, not the only
path allowed.**

For standing up a portal — catalog, scaffolder templates, and adoption metrics — read
`references/building-a-portal.md`.

## 1. Treat the platform as a product with real users

A platform team without a backlog driven by user pain is building what it finds interesting, not
what unblocks people. Run discovery the way a product team does: interview the teams you serve,
watch where they get stuck, and prioritize by how many people a fix unblocks and how often. A
roadmap set by the platform team's own architectural preferences, with no developer input, is the
single most common reason IDPs get built and then quietly bypassed.

- **Assign a product owner**, not just a tech lead — someone accountable for adoption, not uptime.
- **Run office hours or a feedback channel** that's actually staffed, not a ticket queue that ages.
- **Kill features nobody uses** instead of maintaining them out of sunk-cost loyalty.

**Done when:** the platform roadmap traces every item back to a specific, named developer pain
point, not an internal architecture goal.

## 2. Pave the road people are already taking

Look at how teams actually deploy, configure, and debug today — including the workarounds — before
designing the "right" way. The paved road that wins is the one that matches how good teams already
work, just with the toil removed; a paved road invented from scratch in a vacuum competes with real
habits and usually loses. The curated templates and defaults themselves belong to `golden-paths` —
this skill is about the platform that hosts and enforces them, not their contents.

**Done when:** the first paved-road template you ship is modeled on an existing team's working
setup, not a greenfield ideal.

## 3. Abstract the plumbing, not the judgment calls

Good abstraction removes repetitive, low-judgment work — provisioning a namespace, wiring up a
load balancer, registering a DNS name. Bad abstraction removes the ability to understand what's
running when something breaks at 2 a.m. If a developer can't answer "what actually happens when I
click deploy" in one sentence, the platform has hidden something it shouldn't have.

- **Show the generated manifest**, don't just apply it silently — link to the Terraform plan or
  Kubernetes YAML the platform produced.
- **Keep debugging primitives available**: logs, `kubectl`, and direct dashboard access should
  never require a platform-team ticket to reach.
- **Never abstract security boundaries** into invisibility — see `policy-as-code` for keeping
  guardrails legible instead of magic.

**Done when:** a developer can explain what infrastructure their service actually runs on without
asking the platform team.

## 4. Ship an escape hatch with every paved road

Every abstraction will eventually meet a use case it wasn't built for. If the only way off the
paved road is a platform-team exception request, you've built a wall, not a road. Provide a
documented, supported way to drop to the underlying primitive — raw Terraform, a direct Helm
chart — for the cases the golden path doesn't cover, and treat frequent escapes as a signal the
paved road needs to widen, not a compliance failure to punish.

**Done when:** at least one real team has used the escape hatch successfully without opening a
ticket to the platform team.

## 5. Measure adoption, not mandate compliance

A platform used because it's required tells you nothing about whether it's good; a platform used
because it's genuinely faster tells you everything. Track voluntary usage, time-to-first-deploy for
a new service, and how often developers route around the platform. See `developer-experience` for
the fuller measurement toolkit — DORA metrics and beyond — this platform is what those numbers are
measuring the effect of.

**Done when:** you can name the percentage of new services onboarded voluntarily versus by mandate,
and the trend is moving toward voluntary.

## 6. Fund and staff it as permanent infrastructure

A platform team stood up as a temporary project, then reassigned once the initial build ships,
leaves developers with unowned infrastructure that silently rots — dependencies stop updating,
paved roads stop matching current best practice, and trust erodes faster than it was built. Staff
the platform team like you'd staff any other product with an install base: ongoing roadmap,
on-call, and a deprecation process for old paved roads.

**Done when:** the platform has a named on-call rotation and a deprecation policy for retiring old
templates, not just a launch date.

## Report

State what the platform currently hosts, the paved roads it enforces versus merely suggests, the
escape hatch mechanism, and the adoption numbers you're tracking. Name honestly which teams are
still working around the platform instead of through it, and why — that gap is the real roadmap,
and naming it beats claiming full adoption.
