# AGENTS.md

Guidance for AI agents (and humans) working in this repository.

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
layout is in sync. When you add a skill, add its path to `plugin.json`.

## Two layouts, one source

The canonical skills live under `skills/<category>/<skill>/` (the Claude Code plugin layout).
Google Antigravity discovers skills from a flat `.agents/skills/<skill>/` layout, which is
**generated** from the canonical tree. After adding or editing any skill, regenerate it:

```bash
python3 scripts/build-antigravity.py
```

Never edit skills under `.agents/skills/` directly — your changes will be overwritten on the next
build. Edit the canonical copy and rebuild.
