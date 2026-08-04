# Contributing

This repository holds 88 DevOps Agent Skills across 15 categories. Each skill is one `SKILL.md`
under `skills/<category>/<skill-name>/`, plus a three-case eval file under `evals/`. Repo
conventions are in `AGENTS.md`; read it before making a change.

## Scope

In scope:

- **A new skill** covering one DevOps responsibility that no existing skill covers.
- **A fix to an existing skill** — a wrong command, an outdated default, a missing step, a
  `Done when:` line that does not describe a checkable state.
- **A reference file** under a skill's `references/` folder, for material too long or too
  lookup-shaped to sit in `SKILL.md`.
- **An eval** — a correction to an existing `evals/<skill>.json` case, or the three cases required
  by a new skill.

Out of scope:

- **Vendor-specific product tutorials.** Skills name tools to illustrate a principle. A skill that
  only works if the reader uses one product does not belong here.
- **Duplicate skills that overlap an existing one.** One responsibility per skill. If the material
  fits inside an existing skill, extend that skill or cross-reference it by name instead of adding
  a second one.

## The shape of a skill

Every `SKILL.md` follows the same structure: frontmatter with exactly `name`, `description`, and
`license: MIT`; an intro ending in a single bold principle line; five or six numbered
`## N. Imperative heading` sections, each ending in a concrete `**Done when:**` line naming a state
that can be checked; and a closing `## Report` stating the key decisions and the honest remaining
gap.

The frontmatter rules, the Agent Skills length and character constraints, how to write a
description that triggers correctly, the body skeleton, and the reference-file rules are set out in
[docs/authoring-skills.md](docs/authoring-skills.md). Read it before writing a new skill.

Two more rules from `AGENTS.md`: be opinionated and explain why, since a rule without a reason is
not memorable; and no placeholders — a skill must be complete and technically correct when it
lands.

## Adding a skill

1. Create the folder under the category it belongs to: `skills/<category>/<skill-name>/`. Skill
   names are globally unique across categories — the Antigravity build flattens the tree and fails
   on a collision.
2. Write `skills/<category>/<skill-name>/SKILL.md` in the shape described above.
3. Add the eval file at `evals/<skill-name>.json`: `skill_name` matching the folder name and an
   `evals` array of exactly three cases. The schema, the three-case convention, and how to write an
   `expected_output` are in [docs/evals.md](docs/evals.md).
4. Add the skill path to the `skills` array in `.claude-plugin/plugin.json`, in the form
   `./skills/<category>/<skill-name>`.
5. Add a row for the skill to its category table in `README.md`. The validator requires one, and
   requires its text to match the skill's `description` up to the `Use this` trigger. Update the
   category count in the summary table at the top of the same section.
6. Regenerate the Antigravity layout:

   ```bash
   python3 scripts/build-antigravity.py
   ```

7. Run the validator and fix anything it reports:

   ```bash
   python3 scripts/check-skills.py
   ```

   It checks every skill, its eval file, the `README.md` catalogue, `.claude-plugin/plugin.json`,
   and the `.agents/skills/` mirror; the full list of checks is in
   [docs/architecture.md](docs/architecture.md#scriptscheck-skillspy). The same script runs in CI on
   every pull request via `.github/workflows/ci.yml`.

## Never edit .agents/skills/ by hand

`.agents/skills/` is the flat layout Google Antigravity discovers. It is generated from the
canonical `skills/` tree by `scripts/build-antigravity.py`, which deletes and rebuilds the whole
directory on every run. Edits made there are overwritten. Edit the canonical copy under
`skills/<category>/<skill-name>/` and rebuild.

## Pull requests

- **One skill, or one concern, per pull request.** A PR that adds a skill and also rewrites three
  others is hard to review and hard to revert.
- **The validator must pass.** Run `python3 scripts/check-skills.py` before opening the PR; CI runs
  it again.
- **Explain the reasoning behind an opinion the skill takes.** Skills here are opinionated by
  design. If a skill says to do something one way, the PR description should say what goes wrong
  when it is done the other way. That reasoning is what makes the opinion reviewable.

## Reporting problems

Open an issue at
<https://github.com/arjunprabhulal/devops-skills/issues>.

For a skill that produced bad behavior, a transcript showing the agent doing the wrong thing is
more useful than a prose description of it. Include the prompt, which skill loaded, and what the
agent did. That makes the failure reproducible and often maps directly onto a new eval case.
