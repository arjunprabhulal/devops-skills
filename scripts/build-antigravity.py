#!/usr/bin/env python3
"""Generate the Google Antigravity skill layout from the canonical skills/ tree.

Claude Code discovers skills from the category-nested `skills/<category>/<skill>/` tree
(listed in .claude-plugin/plugin.json). Google Antigravity discovers skills from a flat
`.agents/skills/<skill>/SKILL.md` layout (workspace root), or `~/.gemini/config/skills/`
when installed globally.

Both use the same SKILL.md format (YAML frontmatter with name + description, then the guide),
so this script simply flattens the canonical tree into `.agents/skills/`, carrying each skill's
`references/` folder along. Skill names are globally unique, so the flatten is lossless.

Run this after adding or editing any skill so the two layouts stay in sync:

    python3 scripts/build-antigravity.py
"""
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "skills")
DST = os.path.join(ROOT, ".agents", "skills")

# rebuild cleanly so deletions propagate
if os.path.isdir(DST):
    shutil.rmtree(DST)
os.makedirs(DST)

count = 0
names = {}
for category in sorted(os.listdir(SRC)):
    cat_dir = os.path.join(SRC, category)
    if not os.path.isdir(cat_dir):
        continue
    for skill in sorted(os.listdir(cat_dir)):
        s_dir = os.path.join(cat_dir, skill)
        skillmd = os.path.join(s_dir, "SKILL.md")
        if not os.path.isfile(skillmd):
            continue
        if skill in names:
            print(f"ERROR: duplicate skill name '{skill}' "
                  f"({category} vs {names[skill]}) — flatten would collide", file=sys.stderr)
            sys.exit(1)
        names[skill] = category
        # copy the whole skill folder (SKILL.md + references/ + any resources)
        shutil.copytree(s_dir, os.path.join(DST, skill))
        count += 1

# a short pointer so anyone browsing the folder knows it is generated
open(os.path.join(ROOT, ".agents", "README.md"), "w").write(
    "# .agents/ — Google Antigravity layout\n\n"
    "This directory is GENERATED from the canonical `skills/` tree by\n"
    "`scripts/build-antigravity.py`. Do not edit skills here directly — edit them under\n"
    "`skills/<category>/<skill>/` and re-run the script.\n\n"
    "`.agents/skills/<skill>/SKILL.md` is the layout Google Antigravity discovers in a\n"
    "workspace. For a global install, copy any skill folder into `~/.gemini/config/skills/`.\n"
)
print(f"Generated .agents/skills/ with {count} skills (flattened from {len(set(names.values()))} categories).")
