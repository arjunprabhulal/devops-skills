#!/usr/bin/env python3
"""Validate every skill in the repo. Run: python3 scripts/check-skills.py

Checks each skills/<category>/<skill>/SKILL.md for:
  - valid YAML frontmatter with name, description, license
  - name matches its folder, and meets the Agent Skills spec (<=64 chars,
    lowercase letters/numbers/hyphens only, no reserved words)
  - description within a sane length, free of XML tags, containing a trigger phrase
  - a body under 500 lines, per progressive-disclosure guidance
  - a Report section and at least one Done-when checkpoint
  - balanced code fences
Also checks reference files (one level deep, Contents list once over 100 lines),
eval files, the generated Antigravity layout, that README.md lists every skill with
its current description, and that .claude-plugin/plugin.json matches the skills on disk.

Spec: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
"""
import json, os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []

skill_files = sorted(glob.glob(os.path.join(ROOT, "skills", "*", "*", "SKILL.md")))
for f in skill_files:
    rel = os.path.relpath(f, ROOT)
    folder = os.path.basename(os.path.dirname(f))
    txt = open(f, encoding="utf-8").read()
    if not txt.startswith("---"):
        errors.append(f"{rel}: missing frontmatter"); continue
    fm = txt.split("---", 2)[1]
    def key(k):
        m = re.search(rf'^{k}:\s*(.+)$', fm, re.M)
        return m.group(1).strip() if m else None
    name, desc, lic = key("name"), key("description"), key("license")
    if name != folder:
        errors.append(f"{rel}: name '{name}' != folder '{folder}'")
    if name and len(name) > 64:
        errors.append(f"{rel}: name {len(name)} chars (spec max 64)")
    if name and not re.fullmatch(r"[a-z0-9-]+", name):
        errors.append(f"{rel}: name '{name}' must be lowercase letters, numbers, hyphens only")
    if name and re.search(r"anthropic|claude", name):
        errors.append(f"{rel}: name '{name}' contains a reserved word")
    if lic != "MIT":
        errors.append(f"{rel}: license is '{lic}', expected MIT")
    if not desc:
        errors.append(f"{rel}: missing description")
    else:
        # Spec ceiling is 1024; this repo holds a tighter house limit for scannability.
        if len(desc) > 620:
            errors.append(f"{rel}: description {len(desc)} chars (>620)")
        if re.search(r"<[A-Za-z/]", desc):
            errors.append(f"{rel}: description contains an XML tag")
        if "Use this" not in desc:
            errors.append(f"{rel}: description lacks a 'Use this…' trigger")
    body_lines = len(txt.split("---", 2)[2].splitlines())
    if body_lines > 500:
        errors.append(f"{rel}: body {body_lines} lines (>500, split into references/)")
    if "## Report" not in txt:
        errors.append(f"{rel}: missing '## Report' section")
    if "**Done when:**" not in txt:
        errors.append(f"{rel}: no '**Done when:**' checkpoint")
    if txt.count("```") % 2 != 0:
        errors.append(f"{rel}: unbalanced code fences")

# evals: one JSON per skill, skill_name matches, 3 well-formed evals
for f in skill_files:
    skill = os.path.basename(os.path.dirname(f))
    ev = os.path.join(ROOT, "evals", skill + ".json")
    if not os.path.exists(ev):
        errors.append(f"evals/{skill}.json: missing"); continue
    try:
        data = json.load(open(ev, encoding="utf-8"))
    except Exception as e:
        errors.append(f"evals/{skill}.json: invalid JSON ({e})"); continue
    if data.get("skill_name") != skill:
        errors.append(f"evals/{skill}.json: skill_name '{data.get('skill_name')}' != '{skill}'")
    evs = data.get("evals", [])
    if not isinstance(evs, list) or len(evs) != 3:
        errors.append(f"evals/{skill}.json: expected 3 evals, got {len(evs) if isinstance(evs,list) else 'non-list'}")
    for i, e in enumerate(evs if isinstance(evs, list) else [], 1):
        for k in ("id", "prompt", "expected_output", "files"):
            if k not in e:
                errors.append(f"evals/{skill}.json eval {i}: missing '{k}'")

# reference links: every references/<file>.md a SKILL.md points to must exist
ref_re = re.compile(r'`references/([A-Za-z0-9._-]+)`')
for f in skill_files:
    body = open(f, encoding="utf-8").read()
    d = os.path.dirname(f)
    for ref in ref_re.findall(body):
        if not os.path.exists(os.path.join(d, "references", ref)):
            errors.append(f"{os.path.relpath(f, ROOT)}: broken reference link references/{ref}")

# reference files: one level deep from SKILL.md, and a Contents list once over 100 lines,
# so a partial read still shows the full scope of the file.
for r in sorted(glob.glob(os.path.join(ROOT, "skills", "*", "*", "references", "*.md"))):
    rel = os.path.relpath(r, ROOT)
    txt = open(r, encoding="utf-8").read()
    if len(txt.splitlines()) > 100 and not re.search(r"^##\s+Contents\s*$", txt, re.M):
        errors.append(f"{rel}: over 100 lines without a '## Contents' list")
    if re.search(r"\]\((?!https?://)[^)]*\.md\)", txt):
        errors.append(f"{rel}: links to another file (references must be one level deep)")
    if re.search(r"`[A-Za-z0-9_.-]+\\[A-Za-z0-9_.-]+`", txt):
        errors.append(f"{rel}: Windows-style path (use forward slashes)")

