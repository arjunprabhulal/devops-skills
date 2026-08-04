# Building a Developer Portal

Mechanics referenced from the main skill: what a portal needs to actually do, how Backstage
usually serves as the reference implementation, how self-service provisioning wires through the
portal instead of living inside it, and the failure modes that kill portals before they earn
adoption.

## Contents

- The core capabilities, in priority order
- Backstage as the common reference implementation
- Self-service provisioning: portal, then pipeline, then IaC
- Measuring adoption, not existence
- Failure modes that kill portals
- Report

## The core capabilities, in priority order

A portal is not one feature — it is four, and they're usually built in the wrong order. Teams
reach for the scaffolder first because it's the visible part; the catalog is what makes everything
else useful, so it has to come first.

1. **Service catalog with ownership.** Every service, API, and resource has an entry with a named
   owning team, not a component floating with no accountable human. Without this, "who owns
   checkout-api" is a Slack archaeology exercise, and the other three capabilities have nothing to
   attach to.
2. **Software templates (the scaffolder).** The golden paths from `golden-paths` need a place
   developers can invoke them — a form, not a wiki page with a `git clone` command and seven
   manual follow-up steps.
3. **Tech docs, next to the code they describe.** Docs in a wiki drift within a quarter. Docs
   generated from a `docs/` folder in the same repo, published on merge, stay roughly true because
   updating them rides along with the same PR as the change.
4. **A plugin model.** Cost data, on-call status, deploy history, security posture don't belong
   bolted onto the catalog schema — they belong as plugins that read the catalog and render next
   to it, keeping the catalog itself small and stable.

**Done when:** a new hire can find who owns a service, spin up a new one from a template, and read
its docs, without asking in Slack.

## Backstage as the common reference implementation

Most teams don't design a catalog schema from scratch — they adopt Backstage's, because
`catalog-info.yaml` and its entity model are the closest thing the industry has to a standard.
Whether or not you run Backstage itself, its shape is worth copying.

```yaml
# catalog-info.yaml — lives in the service's own repo, next to the code
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: checkout-api
  annotations:
    github.com/project-slug: acme-corp/checkout-api
    backstage.io/techdocs-ref: dir:.
  tags: [payments, tier-1]
spec:
  type: service
  lifecycle: production
  owner: group:payments-team
  system: checkout
  dependsOn: [resource:checkout-db, component:payments-gateway-client]
```

`owner` and `lifecycle` matter most — an entry with no accountable team and no signal of whether
it's experimental or load-bearing is close to useless during an incident. Keep this file in the
service's own repo, not a central metadata repo, so it travels with the code.

A scaffolder template sketch for the same golden path — note it never calls a cloud API directly,
just creates a repo from a known-good skeleton and registers it:

```yaml
# template.yaml — registered in the portal as "Create > New Service"
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: new-node-service
  title: New Node.js Service (paved road)
spec:
  owner: group:platform-team
  parameters:
    - required: [name, owner]
      properties:
        name: { type: string, description: "Service name (kebab-case)" }
        owner: { type: string, description: "Owning team (must exist in the catalog)" }
  steps:
    - id: fetch
      action: fetch:template
      input: { url: ./skeleton, values: { name: "{{ parameters.name }}" } }
    - id: publish
      action: publish:github
      input: { repoUrl: "github.com?owner=acme-corp&repo={{ parameters.name }}" }
    - id: register
      action: catalog:register
      input: { catalogInfoPath: /catalog-info.yaml }
```

That boundary — no direct cloud calls — is the whole subject of the next section.

## Self-service provisioning: portal, then pipeline, then IaC

The most common design mistake is having the portal call the cloud provider directly — an action
that shells out to `aws` from inside the portal. That collapses review, state, and audit trail
into a UI click with no paper trail. The portal's job is to kick off a pipeline that runs
Terraform against the same review gates every other change goes through.

```
developer fills out template form
  -> portal (scaffolder) opens a PR: new service skeleton + Terraform module call
  -> CI pipeline: terraform plan, policy check, human/auto approval
  -> terraform apply, through the same pipeline every other infra change uses
  -> portal catalog registers the new entity, links back to the PR
```

This keeps the portal a front door, not a second infrastructure control plane — if it goes down,
infra changes still flow through the pipeline, because the pipeline was never portal-dependent. It
also means the escape hatch from `golden-paths` applies here too: a team that outgrows the
template can edit the generated Terraform directly and send it through the same pipeline, no
platform-team ticket required.

## Measuring adoption, not existence

A portal with a working catalog and zero organic usage is the same failure as no portal, plus
maintenance cost. Track these specifically, alongside the fuller toolkit in `developer-experience`:

- **Percentage of services with a real (non-default) catalog entry**, not registered as a
  formality during a mandated migration.
- **Percentage of new services created via the scaffolder** versus hand-rolled and registered
  after the fact — the second number says the templates don't match what people need.
- **Time-to-first-deploy for a service created through the portal**, versus the old manual path.
  If the portal isn't faster, it has no reason to win.
- **Doc page views and staleness** — a tech-docs tab nobody opens, or one two major versions out
  of date, means the plugin isn't earning its place either.

**Done when:** you can show a trend line of voluntary scaffolder usage climbing, not a mandate
memo announcing the portal is now required.

## Failure modes that kill portals

- **Building it before anyone asked, and no owner once it ships.** A portal stood up because
  "every platform team has one now" has no backlog of real pain to fix, and it shows: empty
  catalog, unused templates, office hours nobody attends. Left afterward to volunteers "when they
  have time," the schema drifts and plugins break on upgrade. Start from the discovery work in
  principle 1, and staff it like the permanent product it is, per principle 6.
- **Becoming a second source of truth that drifts.** The catalog is only worth trusting if it's
  validated against reality — ownership from CODEOWNERS, on-call from the paging tool, deploy
  status from the pipeline. Hand-maintained YAML nobody touches after the first commit becomes the
  stale wiki it was meant to replace, except now trusted by default.
- **Templates that outrun the golden paths they represent.** If `golden-paths` changes a paved
  road's defaults and the template isn't updated in lockstep, the portal hands out services built
  to a standard nobody endorses anymore. Treat template updates as part of the same change.

## Report

State which of the four core capabilities the portal actually delivers today versus which are
placeholders, whether provisioning flows through a pipeline or the portal talks to the cloud
directly, and the adoption numbers — scaffolder usage rate, time-to-first-deploy, catalog
freshness. Name which teams register services after the fact instead of through the template, and
why; that gap is usually the template's fault, not the team's.
