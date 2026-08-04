# Repository architecture

How this repository is put together: where files live, which tree is authoritative, what the two
scripts do, and how a change moves through the repo.

## Directory map

| Path | Purpose |
| --- | --- |
| `skills/<category>/<skill>/SKILL.md` | Canonical skill sources. 88 skills, 15 category folders. |
| `skills/<category>/<skill>/references/` | Optional deep-dive files. 15 skills have one. |
| `.agents/skills/<skill>/` | Generated flat mirror of every skill, for Google Antigravity. |
| `.agents/README.md` | Generated note stating that `.agents/` is built, not hand-written. |
| `evals/<skill>.json` | Three evaluation cases per skill, one file per skill name. |
| `scripts/build-antigravity.py` | Regenerates `.agents/skills/` from `skills/`. |
| `scripts/check-skills.py` | Validates skills, evals, references, both layouts, and `plugin.json`. |
| `.claude-plugin/plugin.json` | Claude Code plugin manifest. Lists all 88 skill paths. |
| `.claude-plugin/marketplace.json` | Marketplace entry making the repo installable as a plugin. |
| `.github/workflows/ci.yml` | Runs the validator on push to `main` and on pull requests. |
| `AGENTS.md` | Conventions for agents and humans editing the repo. |
| `README.md` | Skill catalog and installation instructions. |
| `docs/architecture.md` | This file. |
| `.claude/settings.local.json` | Machine-local agent settings. Ignored by git. |
| `LICENSE` | MIT. |

The 15 categories are `automation`, `ci-cd`, `cloud`, `containers`, `data`, `finops`, `gitops`,
`iac`, `kubernetes`, `networking`, `observability`, `performance`, `platform-engineering`,
`reliability`, and `security`.

## Two layouts, one source

Skills exist in two directory shapes because the two tools that consume them discover them
differently. `skills/<category>/<skill>/` is canonical and is the only place a skill is edited. The
Claude Code plugin manifest points at these paths directly: every entry in the `skills` array of
`.claude-plugin/plugin.json` is a path of the form `./skills/<category>/<skill>`.

`.agents/skills/<skill>/` is the flat layout Google Antigravity discovers in a workspace. Category
folders are dropped; each skill sits directly under `.agents/skills/`. Skill names are unique
across the whole repo, so flattening loses nothing.

The generated tree is committed to git. Cloning the repo into an Antigravity workspace is enough —
there is no build step for a consumer. That convenience has one cost: the mirror can drift, so the
validator compares it against the canonical tree on every run.

Never hand-edit anything under `.agents/skills/`. The build script deletes the directory and
recreates it, so edits made there are lost on the next build. Edit the canonical copy and rebuild.

## scripts/build-antigravity.py

Source is `skills/`, destination is `.agents/skills/`. The script:

1. Deletes `.agents/skills/` entirely if it exists, then recreates it. The clean rebuild is what
   makes deletions and renames propagate instead of leaving stale folders.
2. Walks category folders in sorted order, then skill folders in sorted order. A skill folder is
   only considered if it contains a `SKILL.md`.
3. Fails on a duplicate skill name: it prints which two categories collided and exits 1.
4. Copies each skill folder whole with `shutil.copytree` — `SKILL.md`, `references/`, and any other
   resource files.
5. Writes `.agents/README.md`, the pointer explaining that the directory is generated and that a
   global Antigravity install means copying a skill folder into `~/.gemini/config/skills/`.
6. Prints the number of skills generated and the number of source categories.

The script rewrites no skill content. `SKILL.md` files are copied byte for byte; both tools read
the same frontmatter format, so no path fixups are needed. The only file whose text the script
authors is `.agents/README.md`.

## scripts/check-skills.py

The validator globs `skills/*/*/SKILL.md`, collects every failure into one list, then prints them
all and exits 1. On success it prints the skill and category counts.

Per `SKILL.md`:

- The file starts with `---` frontmatter. A file that does not is reported and skipped.
- `name` in the frontmatter equals the containing folder name.
- `license` is exactly `MIT`.
- `description` is present, is 620 characters or fewer, and contains the string `Use this`.
- The body contains a `## Report` section.
- The body contains at least one `**Done when:**` checkpoint.
- The count of ``` fences is even.

Per eval file:

- `evals/<skill>.json` exists for every skill on disk.
- It parses as JSON.
- Its `skill_name` field equals the skill folder name.
- Its `evals` field is a list of exactly three entries.
- Each entry has `id`, `prompt`, `expected_output`, and `files`.

Reference links: every `` `references/<file>` `` mentioned in a `SKILL.md` resolves to a real file
in that skill's own `references/` folder.

Antigravity layout, checked when `.agents/skills/` exists:

- `.agents/skills/<skill>/SKILL.md` exists for every canonical skill.
- Its contents are identical to the canonical file. Any difference is reported as out of sync.
- No directory under `.agents/skills/` lacks a canonical counterpart. Extras are reported as stale.

Plugin manifest: the set of last path segments in `plugin.json`'s `skills` array equals the set of
skill folder names on disk. Skills on disk but unlisted, and listed skills missing on disk, are
reported separately.

## The plugin manifests

`.claude-plugin/plugin.json` is the plugin definition: `name`, `version`, `description`, `author`,
`repository`, `license`, `keywords`, and the `skills` array of 88 relative paths into `skills/`.
The array is the load list — a skill that is not listed is not loaded.

Adding a skill means adding its `./skills/<category>/<skill>` path to that array. The validator
enforces this, so a forgotten entry fails the build rather than silently disabling the skill.

`.claude-plugin/marketplace.json` is the marketplace index. It names the owner and lists one plugin
entry, `devops-skills`, whose `source` is `./` — marketplace and plugin live in the same repository.
It carries a category and keywords for discovery, and does not list individual skills.

## CI

`.github/workflows/ci.yml` defines the `validate-skills` workflow. It triggers on pushes to `main`
and on every pull request, with read-only `contents` permission. It has two jobs, each checking
out the repo on `ubuntu-latest` and setting up Python 3.12:

- `validate` runs `python3 scripts/check-skills.py`. The validator's non-zero exit fails the job.
- `generated-tree-is-current` runs `python3 scripts/build-antigravity.py`, then fails on any
  `git diff`. A diff means the generated tree was hand-edited or a canonical change landed without
  a rebuild.

CI runs no other step. The validator also compares the two trees, so a stale mirror fails both
jobs.

## How a change flows through the repo

1. Edit the canonical file: `skills/<category>/<skill>/SKILL.md`, plus its `references/` files.
2. For a new skill, add `evals/<skill>.json` with three cases, add the skill's path to
   `.claude-plugin/plugin.json`, and add its catalogue row to `README.md`.
3. Rebuild the flat tree: `python3 scripts/build-antigravity.py`.
4. Run the validator: `python3 scripts/check-skills.py`. Fix everything it reports.
5. Commit both trees together — the canonical change and the regenerated `.agents/skills/` output
   in the same commit, so the two layouts never disagree in history.
