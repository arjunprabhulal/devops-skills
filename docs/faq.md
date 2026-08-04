# FAQ

Answers about what this repository contains, how the skills load, and where the limits are.

## What is an Agent Skill, and how is it different from a prompt, a rule, or a slash command?

A skill is a folder with a `SKILL.md` file: YAML frontmatter (`name`, `description`, `license`)
followed by Markdown instructions. The agent loads it on its own when a task matches the
description. A prompt is text typed once for one turn. A rule is always-on context that applies to
every turn whether or not it is relevant. A slash command is invoked explicitly by the user. A
skill sits between them: written once, stored on disk, and pulled in only for the tasks it names.

## Do I need all 88 skills installed, or can I take one?

One is fine. Each skill is self-contained — a single `SKILL.md`, plus a `references/` folder for
15 of them. Copy the folder:

```bash
cp -r skills/kubernetes/kubernetes-operations ~/.claude/skills/
```

Skills cross-reference siblings by name in their descriptions (for example, `alerting` points at
`slo-definition`). If the sibling is not installed, the reference is inert text — nothing breaks,
the agent just does not have the other guide.

## When does a skill actually load?

Only the frontmatter is preloaded. The agent holds each installed skill's `name` and `description`
in context, then reads the body of a `SKILL.md` when it decides that skill applies. The size
difference is large: across all 88 skills, the descriptions total roughly 49,000 characters while
the bodies total roughly 504,000. Installing all 88 costs about the metadata; it does not put 88
guides in the context window.

## How does the agent decide which skill to use?

The `description` frontmatter is the trigger, and it is the only thing the agent sees before
deciding. Every description in this repo states what the skill covers, a set of concrete "Use this
whenever…" conditions, and cross-references naming which sibling to use instead for adjacent work.
`scripts/check-skills.py` enforces a trigger phrase and a 620-character ceiling on each one.
Selection is a model judgment, not a lookup — a vague description gets a skill ignored or
misfired.

## Do these work outside Claude Code?

Google Antigravity today. It reads the same `SKILL.md` format from a flat
`.agents/skills/<skill>/` layout, built with `scripts/build-antigravity.py`; copy a folder into
`~/.gemini/config/skills/` for a global install. Beyond those two, the format is plain Markdown
plus a YAML header with no tool-specific syntax, so any harness that can read a file and pass it
to a model can use these. Nothing here has been tested against harnesses other than Claude Code
and Antigravity.

## Are these tied to AWS, GCP, or Azure?

No. The rule in `AGENTS.md` is principles over vendors: tools and providers are named to
illustrate a point, never to anchor a skill to one product. The cost is real. There are no console
click-paths, no provider-specific IAM policy documents, and no copy-paste resource identifiers. A
skill explains what a private endpoint is for and when to use one; translating that into a
specific provider's API is left to the reader or the agent.

## Can a skill run commands or change my infrastructure?

No. A `SKILL.md` is text the agent reads. It has no execution privileges of its own and no hooks.
What actually runs is decided entirely by the agent's tools and the permissions granted to them.
Skills do contain shell and YAML examples, and an agent with command-execution approval may
propose running them — review those the same way any other agent-proposed command should be
reviewed.

## Why is there no eval runner?

The eval files describe expected behavior in prose ("pushes back that these are causes, not
symptoms…"), which is graded by a human reading the transcript or by a judge model, not by string
comparison. Writing a scoring harness would mean picking a model, a judge prompt, and a threshold,
and shipping those as if they were part of the skills. `scripts/check-skills.py` validates that
every eval file exists and is well-formed; it does not run anything. Nothing in this repo
automatically measures whether a model followed a skill.

## Why is there a second, generated copy of every skill?

Two harnesses expect two different directory layouts. `skills/<category>/<skill>/` is the
canonical tree and the one the Claude Code plugin lists in `.claude-plugin/plugin.json`.
`.agents/skills/<skill>/` is a flat mirror that Google Antigravity discovers, produced by
`scripts/build-antigravity.py`. Skill names are globally unique, so flattening is lossless.

Only the canonical tree is committed. `.agents/` is gitignored and built on demand, because skill
registries scan `.agents/skills/` too and would otherwise index this repository's 88 skills twice.
Edit the canonical copy only — the build script deletes and regenerates the mirror — then re-run
it. `check-skills.py` compares the two trees whenever the mirror is present.

## How do I know a skill is any good, and how were these validated?

Structure is checked mechanically: `python3 scripts/check-skills.py` verifies frontmatter, that
each `name` matches its folder, description length and trigger, the presence of a `## Report`
section and `Done when:` checkpoints, balanced code fences, that reference links resolve, that
each skill has a three-case eval file, that the Antigravity mirror is in sync, and that
`plugin.json` matches disk. GitHub Actions runs it on every push and pull request
(`.github/workflows/ci.yml`). Content is another matter: each skill has three eval cases stating
the behavior it should produce, but those are read and judged by hand. There are no benchmark
scores or A/B results here. The honest check is to read the `SKILL.md` for a topic you already
know well and see whether it matches your experience.

## Can I use these commercially?

Yes. MIT, copyright 2026 Arjun Prabhulal — see `LICENSE`. Copy, modify, embed in a product, or
ship an edited fork. The only obligation is keeping the copyright and licence notice. Each skill
also carries `license: MIT` in its own frontmatter, so a single copied folder stays licensed on
its own.

## How do I request or contribute a skill?

Open an issue or a pull request at <https://github.com/arjunprabhulal/devops-skills>. New skills
must match the existing shape — one responsibility, a trigger-bearing description, numbered
sections with `Done when:` lines, a closing `## Report`, an `evals/<skill>.json` file, an entry in
`plugin.json`, and a `scripts/build-antigravity.py` run. See [CONTRIBUTING.md](../CONTRIBUTING.md)
for the full procedure and [AGENTS.md](../AGENTS.md) for the format rules.
