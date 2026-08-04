<!-- One skill, or one concern, per pull request. -->

## What this changes

<!-- The skill or file affected, and what is different after this change. -->

## Why

<!-- Skills in this repository take positions. If this adds or changes an opinion, say what the
     opinion is and what evidence or experience supports it. If it corrects something, say what
     was wrong. -->

## Checklist

- [ ] `python3 scripts/check-skills.py` passes
- [ ] `python3 scripts/build-antigravity.py` was re-run if any skill changed, and `.agents/` is committed
- [ ] No files under `.agents/skills/` were edited by hand
- [ ] New skill only: eval file added at `evals/<skill>.json` with 3 cases
- [ ] New skill only: skill path added to `.claude-plugin/plugin.json`
- [ ] New skill only: cross-references an existing sibling skill rather than repeating it
