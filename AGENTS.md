# AGENTS.md

Guidance for AI agents (and humans) working in this repository: the required shape of a skill, the
workflow for changing one, and the reasoning behind both. `README.md` describes what the collection
contains and how to install it.

## What this repo is

A collection of **88 DevOps Agent Skills** across 15 categories. Each skill is a single
`SKILL.md` under `skills/<category>/<skill-name>/`, loaded on demand when a matching task appears.

## The shape of every skill

1. **Frontmatter** — exactly three keys: `name` (must equal the folder name), `description`
   (one paragraph with concrete "Use this whenever…" triggers and "For X use `sibling`"
   cross-references), and `license: MIT`.
2. **Intro** — one or two paragraphs framing the core principle, ending in a single **bold
   principle line**.
3. **5–6 numbered `## N. Imperative heading` sections** — each explains the *why*, may carry at
   most one or two code blocks or tables total, and ends with a concrete **`Done when:`** line.
4. **`## Report`** — closes by stating the key decisions and, explicitly, the honest remaining gap.

## Rules

- **One responsibility per skill.** Cross-reference siblings by name instead of repeating them.
- **Be opinionated and explain why.** A rule without a reason is not memorable.
- **Principles over vendors.** Name tools to illustrate; never tie a skill to one product.
- **No placeholders.** Every skill must be complete and technically correct.

## Before committing

Run the validator:

```bash
python3 scripts/check-skills.py
```

It checks frontmatter, name/folder match, description length and triggers, the presence of a
Report section and Done-when checkpoints, balanced code fences, eval files, reference links, that
`.claude-plugin/plugin.json` matches the skills on disk, and that the Antigravity `.agents/skills/`
layout is in sync. When you add a skill, add its path to `plugin.json` and to the README catalogue.

## Two layouts, one source

The canonical skills live under `skills/<category>/<skill>/` (the Claude Code plugin layout).
Google Antigravity discovers skills from a flat `.agents/skills/<skill>/` layout, which is
**generated** from the canonical tree and **not committed** — `.agents/` is gitignored. After
adding or editing any skill, regenerate it locally:

```bash
python3 scripts/build-antigravity.py
```

Never edit skills under `.agents/skills/` directly — your changes will be overwritten on the next
build. Edit the canonical copy and rebuild.

---

# Design rationale

Why the repository is shaped this way, so that changes extend the design instead of eroding it.

## Skills instead of one large prompt

The alternative to 88 files is one long document, or an always-on rules file, describing all of
DevOps at once. Both fail for the same reason: everything is loaded for every task. A question
about HPA stabilization windows drags in Terraform state, incident severity tiers, and CDN cache
keys, and the relevant paragraph competes with 80 irrelevant ones that pull answers off target.

A skill is loaded on demand. The `description` frontmatter is the trigger — it states when to
reach for the skill and which sibling to use instead — so the selection decision happens before
any content is read. `scripts/check-skills.py` enforces a "Use this…" phrase in every description
and caps it at 620 characters, because a vague trigger causes both misfires and misses. The split
also makes the collection editable: a skill is a unit one person can hold in their head, rewrite,
and validate in isolation. A single large prompt is not.

## One responsibility per skill, and cross-references instead of copies

Skills overlap in subject matter constantly: `autoscaling` touches resource requests, so does
`kubernetes-operations`, so does `cost-optimization`. The rule is that exactly one skill owns each
topic and the others name it — `observability` points at `metrics-and-monitoring`,
`log-management`, and `distributed-tracing` rather than restating them. Two copies of the same
guidance drift, and the agent then gets contradictory instructions with no way to tell which is
current. A cross-reference by skill name has no version to fall out of date; it resolves to
whatever the owning skill says now. The cost is that a skill read in isolation is deliberately
incomplete, and assumes the reader can follow a name to the neighboring skill.

## Why every step ends in a "Done when:" line

