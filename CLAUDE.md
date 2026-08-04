# CLAUDE.md

Repository conventions for agents live in `AGENTS.md`. Read it before editing anything here and
follow it — it defines the required shape of a skill, the frontmatter keys, and the commit checks.

The design rationale behind that structure is in `CONTEXT.md`.

Two rules worth restating:

- `.agents/skills/` is generated from `skills/<category>/<skill>/` by
  `scripts/build-antigravity.py`. Never edit it by hand; edit the canonical skill and rebuild.
- `python3 scripts/check-skills.py` must pass before any commit.
