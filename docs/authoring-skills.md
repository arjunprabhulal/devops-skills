# Authoring skills

The format specification for a skill in this repository: the files a skill consists of, the
frontmatter contract, the body structure, and what `scripts/check-skills.py` enforces.
Repository-wide conventions are in `AGENTS.md`; this document is the detail behind them.

## 1. File layout

A skill is a directory under `skills/<category>/<skill-name>/`, where the category is one of the
15 existing directories in `skills/` and the skill name is the directory name.

```
skills/<category>/<skill-name>/
    SKILL.md                     required — frontmatter plus the guide
    references/<topic>.md        optional — depth moved out of SKILL.md
evals/<skill-name>.json          required — 3 cases, checked by the validator
```

Three more files must know about a new skill:

- `.claude-plugin/plugin.json` — add `./skills/<category>/<skill-name>` to the `skills` array.
- `README.md` — add a catalogue row under the skill's category. The validator holds the row text
  to the skill's `description` up to its `Use this` trigger.
- `.agents/skills/<skill-name>/` — generated. Run `python3 scripts/build-antigravity.py` after
  any edit. Never edit files under `.agents/skills/` directly; the next build overwrites them.

The eval file holds `skill_name` (equal to the directory name) and an `evals` list of exactly
three objects, each with `id`, `prompt`, `expected_output`, and `files`. `prompt` is how a user
would phrase the request; `expected_output` states what a correct answer must contain.

## 2. Frontmatter

YAML frontmatter opens the file and carries exactly three keys, in this order:

```yaml
---
name: containerization
description: Packages an application into a container image … Use this whenever … For X use `y`.
license: MIT
---
```

`name` constraints:

- 64 characters maximum.
- Lowercase letters, numbers, and hyphens only. No spaces, underscores, or capitals.
- Must equal the containing folder name exactly.
- Must not contain the reserved words `anthropic` or `claude`.

`description` constraints:

- Non-empty, 1024 characters maximum. `check-skills.py` applies a tighter limit of 620
  characters; the longest description on disk is 615.
- Written in the third person, describing the skill, not addressing the reader.
- Plain text on one line. No XML tags.
- States both what the skill does and when to use it.

`license` is the literal string `MIT` on every skill.

## 3. Writing a description that triggers correctly

The description is the only text an agent sees before deciding whether to load the skill. Three
parts, in order.

1. **What the skill does** — one sentence in the third person, naming the concrete subject matter.
   "Packages an application into a container image" is retrievable; "helps with containers" is not.
2. **When to use it** — a `Use this whenever the user …` clause listing concrete situations in
   the words a user would use, not the vocabulary of the skill: symptoms, tool names, file names,
   and questions.
3. **Cross-references** — a closing `For X use <sibling-skill>` clause, sibling name in backticks,
   pointing at the skills that own the neighbouring problem. Overlapping skills then stop
   competing.

A real example, from `skills/containers/containerization/SKILL.md`:

> Packages an application into a container image that is small, reproducible, and safe to run —
> Dockerfiles, layer caching, multi-stage builds, non-root users, and runtime configuration. Use
> this whenever the user is writing a Dockerfile, mentions Docker or OCI images, image size or
> build times, or is preparing an application to run on Kubernetes. For orchestrating those images
> use `kubernetes-operations`; for scanning them use `image-scanning`.

The triggers there are specific: writing a Dockerfile, the words Docker and OCI, image size,
build times, preparing for Kubernetes. The cross-references hand orchestration and scanning off
to the two skills that own them.

## 4. Body structure

The body is a short opinionated guide, not a manual. It follows a fixed shape:

- **Intro** — one or two paragraphs framing the core idea, ending in a single **bold principle
  line** that states the skill's one rule.
- **A reference pointer** when the skill has a `references/` folder — one sentence, one link.
- **5–6 numbered sections**, headed `## N. Imperative sentence`. Each explains why the rule holds,
  carries at most one or two code blocks or tables, and ends with a bold `**Done when:**` line
  stating an observable condition.
- **`## Report`** — names what to state at the end of the work, and the honest remaining gap.
  Every Report section on disk names something still not known or not covered.

Skeleton:

```markdown
---
name / description / license      # exactly as in section 2
---

# Skill Name

Two paragraphs framing the problem and the one idea that resolves it.

**The single bold principle line.**

For <what the reference holds>, read `references/topic.md`.

## 1. Imperative heading

Why the rule exists and what goes wrong without it.

**Done when:** an observable condition, not an intention.

## 2. Imperative heading   (through section 5 or 6)

## Report

What to state at the end: decisions made, values chosen, and the gap that remains.
```

## 5. Progressive disclosure

`SKILL.md` is loaded into context whenever the skill matches. Keep it under 500 lines; the files
on disk run 81–135 lines, which is the target range. Depth belongs in `references/`.

- Move long templates, command catalogues, matrices, and per-vendor detail into
  `references/<topic>.md`. Keep the argument in `SKILL.md`.
- Link reference files exactly one level deep from `SKILL.md`, as backtick paths of the form
  `references/topic.md`. A reference file must not link on to a third file; no detail should be
  two hops away.
- Give any reference file over 100 lines a `## Contents` list near the top, naming every section,
  so a partial read still shows the full scope. All 15 reference files on disk do this.

## 6. Style rules

- **One responsibility per skill.** If a section starts becoming a second skill, cross-reference
  the sibling instead. `gitops` points at `secrets-management` rather than explaining rotation.
- **Be opinionated and give the reason.** A rule without a reason is not memorable.
- **Principles over vendors.** Name tools to illustrate a point; never make the skill useless
  outside one product.
- **Cross-reference, do not repeat.** Name sibling skills in backticks, by skill name.
- **No placeholders.** No `TODO`, no stub sections, no invented flags. Every command, path, and
  file name must be real.
- **No marketing language and no emoji.** Plain prose, short sentences, imperative or third
  person.
- Wrap Markdown at roughly 100 columns. ATX headings. No trailing whitespace.

## 7. Validation

Run the validator before committing:

```bash
python3 scripts/check-skills.py
```

It must exit clean. It checks, for every `skills/*/*/SKILL.md`:

- Frontmatter is present and parses, with `name`, `description`, and `license`.
- `name` equals the folder name, and `license` is `MIT`.
- `description` is non-empty, at most 620 characters, and contains `Use this`.
- The body has a `## Report` section and at least one `**Done when:**` checkpoint.
- Code fences are balanced.

It also checks that `evals/<skill>.json` exists, is valid JSON, has a matching `skill_name`, and
holds three evals with the four required keys; that every `references/<file>` linked from a
`SKILL.md` exists on disk; that `.agents/skills/` matches the canonical tree with no stale
directories; and that `.claude-plugin/plugin.json` lists exactly the skills on disk.

The validator does not judge prose. The body shape in section 4 and the style rules in section 6
are enforced by review.