Guidance that cannot be checked is guidance that can be claimed. Without a checkpoint, an agent or
a person can read a section on probes, add a liveness probe that duplicates the readiness probe,
and report the step complete. The `Done when:` line names the observable state that has to hold —
not the action taken, but the condition that proves the action worked. Each is written to be
falsifiable against a real system, which is why they name things that can be looked up: what a
query returns, what a rollout does, what happens when a dependency is killed. The validator
requires at least one `**Done when:**` per skill; the convention is one per numbered section.

## Why every skill ends in a Report that names a gap

The `## Report` section closes each skill by stating the decisions made and, explicitly, what is
still missing. This counteracts a specific failure: work that ends with a summary implying
completion. Alerting is never finished. Observability coverage is never total. A skill that ends
without naming a gap teaches the agent to hand back a false all-clear. Naming the gap also makes
the handoff useful — "traces cover the API tier but not the async workers" is something the next
person can act on, and "observability is configured" is not.

## Principles over vendors, and what that costs

Skills describe how a class of system behaves and why one approach beats another. Tools appear as
illustration — Prometheus for the metric data model, Argo CD for reconciliation, OPA and Kyverno
for admission policy — never as the subject. The reason is durability: vendor syntax, flag names,
and console workflows change on a schedule nobody in this repo controls, while the reasons behind a
default-deny NetworkPolicy or a build-once-promote-many artifact flow do not.

The price should be stated plainly. A skill will not produce a finished vendor configuration.
Asking for "the Terraform for a production VPC" gets the decisions a VPC design has to make and the
failure modes of each, not a module that can be applied unread. The collection is optimized for
making a correct decision, not for saving keystrokes on a config file.

Fifteen skills carry a `references/` folder as the release valve — concrete material in one
concrete syntax, such as `skills/ci-cd/ci-pipelines/references/github-actions.md`. References sit
outside the skill body so the body stays vendor-neutral and the vendor-specific part is read only
when needed, which also keeps each `SKILL.md` under the validator's 500-line body limit.

## Why one of the two layouts is generated

The nested tree is canonical because categories are how the collection is browsed, reviewed, and
kept balanced — 15 groups of 3 to 9 skills. The flat tree carries no information the nested one
lacks, so hand-maintaining both would mean two copies of 88 files with nothing to keep them honest.

`scripts/build-antigravity.py` deletes and regenerates `.agents/skills/` from the canonical tree,
copying each skill folder whole, including `references/`. It rebuilds rather than syncs so
deletions propagate, and it fails if two skills in different categories share a name, since the
flatten would collide. `scripts/check-skills.py` then compares each mirrored `SKILL.md` byte for
byte against its canonical copy and flags stale directories.

## Why evals live in the repo

Every skill has `evals/<skill>.json` with three cases: a "do the task" prompt, a "diagnose and fix"
prompt, and a "push back on an anti-pattern" prompt, each recording the behavior a well-guided
agent should show. They are committed alongside the skills, not kept in a separate test project,
because they are part of the specification. The third case in particular encodes the opinion:
`evals/alerting.json` expects the agent to refuse "page whenever any pod restarts or disk hits 80%"
and explain that those are causes rather than symptoms. Prose can state a position; only an eval
states what disagreement looks like in practice.

Adjacency means a skill rewrite and its expectations move in one commit. `scripts/check-skills.py`
requires the file to exist, to name its skill, and to hold exactly three well-formed cases, so a
new skill cannot land without stating what it is supposed to do. The same validator holds each
README catalogue row to the skill's current description, since the description is the trigger and a
catalogue that drifts from it describes a collection that no longer exists.

## Deliberate limits

The collection encodes judgment, not state. No skill knows what is running, what the last deploy
changed, or which alert fired last night. Skills describe how to find that out and what to conclude
from it; the finding out happens against the live system, with the tools the reader already has.

It is also not a replacement for local runbooks. A skill can say that every page needs a documented
response; it cannot know that a specific database failover requires a specific manual step first.
Organization-specific procedure belongs in organization-specific documents, and the skills are
written to be read alongside them rather than instead of them.

The collection is opinionated by design. Where a real tradeoff exists, a skill takes a position and
explains it, which makes disagreement legible — the intended outcome, provided the disagreement
carries a stated reason rather than an unexamined default.
