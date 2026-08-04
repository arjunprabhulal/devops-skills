# Installation

This repository holds 88 DevOps agent skills. Each skill is a single `SKILL.md` under
`skills/<category>/<skill-name>/`. The same files work in Claude Code and in Google Antigravity,
which reads a flat mirror of the tree at `.agents/skills/<skill-name>/`.

## Claude Code, as a plugin

Add the marketplace, then install the plugin. Both are slash commands, typed inside a Claude Code
session:

```bash
/plugin marketplace add arjunprabhulal/devops-skills
/plugin install devops-skills@arjunprabhulal
```

Installing the plugin registers all 88 skills at once. The list of skill paths is the `skills`
array in `.claude-plugin/plugin.json`; the marketplace entry pointing at this repository is
`.claude-plugin/marketplace.json`.

Registration is not the same as loading. Only each skill's frontmatter — `name` and `description`
— is preloaded into context. The body of a `SKILL.md` is read when the agent decides the skill is
relevant to the task at hand. Eighty-eight skills cost 88 short descriptions of context, not 88
full documents.

## Any harness, via the skills CLI

The [skills.sh](https://www.skills.sh/) CLI installs skills straight from a GitHub repository, and
works across agents rather than only Claude Code:

```bash
npx skills add arjunprabhulal/devops-skills
```

The CLI discovers skills up to two levels below `skills/`, so the category layout used here —
`skills/<category>/<skill-name>/SKILL.md` — is read directly with no build step. It also recognizes
`.claude-plugin/plugin.json`, which this repository provides.

Eighty-eight skills is a lot to take at once. To see what is on offer without writing anything:

```bash
npx skills add arjunprabhulal/devops-skills --list
```

To install a named subset instead of everything:

```bash
npx skills add arjunprabhulal/devops-skills -s kubernetes-operations,incident-response,gitops
```

Other flags worth knowing:

- `--all` — every skill, every detected agent, no prompts.
- `-g`, `--global` — install at user level rather than into the current project.
- `-a <agents>` — target specific agents, or `'*'` for all of them.
- `--copy` — copy the files instead of symlinking them into agent directories.
- `npx skills use arjunprabhulal/devops-skills@<skill>` — generate the prompt for one skill without
  installing anything.

Installed skills are then managed with `npx skills list`, `npx skills update`, and
`npx skills remove`.

## Claude Code, a single skill, manually

To use one skill without the plugin, copy its folder into a skills directory:

- `.claude/skills/` in a project — available in that project only.
- `~/.claude/skills/` — available in every project.

Installing `kubernetes-operations` for the current project:

```bash
mkdir -p .claude/skills
cp -r skills/kubernetes/kubernetes-operations .claude/skills/
```

For all projects:

```bash
cp -r skills/kubernetes/kubernetes-operations ~/.claude/skills/
```

Copy the whole folder, not just `SKILL.md`. Fifteen skills carry a `references/` subfolder linked
relatively from the skill body. `kubernetes-operations` is one of them, and its links break if that
folder is left behind.

## Google Antigravity

Antigravity uses the same `SKILL.md` format and discovers skills from a flat
`.agents/skills/<skill-name>/` layout. That layout is prebuilt and committed here, so no conversion
step is needed. See <https://antigravity.google/docs/skills>.

Workspace skills — open this repository in Antigravity, or copy its `.agents/` folder into
the root of another project. Every skill under `.agents/skills/` is discovered automatically.

Global skills — copy a skill folder into `~/.gemini/config/skills/` to make it available across
all workspaces. The Antigravity tree is flat, so no category segment appears in the source path:

```bash
cp -r .agents/skills/kubernetes-operations ~/.gemini/config/skills/
```

Frontmatter here carries three keys: `name`, `description`, and `license`. Antigravity reads
`name` and `description` and ignores the extra `license` field. No edit is needed to make a skill
load.

The `.agents/skills/` tree is generated from `skills/` by `scripts/build-antigravity.py`. Do not
edit files under `.agents/skills/` — edit the canonical copy under `skills/<category>/<skill>/` and
re-run:

```bash
python3 scripts/build-antigravity.py
```

## Antigravity rules and workflows

A skill file can also be used through Antigravity's two other mechanisms. See
<https://antigravity.google/docs/rules-workflows>.

As a rule — drop the file under `.agents/rules/` in a workspace. Rules apply always-on or by file
glob rather than being selected by the agent from a description. Use this when a skill's guidance
should hold for every task in a repository.

As a workflow — wrap a multi-step skill as a workflow and invoke it by name, as `/workflow-name`.
Use this when the steps should run on request rather than whenever the agent judges them relevant.

## Verifying the install

In Claude Code, run `/plugin` to list installed plugins and confirm `devops-skills@arjunprabhulal`
is there. For a manually copied skill, confirm the file is where the agent looks:

```bash
ls ~/.claude/skills/kubernetes-operations/SKILL.md
```

The real test is discovery, not file placement. Ask something that matches a skill's trigger — for
`kubernetes-operations`, debugging a pod stuck in `CrashLoopBackOff` — and check that the agent
reaches for the skill.

That match is driven entirely by the `description` frontmatter. Each description states when to use
the skill ("Use this whenever…") and which sibling to use instead for adjacent problems. It is the
only part of the skill the agent sees before deciding. A skill that never fires usually has a
description that does not name the situation the user described.

To check the repository itself rather than an install, run the validator:

```bash
python3 scripts/check-skills.py
```

It checks every skill, its eval file, the README catalogue, the plugin manifest, and the
`.agents/skills/` mirror. The full list of checks is in
[architecture.md](architecture.md#scriptscheck-skillspy).

## Updating and uninstalling

The plugin is installed from this repository through the marketplace, so both updating and removing
it are done from the `/plugin` menu in Claude Code, which lists the installed plugins and their
marketplaces.

Manually copied skills are updated by copying the folder again. `cp -r` overwrites `SKILL.md` but
leaves stale files behind in `references/`; delete the destination folder first if a skill's
references have changed. Removing a skill means deleting its folder:

```bash
rm -rf ~/.claude/skills/kubernetes-operations
rm -rf ~/.gemini/config/skills/kubernetes-operations
```

Workspace skills in Antigravity go away with the `.agents/` folder, or by deleting the individual
directory under `.agents/skills/`. If that directory was generated here, it returns on the next
`scripts/build-antigravity.py` run.
