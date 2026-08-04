# DevOps Skills

[![validate-skills](https://github.com/arjunprabhulal/devops-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/arjunprabhulal/devops-skills/actions/workflows/ci.yml)
[![Skills](https://img.shields.io/badge/skills-88-informational)](#skills)
[![Categories](https://img.shields.io/badge/categories-15-informational)](#skills)
[![Evals](https://img.shields.io/badge/evals-264-informational)](docs/evals.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

DevOps field guides an AI agent loads on demand — 88 skills spanning the lifecycle: CI/CD,
containers, Kubernetes, infrastructure as code, cloud, GitOps, observability, reliability,
security, networking, data, platform engineering, automation, FinOps, and performance.

Each skill is a single `SKILL.md` file covering one job, loaded when the task matches. The
`description` frontmatter states when to reach for the skill and which sibling skill to use
instead; the body walks through the work in numbered steps, each ending in a concrete
`Done when:` checkpoint; the closing `Report` section states what was decided and what the skill
does not cover.

Skills name tools as examples rather than requirements, so they apply across providers. The cost of
that choice is that a skill will reason through a decision with you, but will not hand you a
finished vendor-specific config.

## Install

```bash
# Claude Code, as a plugin
/plugin marketplace add arjunprabhulal/devops-skills
/plugin install devops-skills@arjunprabhulal

# Any harness, via the skills CLI
npx skills add arjunprabhulal/devops-skills

# A single skill, by hand
cp -r skills/kubernetes/kubernetes-operations ~/.claude/skills/
```

Google Antigravity reads the prebuilt flat tree at `.agents/skills/`. See
[docs/installation.md](docs/installation.md) for every route, verification, and uninstalling.

## What a skill looks like

The frontmatter that decides when the skill triggers, and one of the six steps, from
[`incident-response`](skills/reliability/incident-response/SKILL.md). The intro and the other five
steps are elided:

````markdown
---
name: incident-response
description: Runs a live incident from first alert to resolution — assigning clear roles, mitigating before diagnosing, setting severity, and communicating in a structured cadence so a system under stress does not also become a communication failure. Use this whenever the user says production is down, an alert just fired, customers are affected, they need an incident commander, or they ask how to run or structure an active incident. For the after-the-fact writeup use `root-cause-analysis`, for the step-by-step fix procedures use `runbooks`, and for the on-call rotation that catches the page use `on-call-management`.
license: MIT
---

**Mitigate first, understand second, and let one person own the decisions.**

## 2. Mitigate before you diagnose

Rolling back a bad deploy, failing over to a healthy region, or shedding load buys time and
stops the bleeding, even if you don't yet know why the system broke. Root-causing while the
customer is still down is optimizing for the wrong thing. The fix does not need to be
permanent — it needs to be now.

- **Ask "what changed?" before "why did it break?"** — most incidents trace to a recent
  deploy, config change, or scaling event, and reverting it is faster than understanding it.
- **Prefer reversible mitigations** — a rollback or a traffic shift you can undo beats a
  targeted code fix you're improvising under pressure.
- **A mitigated incident is not a closed incident** — it moves to lower urgency, not to done.

**Done when:** customer-facing impact has stopped or measurably reduced, independent of
whether the cause is understood.
````

## Using a skill

There is no command to run. Both Claude Code and Antigravity preload only each skill's `name` and
`description`, then read the body of a `SKILL.md` when the description matches the task. Describe
the problem and the relevant skill loads.

### Claude Code

```text
> a pod keeps restarting, CrashLoopBackOff, and I can't tell why

  ⏺ Skill(kubernetes-operations)

  Reads the container's previous logs before the restart, then describe/events for the
  exit code — 137 points at the memory limit, 1 at the process itself...
```

To force a specific skill rather than letting the description decide, name it:

```text
> use the incident-response skill — checkout is down for about 30% of users
```

Skills also compose. A cost question that turns into a sizing question pulls in
[`rightsizing`](skills/finops/rightsizing/SKILL.md) from
[`cost-optimization`](skills/finops/cost-optimization/SKILL.md), because each skill names the
sibling to hand off to.

### Google Antigravity

Antigravity discovers skills from `.agents/skills/<skill>/` in the workspace and
`~/.gemini/config/skills/<skill>/` globally, and selects them the same way — by description. Open
this repository, or copy its `.agents/` folder into your own project root:

```text
> our terraform plan wants to replace the RDS instance and I don't know what changed

  [agent loads infrastructure-as-code]

  A replace in the plan is a destroy-then-create. Find the forces replacement line in the
  plan output first, then decide whether the attribute driving it can be changed in place...
```

Naming the skill explicitly works here too. Per the
[Antigravity skills documentation](https://antigravity.google/docs/skills): "You don't need to
explicitly tell the agent to use a skill — it decides based on context. However, you can mention a
skill by name if you want to ensure it's used."

The same file can also be used as an always-on **rule** under `.agents/rules/`, or wrapped as a
**workflow** invoked with `/workflow-name` — see
[docs/installation.md](docs/installation.md#antigravity-rules-and-workflows).

## Skills

<!-- categories:start -->
[![CI/CD](https://img.shields.io/badge/CI%2FCD-8-555)](#skills)
[![Containers](https://img.shields.io/badge/Containers-4-555)](#skills)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-9-555)](#skills)
[![Infrastructure as Code](https://img.shields.io/badge/Infrastructure%20as%20Code-6-555)](#skills)
[![Cloud](https://img.shields.io/badge/Cloud-6-555)](#skills)
[![GitOps](https://img.shields.io/badge/GitOps-3-555)](#skills)
[![Observability](https://img.shields.io/badge/Observability-7-555)](#skills)
[![Reliability & SRE](https://img.shields.io/badge/Reliability%20%26%20SRE-8-555)](#skills)
[![Security & DevSecOps](https://img.shields.io/badge/Security%20%26%20DevSecOps-8-555)](#skills)
[![Networking](https://img.shields.io/badge/Networking-6-555)](#skills)
[![Data & Storage](https://img.shields.io/badge/Data%20%26%20Storage-5-555)](#skills)
[![Platform Engineering](https://img.shields.io/badge/Platform%20Engineering-5-555)](#skills)
[![Automation](https://img.shields.io/badge/Automation-5-555)](#skills)
[![FinOps](https://img.shields.io/badge/FinOps-4-555)](#skills)
[![Performance](https://img.shields.io/badge/Performance-4-555)](#skills)
<!-- categories:end -->

| Category | Skills | Focus |
| --- | --- | --- |
| CI/CD | 8 | Getting a change from commit to production, fast and safe |
| Containers | 4 | Packaging applications into images that are small, reproducible, and safe |
| Kubernetes | 9 | Running workloads on Kubernetes without fighting the control loop |
| Infrastructure as Code | 6 | Changing infrastructure through version-controlled, reviewable configuration |
| Cloud | 6 | Designing and operating on cloud platforms deliberately |
| GitOps | 3 | Making Git the source of truth and letting a controller reconcile reality to it |
| Observability | 7 | Making running systems explain themselves |
| Reliability & SRE | 8 | Keeping systems up, and recovering fast when they are not |
| Security & DevSecOps | 8 | Building security into the pipeline and the platform, not bolting it on |
| Networking | 6 | Getting traffic to the right place, reliably and securely |
| Data & Storage | 5 | Running stateful systems and moving data without losing it |
| Platform Engineering | 5 | Building the paved roads that make the right way the easy way |
| Automation | 5 | Removing the repetitive, error-prone work humans should not be doing |
| FinOps | 4 | Spending cloud money deliberately, not accidentally |
| Performance | 4 | Making systems fast by measuring, not guessing |

<details>
<summary><strong>CI/CD</strong> (8) — Getting a change from commit to production, fast and safe</summary>

| Skill | What it does |
| --- | --- |
| [`ci-pipelines`](skills/ci-cd/ci-pipelines/SKILL.md) | Designs continuous integration pipelines that give a fast, honest merge signal — stage ordering, reproducibility, safe caching, and required checks that actually gate merges |
| [`continuous-delivery`](skills/ci-cd/continuous-delivery/SKILL.md) | Builds the deployment pipeline that takes an artifact from a merged commit to production automatically and safely — promotion gates between environments, deploy-on-merge, and keeping main always releasable |
| [`deployment-strategies`](skills/ci-cd/deployment-strategies/SKILL.md) | Chooses and implements the deployment technique — blue-green, canary, rolling, or shadow — that buys the most information before you're fully committed, plus the rollback plan that makes each one safe |
| [`release-management`](skills/ci-cd/release-management/SKILL.md) | Coordinates what ships and when — semantic versioning, changelogs, release trains vs continuous release, and cutting a multi-service release safely |
| [`build-optimization`](skills/ci-cd/build-optimization/SKILL.md) | Makes builds fast and reproducible through incremental and hermetic builds, remote or shared caching, dependency caching, and parallelism, without trading correctness for speed |
| [`artifact-management`](skills/ci-cd/artifact-management/SKILL.md) | Versions, stores, and promotes build outputs — registries, immutability, build-once-promote-many, retention and garbage collection, and provenance metadata |
| [`feature-flags`](skills/ci-cd/feature-flags/SKILL.md) | Decouples deploying code from releasing it to users through runtime feature flags — flag types, targeting rules, and the flag-debt cleanup discipline that keeps the flag system from becoming its own liability |
| [`pipeline-security`](skills/ci-cd/pipeline-security/SKILL.md) | Secures the CI/CD pipeline itself as an attack surface — least-privilege runners, protecting secrets, preventing poisoned-pipeline execution, pinning third-party actions by SHA, and preferring OIDC over long-lived keys |

</details>

<details>
<summary><strong>Containers</strong> (4) — Packaging applications into images that are small, reproducible, and safe</summary>

| Skill | What it does |
| --- | --- |
| [`containerization`](skills/containers/containerization/SKILL.md) | Packages an application into a container image that is small, reproducible, and safe to run — Dockerfiles, layer caching, multi-stage builds, non-root users, and runtime configuration |
| [`image-optimization`](skills/containers/image-optimization/SKILL.md) | Shrinks container image size and build time — base image choice, layer minimization, dependency pruning, .dockerignore, multi-arch builds, and measuring what actually ends up in the image |
| [`image-scanning`](skills/containers/image-scanning/SKILL.md) | Finds vulnerabilities, misconfiguration, and embedded secrets in container images before they ship — CVE scanning in the pipeline, gate-versus-warn policy, base image freshness, and separating fixable findings from noise |
| [`container-registry`](skills/containers/container-registry/SKILL.md) | Stores and distributes container images safely — tagging strategy, immutability, retention and garbage collection, access control, signing, and replication or pull-through caching |

</details>

<details>
<summary><strong>Kubernetes</strong> (9) — Running workloads on Kubernetes without fighting the control loop</summary>

| Skill | What it does |
| --- | --- |
| [`kubernetes-operations`](skills/kubernetes/kubernetes-operations/SKILL.md) | Covers running workloads through Kubernetes's control loop — requests/limits, liveness/readiness/startup probes, reading describe/events to debug CrashLoopBackOff, OOMKilled, Pending, or empty endpoints, safe rollouts and undo, and guardrails like PodDisruptionBudgets |
| [`kubernetes-networking`](skills/kubernetes/kubernetes-networking/SKILL.md) | Explains how traffic reaches and moves between pods — Services (ClusterIP/NodePort/LoadBalancer), Ingress and controllers, cluster DNS, NetworkPolicy default-deny, and debugging selector mismatches or empty endpoints |
| [`kubernetes-security`](skills/kubernetes/kubernetes-security/SKILL.md) | Hardens the cluster and its workloads — RBAC least-privilege, Pod Security Standards, admission control with OPA/Kyverno, securityContext, secrets at rest, image provenance, and disabling default service-account automount |
| [`helm-charts`](skills/kubernetes/helm-charts/SKILL.md) | Covers packaging and templating Kubernetes manifests with Helm — chart structure, values design and environment overrides, releases and revisions, upgrade/rollback semantics, avoiding template sprawl, and choosing Helm versus Kustomize |
| [`kubernetes-storage`](skills/kubernetes/kubernetes-storage/SKILL.md) | Covers persistent data in the cluster — PersistentVolumes/Claims, StorageClasses and dynamic provisioning, access modes, StatefulSets, volume lifecycle, and reclaim policy so data survives rescheduling |
| [`autoscaling`](skills/kubernetes/autoscaling/SKILL.md) | Covers scaling Kubernetes workloads and nodes to demand — HPA on the right metric, VPA, cluster autoscaler, custom/external metrics, avoiding thrash with stabilization windows, and requests as the foundation underneath it all |
| [`service-mesh`](skills/kubernetes/service-mesh/SKILL.md) | Covers when and how to adopt a service mesh — mTLS between services, traffic shifting, retries/timeouts enforced at the mesh layer, near-free observability, and the real latency and complexity cost of running one |
| [`operators-and-crds`](skills/kubernetes/operators-and-crds/SKILL.md) | Covers extending Kubernetes with CustomResourceDefinitions and controllers — the reconciliation pattern, a CRD as an API contract, why controllers must be level-triggered not edge-triggered, and when to build an operator versus buy one versus not bother |
| [`multi-tenancy`](skills/kubernetes/multi-tenancy/SKILL.md) | Covers safely sharing a Kubernetes cluster across teams or customers — namespace isolation, ResourceQuota and LimitRange, NetworkPolicy tenant boundaries, per-tenant RBAC, noisy-neighbor control, and soft versus hard multi-tenancy |

</details>

<details>
<summary><strong>Infrastructure as Code</strong> (6) — Changing infrastructure through version-controlled, reviewable configuration</summary>

| Skill | What it does |
| --- | --- |
| [`infrastructure-as-code`](skills/iac/infrastructure-as-code/SKILL.md) | Treats infrastructure changes as version-controlled, reviewable configuration instead of manual clicks or SSH sessions — Terraform state, plan review, environment parity, and guardrails against irreversible changes |
| [`terraform-modules`](skills/iac/terraform-modules/SKILL.md) | Covers designing Terraform modules that are reusable and composable rather than copy-pasted or over-engineered — clean input/output interfaces, version pinning, and knowing when abstraction earns its complexity |
| [`configuration-management`](skills/iac/configuration-management/SKILL.md) | Covers Ansible, Chef, and Puppet for managing mutable systems declaratively — idempotent tasks, convergence toward desired state instead of one-off scripts, inventory organization, and roles |
| [`policy-as-code`](skills/iac/policy-as-code/SKILL.md) | Covers enforcing infrastructure and cluster rules automatically, before a bad change ever reaches production — OPA, Sentinel, and Kyverno policies evaluated against the plan or admission request, and testing those policies like real code |
| [`environment-management`](skills/iac/environment-management/SKILL.md) | Covers keeping dev, staging, and prod as the same system at different sizes rather than forked copies that drift apart — parity via values not branches, ephemeral preview environments per pull request, and keeping non-prod cheap without making it useless as a signal |
| [`immutable-infrastructure`](skills/iac/immutable-infrastructure/SKILL.md) | Covers replacing servers wholesale instead of patching them in place — baking golden images, treating instances as disposable cattle rather than nursed pets, rebuilding to make any change, and the rollback simplicity that buys |

</details>

<details>
<summary><strong>Cloud</strong> (6) — Designing and operating on cloud platforms deliberately</summary>

| Skill | What it does |
| --- | --- |
| [`cloud-architecture`](skills/cloud/cloud-architecture/SKILL.md) | Designs systems for the cloud's actual shape — regions and availability zones, managed vs self-run tradeoffs, statelessness, failure-domain isolation, and the cost and lock-in consequences of each choice |
| [`serverless`](skills/cloud/serverless/SKILL.md) | Covers functions and managed compute where the platform enforces statelessness and bills per request — cold starts, event-driven design, concurrency limits, and when serverless does not fit |
| [`cloud-networking`](skills/cloud/cloud-networking/SKILL.md) | Covers the virtual network layer of a cloud deployment — VPCs, subnets, route tables, peering and transit, private endpoints, egress control, and hybrid or on-prem connectivity |
| [`cloud-migration`](skills/cloud/cloud-migration/SKILL.md) | Guides moving workloads to or between clouds using the 6 Rs, a phased cutover with a real rollback path, data sync, and avoiding a lift-and-shift that just relocates old problems |
| [`multi-cloud`](skills/cloud/multi-cloud/SKILL.md) | Covers running across cloud providers on purpose — portability vs managed services, the real operational cost of a second provider, avoiding accidental multi-cloud, and where the abstraction is worth it |
| [`well-architected-review`](skills/cloud/well-architected-review/SKILL.md) | Runs a structured audit against the standard pillars — reliability, security, cost, performance, operational excellence, sustainability — producing prioritized, actionable findings, not a checklist tick |

</details>

<details>
<summary><strong>GitOps</strong> (3) — Making Git the source of truth and letting a controller reconcile reality to it</summary>

| Skill | What it does |
| --- | --- |
| [`gitops`](skills/gitops/gitops/SKILL.md) | Establishes Git as the single source of truth for deployed state, with a pull-based controller reconciling the cluster to match a repo instead of humans or pipelines pushing changes via kubectl or helm |
| [`argocd-operations`](skills/gitops/argocd-operations/SKILL.md) | Covers running Argo CD day to day — structuring app-of-apps, choosing sync policies and waves, reading health versus sync status correctly, and unsticking a degraded or hung Application |
| [`progressive-delivery`](skills/gitops/progressive-delivery/SKILL.md) | Automates canary and blue-green rollouts so promotion and rollback are driven by live metrics, not a timer or a human watching a dashboard, using controllers like Argo Rollouts or Flagger |

</details>

<details>
<summary><strong>Observability</strong> (7) — Making running systems explain themselves</summary>

| Skill | What it does |
| --- | --- |
| [`observability`](skills/observability/observability/SKILL.md) | Frames the mental model for making a running system explain itself — metrics, logs, and traces as complementary signals, RED and USE checklists, SLOs and error budgets, cardinality as the tax paid for detail |
| [`metrics-and-monitoring`](skills/observability/metrics-and-monitoring/SKILL.md) | Covers instrumenting and collecting numeric time-series data — the Prometheus data model, choosing between counters, gauges, and histograms, controlling cardinality before it controls your bill, applying RED and USE systematically, and writing recording rules |
| [`log-management`](skills/observability/log-management/SKILL.md) | Covers structured logging at scale — emitting JSON not prose, choosing sensible levels, sampling high-volume paths, setting retention against real cost, correlating log lines with trace IDs, and keeping secrets out of logs entirely |
| [`distributed-tracing`](skills/observability/distributed-tracing/SKILL.md) | Covers following a single request across service boundaries — context propagation, span and attribute design, sampling that keeps the traces worth keeping, and using traces to find where latency actually accumulates |
| [`alerting`](skills/observability/alerting/SKILL.md) | Covers designing alerts that page a human only when a human needs to act — symptom-based alerting over cause-based, multi-window burn-rate alerts on error budgets, severity tiers that route between page/ticket/dashboard, requiring every page to link a runbook, and tuning out alert fatigue |
| [`dashboards`](skills/observability/dashboards/SKILL.md) | Covers building dashboards people actually open during an incident instead of ignoring — one question per panel, RED/USE-based layout, designing for a specific audience and decision, and avoiding the wall-of-graphs nobody reads |
| [`slo-definition`](skills/observability/slo-definition/SKILL.md) | Covers turning "the service should be reliable" into a falsifiable number — SLIs that reflect real user experience, SLO targets meaningfully below 100%, the error budget those targets imply, and the policy that gates release velocity when it's spent |

</details>

<details>
<summary><strong>Reliability & SRE</strong> (8) — Keeping systems up, and recovering fast when they are not</summary>

| Skill | What it does |
| --- | --- |
| [`incident-response`](skills/reliability/incident-response/SKILL.md) | Runs a live incident from first alert to resolution — assigning clear roles, mitigating before diagnosing, setting severity, and communicating in a structured cadence so a system under stress does not also become a communication failure |
| [`runbooks`](skills/reliability/runbooks/SKILL.md) | Writes and maintains the procedural documents that let a tired, half-awake engineer resolve a known failure at 3am without needing the original author or deep system knowledge |
| [`disaster-recovery`](skills/reliability/disaster-recovery/SKILL.md) | Prepares a system to survive a total, catastrophic failure — a lost region, a corrupted database, a deleted cloud account — through defined RTO/RPO targets, backups that have actually been restored, and tested failover, not a backup cron job someone set up once |
| [`chaos-engineering`](skills/reliability/chaos-engineering/SKILL.md) | Deliberately injects controlled failure into a system to find weaknesses before they find you in production, using a stated hypothesis, a bounded blast radius, and a defined steady-state metric to verify against |
| [`capacity-planning`](skills/reliability/capacity-planning/SKILL.md) | Ensures a system has enough headroom before it needs it, by forecasting growth, modeling load against real saturation signals, and accounting for the lead time it takes to actually add capacity |
| [`root-cause-analysis`](skills/reliability/root-cause-analysis/SKILL.md) | Turns an incident into a blameless postmortem that actually changes something — a factual timeline, multiple contributing factors instead of one scapegoat cause, and action items with real owners and dates that get tracked to completion |
| [`on-call-management`](skills/reliability/on-call-management/SKILL.md) | Designs a sustainable on-call system — fair rotations, clear escalation paths, clean handoffs, and a humane alert load — and treats on-call health itself as a reliability metric rather than an unmeasured cost absorbed by whoever holds the pager |
| [`error-budgets`](skills/reliability/error-budgets/SKILL.md) | Turns an SLO into a spendable number that makes the velocity-versus-reliability tradeoff explicit — deriving the budget from the SLO, tracking how fast it's consumed, and enforcing freeze policies when it runs out, instead of arguing about "is it reliable enough" from gut feeling |

</details>

<details>
<summary><strong>Security & DevSecOps</strong> (8) — Building security into the pipeline and the platform, not bolting it on</summary>

| Skill | What it does |
| --- | --- |
| [`secrets-management`](skills/security/secrets-management/SKILL.md) | Keeps credentials, API keys, and certificates out of code, images, and logs, and moves them into a real secret store with tight, scoped runtime injection |
| [`vulnerability-management`](skills/security/vulnerability-management/SKILL.md) | Finds, prioritizes, and closes out vulnerabilities across code, dependencies, images, and infrastructure without drowning the team in unactionable findings |
| [`supply-chain-security`](skills/security/supply-chain-security/SKILL.md) | Establishes trust in what you build and ship — SBOMs, build provenance, dependency pinning and verification, artifact signing, and signature verification before deploy |
| [`compliance-as-code`](skills/security/compliance-as-code/SKILL.md) | Turns compliance controls into executable, version-controlled checks with automated evidence collection, so audits become a query instead of a fire drill |
| [`iam-access-management`](skills/security/iam-access-management/SKILL.md) | Grants least-privilege access to systems and cloud resources through roles rather than individual permissions, short-lived credentials, and regular review, so standing access doesn't accumulate unnoticed |
| [`security-scanning`](skills/security/security-scanning/SKILL.md) | Places SAST, DAST, and dependency scanning at the right stage of the pipeline, tuned to gate or merely inform depending on confidence, without turning every merge into a wall of unreviewed findings |
| [`network-security`](skills/security/network-security/SKILL.md) | Protects traffic and boundaries through segmentation, default-deny rules, egress control, and TLS everywhere, minimizing what's actually reachable on the network |
| [`zero-trust`](skills/security/zero-trust/SKILL.md) | Replaces network location with verified identity as the basis for access, removing implicit trust inside the perimeter via microsegmentation and continuous verification |

</details>

<details>
<summary><strong>Networking</strong> (6) — Getting traffic to the right place, reliably and securely</summary>

| Skill | What it does |
| --- | --- |
| [`dns-management`](skills/networking/dns-management/SKILL.md) | Covers DNS as production infrastructure that can take down everything downstream — record types, TTL tradeoffs, propagation and caching, health-checked failover, and split-horizon setups for internal versus external views |
| [`load-balancing`](skills/networking/load-balancing/SKILL.md) | Covers distributing traffic across healthy backends — L4 versus L7 balancing, algorithms, health checks that detect real failure, connection draining during deploys, and the real latency and capacity cost of sticky sessions |
| [`api-gateway`](skills/networking/api-gateway/SKILL.md) | Covers the managed front-door pattern for APIs — request routing, centralized auth, rate limiting and quotas, request/response shaping, and recognizing when a gateway helps versus becomes a bottleneck or single point of failure |
| [`cdn`](skills/networking/cdn/SKILL.md) | Covers caching and serving content at the edge — cache keys and TTL design, invalidation strategies, origin shielding, deciding what is safely cacheable, and moving static and dynamic content closer to users |
| [`service-connectivity`](skills/networking/service-connectivity/SKILL.md) | Covers making service-to-service connections reliable and secure — service discovery, mutual TLS, timeouts and retries with circuit breakers, backpressure under load, and secure links across hybrid or multi-cloud boundaries |
| [`network-troubleshooting`](skills/networking/network-troubleshooting/SKILL.md) | Covers diagnosing connectivity failures methodically, layer by layer, with the right tool per symptom — dig/nslookup for DNS, curl/openssl for TLS and HTTP, traceroute/mtr for routing, tcpdump for packet capture, and ss/netstat for local socket state |

</details>

<details>
<summary><strong>Data & Storage</strong> (5) — Running stateful systems and moving data without losing it</summary>

| Skill | What it does |
| --- | --- |
| [`database-operations`](skills/data/database-operations/SKILL.md) | Covers the operational discipline of running databases in production — connection pooling and exhaustion, online schema changes, replication topology and read scaling, failover and promotion, and the runbook habits that keep an outage from becoming data loss |
| [`backup-and-restore`](skills/data/backup-and-restore/SKILL.md) | Defines the discipline of building backups you can actually restore under pressure — RPO-driven frequency, restores rehearsed on a schedule, offsite immutable copies, encryption, and treating a backup that has never been restored as equivalent to no backup at all |
| [`data-migration`](skills/data/data-migration/SKILL.md) | Covers changing schema or data shape without downtime using expand-then-contract — adding new structures alongside old, backfilling historical data in batches, dual-writing during the transition, verifying both old and new code paths, and keeping every step independently reversible |
| [`caching-strategies`](skills/data/caching-strategies/SKILL.md) | Covers caching correctly — deciding what is worth caching, choosing between cache-aside, write-through, and write-behind, setting TTLs from real staleness tolerance, invalidating on write instead of hoping a TTL catches it, and preventing thundering-herd stampedes on expiry |
| [`stateful-workloads`](skills/data/stateful-workloads/SKILL.md) | Covers running stateful systems — databases, queues, search indexes — on Kubernetes, including StatefulSets and stable identity, durable storage, backup and failover built into the platform rather than bolted on, and the tradeoff between self-managing a stateful service and paying for a managed one |

</details>

<details>
<summary><strong>Platform Engineering</strong> (5) — Building the paved roads that make the right way the easy way</summary>

| Skill | What it does |
| --- | --- |
| [`internal-developer-platform`](skills/platform-engineering/internal-developer-platform/SKILL.md) | Designs an internal developer platform (IDP) as a product for one customer — engineers — with paved roads, self-service workflows, and abstractions that speed people up without hiding the levers they need during an incident |
| [`developer-experience`](skills/platform-engineering/developer-experience/SKILL.md) | Cuts the friction between having an idea and seeing it running — fast local feedback loops, painless environment setup, and DORA-plus metrics that reveal where time actually goes |
| [`service-catalog`](skills/platform-engineering/service-catalog/SKILL.md) | Builds and maintains a catalog of every service, its owner, and its scaffolding template so "who owns this" and "how do I start a new one" always have one authoritative answer |
| [`self-service-infrastructure`](skills/platform-engineering/self-service-infrastructure/SKILL.md) | Lets developers provision databases, queues, and environments themselves through guardrailed templates instead of filing a ticket and waiting on a platform team |
| [`golden-paths`](skills/platform-engineering/golden-paths/SKILL.md) | Curates the one opinionated, secure-and-observable-by-default way to build a service so the easy option and the right option are the same option |

</details>

<details>
<summary><strong>Automation</strong> (5) — Removing the repetitive, error-prone work humans should not be doing</summary>

| Skill | What it does |
| --- | --- |
| [`workflow-automation`](skills/automation/workflow-automation/SKILL.md) | Covers automating multi-step operational workflows — event-driven triggers, orchestrating steps across systems, making every step idempotent and safely retryable, and keeping a human in the loop where judgment or blast radius demands it |
| [`scripting-automation`](skills/automation/scripting-automation/SKILL.md) | Covers writing operational scripts that survive contact with production — idempotency, real error handling and exit codes, structured logging, a dry-run mode, and recognizing when a script has outgrown scripting |
| [`toil-reduction`](skills/automation/toil-reduction/SKILL.md) | Covers finding and eliminating operational toil — measuring it honestly instead of by gut feel, automating the manual and repetitive, protecting a real automation budget against feature pressure, and telling toil apart from valuable work that just looks repetitive |
| [`scheduled-jobs`](skills/automation/scheduled-jobs/SKILL.md) | Covers cron and scheduled work done right — idempotency, preventing overlapping runs, monitoring for missed and failed runs, alerting on silence, and getting time zones and DST transitions correct |
| [`infrastructure-testing`](skills/automation/infrastructure-testing/SKILL.md) | Covers testing infrastructure and config before it ships — validate-and-plan checks, policy enforcement, unit and integration tests for IaC modules, ephemeral test environments, and a testing pyramid sized for infrastructure |

</details>

<details>
<summary><strong>FinOps</strong> (4) — Spending cloud money deliberately, not accidentally</summary>

| Skill | What it does |
| --- | --- |
| [`cost-optimization`](skills/finops/cost-optimization/SKILL.md) | Cuts cloud spend without cutting reliability by finding the few levers that move most of the bill — idle and orphaned resources, over-committed on-demand spend that qualifies for reserved or savings-plan discounts, and oversized fleets — and going after them in dollar order |
| [`resource-tagging`](skills/finops/resource-tagging/SKILL.md) | Builds a tag taxonomy for cost, ownership, and automation, enforces it at provision time so it never depends on discipline after the fact, and uses it to drive cost allocation, showback, and the hunt for untagged waste |
| [`rightsizing`](skills/finops/rightsizing/SKILL.md) | Matches compute, memory, and storage allocation to real measured usage instead of the guess made at launch time, sizing from percentiles rather than averages, and preferring autoscaling over a fixed size wherever demand varies |
| [`cloud-budgeting`](skills/finops/cloud-budgeting/SKILL.md) | Forecasts cloud spend from trend and known upcoming changes, sets budgets and alerts that fire before an overrun becomes a surprise invoice, catches anomalies early, and turns raw spend into unit economics and showback/chargeback that leadership can act on |

</details>

<details>
<summary><strong>Performance</strong> (4) — Making systems fast by measuring, not guessing</summary>

| Skill | What it does |
| --- | --- |
| [`performance-tuning`](skills/performance/performance-tuning/SKILL.md) | Guides systematic performance work — measuring before changing, finding the actual bottleneck with the USE method (Utilization, Saturation, Errors), optimizing the real hot path, and verifying the fix moved the number that matters |
| [`load-testing`](skills/performance/load-testing/SKILL.md) | Tests a system under realistic traffic shapes to find its breaking point before users do — modeling real request mixes and ramp patterns, measuring latency percentiles and error rate together, and exercising the whole system instead of one endpoint in isolation |
| [`profiling`](skills/performance/profiling/SKILL.md) | Finds where time, memory, and IO actually go inside a running system, using CPU and memory profilers, flame graphs, and the right choice between sampling and instrumentation, so optimization targets the real hot path instead of intuition |
| [`scalability-design`](skills/performance/scalability-design/SKILL.md) | Designs systems to handle the next order of magnitude of load by removing state, shared contention, and single bottlenecks, and by choosing deliberately between horizontal and vertical scaling for each component |

</details>

## Documentation

| Document | Contents |
| --- | --- |
| [docs/installation.md](docs/installation.md) | Installing in Claude Code, Antigravity, or by hand |
| [docs/authoring-skills.md](docs/authoring-skills.md) | The skill format, frontmatter rules, and constraints |
| [docs/evals.md](docs/evals.md) | The eval file schema and the three-case convention |
| [docs/architecture.md](docs/architecture.md) | Repository layout, the two skill trees, and the scripts |
| [docs/faq.md](docs/faq.md) | Common questions about scope, triggering, and limits |
| [CONTEXT.md](CONTEXT.md) | Why the collection is shaped the way it is |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Adding or changing a skill |
| [AGENTS.md](AGENTS.md) | Conventions for agents working in this repository |

## Repository layout

```
skills/<category>/<skill>/SKILL.md   # canonical tree, and what the plugin manifest points at
skills/<category>/<skill>/references/  # optional depth, linked one level deep from SKILL.md
.agents/skills/<skill>/              # flat mirror for Antigravity — generated, do not edit
evals/<skill>.json                   # 3 behavioral cases per skill
scripts/check-skills.py              # validator
scripts/build-antigravity.py         # regenerates the flat mirror
```

Fifteen skills carry a `references/` deep-dive with concrete material: a GitHub Actions cookbook,
a Terraform plan and state reference, a kubectl debugging playbook, PromQL patterns, an incident
roles and severity guide, a secret-rotation playbook, and an expand-then-contract SQL walkthrough.

`python3 scripts/check-skills.py` validates frontmatter against the Agent Skills spec, name and
folder agreement, description triggers, body length, `Report` and `Done when:` sections, code
fences, reference links and their Contents lists, the eval files, this README's catalogue, the
plugin manifest, and that the generated Antigravity tree is in sync. CI runs it on every pull
request.

## Design principles

- **One responsibility per skill.** If two skills would say the same thing, one cross-references
  the other instead of repeating it.
- **Opinionated.** Skills take positions and explain the reasoning, because a rule without a reason
  is not memorable.
- **Checkable.** Every step ends in a concrete `Done when:` line.
- **Honest.** Every skill closes by naming what it does not cover, rather than implying the job is
  finished.

## Contributing

New skills should be single-responsibility, take a position and explain it, and end with a Report.
Match the format of an existing skill and cross-reference siblings rather than duplicating them.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the full process. The validator must pass.

## License

MIT — see [LICENSE](LICENSE).

The skill format follows [agent-skills](https://github.com/arjunprabhulal/agent-skills).