# README.md must list every skill with its current description, so the catalogue
# cannot silently drift from the skills themselves.
readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
rows = dict(re.findall(r'\|\s*\[`([a-z0-9-]+)`\]\([^)]+\)\s*\|\s*(.+?)\s*\|\s*$', readme, re.M))
for f in skill_files:
    rel = os.path.relpath(f, ROOT)
    skill = os.path.basename(os.path.dirname(f))
    fm = open(f, encoding="utf-8").read().split("---", 2)[1]
    m = re.search(r"^description:\s*(.+)$", fm, re.M)
    want = re.split(r"\.\s+Use this", m.group(1).strip())[0].rstrip(".").replace("|", r"\|")
    if skill not in rows:
        errors.append(f"README.md: skill not listed in the catalogue: {skill}")
    elif rows[skill] != want:
        errors.append(f"README.md: '{skill}' row does not match its description in {rel}")
for listed in sorted(set(rows) - {os.path.basename(os.path.dirname(f)) for f in skill_files}):
    errors.append(f"README.md: lists a skill that is not on disk: {listed}")

# Hardcoded totals in README.md and the manifests must track the skills on disk.
n_skills = len(skill_files)
n_cats = len({os.path.basename(os.path.dirname(os.path.dirname(f))) for f in skill_files})
if f"badge/skills-{n_skills}-" not in readme:
    errors.append(f"README.md: skill-count badge does not say {n_skills}")
if not re.search(rf"^{n_skills} \[Agent Skills\]", readme, re.M):
    errors.append(f"README.md: opening line does not say {n_skills} skills")
for cat_row in re.findall(r"^\| ([A-Za-z/ &]+?) \| (\d+) \| ", readme, re.M):
    label, claimed = cat_row[0].strip(), int(cat_row[1])
    hits = [f for f in skill_files
            if os.path.basename(os.path.dirname(os.path.dirname(f)))
            == {"CI/CD": "ci-cd", "Infrastructure as Code": "iac", "Reliability & SRE": "reliability",
                "Security & DevSecOps": "security", "Data & Storage": "data",
                "Platform Engineering": "platform-engineering"}.get(label, label.lower())]
    if hits and len(hits) != claimed:
        errors.append(f"README.md: category '{label}' says {claimed}, disk has {len(hits)}")

for mf, path in (("plugin.json", os.path.join(ROOT, ".claude-plugin", "plugin.json")),
                 ("marketplace.json", os.path.join(ROOT, ".claude-plugin", "marketplace.json"))):
    blob = open(path, encoding="utf-8").read()
    counted = re.findall(r"\b(\d{2,3}) (?:DevOps )?(?:agent )?(?:skills|SKILL\.md|field guides)\b", blob)
    if not counted:
        errors.append(f"{mf}: no skill count found to check — reword or update this check")
    for stale in counted:
        if int(stale) != n_skills:
            errors.append(f"{mf}: says {stale}, disk has {n_skills} skills")

# Antigravity layout: .agents/skills/<skill>/SKILL.md must exist and match the canonical copy
agents_dir = os.path.join(ROOT, ".agents", "skills")
if os.path.isdir(agents_dir):
    for f in skill_files:
        skill = os.path.basename(os.path.dirname(f))
        mirror = os.path.join(agents_dir, skill, "SKILL.md")
        if not os.path.exists(mirror):
            errors.append(f".agents/skills/{skill}/SKILL.md: missing (run scripts/build-antigravity.py)")
        elif open(mirror, encoding="utf-8").read() != open(f, encoding="utf-8").read():
            errors.append(f".agents/skills/{skill}/SKILL.md: out of sync (run scripts/build-antigravity.py)")
    canonical_names = {os.path.basename(os.path.dirname(f)) for f in skill_files}
    for extra in sorted(set(os.listdir(agents_dir)) - canonical_names):
        if os.path.isdir(os.path.join(agents_dir, extra)):
            errors.append(f".agents/skills/{extra}: not in canonical skills/ (stale — rebuild)")

# plugin.json <-> disk
pj = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
listed = {p.rstrip("/").split("/")[-1] for p in pj["skills"]}
ondisk = {os.path.basename(os.path.dirname(f)) for f in skill_files}
missing = ondisk - listed
extra = listed - ondisk
for m in sorted(missing):
    errors.append(f"plugin.json: skill on disk not listed: {m}")
for e in sorted(extra):
    errors.append(f"plugin.json: listed skill missing on disk: {e}")

print(f"Checked {len(skill_files)} skills across "
      f"{len({os.path.basename(os.path.dirname(os.path.dirname(f))) for f in skill_files})} categories.")
if errors:
    print(f"\n{len(errors)} problem(s):")
    for e in errors:
        print("  ✗", e)
    sys.exit(1)
print("All skills valid. ✓")
