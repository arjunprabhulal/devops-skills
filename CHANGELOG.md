# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Changes land here before they are cut into a release.

## [1.0.0] - 2026-08-03

### Added

- 88 skills under `skills/<category>/<skill-name>/SKILL.md`, across 15 categories:
  - CI/CD — 8 skills (`skills/ci-cd/`)
  - Containers — 4 skills (`skills/containers/`)
  - Kubernetes — 9 skills (`skills/kubernetes/`)
  - Infrastructure as Code — 6 skills (`skills/iac/`)
  - Cloud — 6 skills (`skills/cloud/`)
  - GitOps — 3 skills (`skills/gitops/`)
  - Observability — 7 skills (`skills/observability/`)
  - Reliability and SRE — 8 skills (`skills/reliability/`)
  - Security and DevSecOps — 8 skills (`skills/security/`)
  - Networking — 6 skills (`skills/networking/`)
  - Data and Storage — 5 skills (`skills/data/`)
  - Platform Engineering — 5 skills (`skills/platform-engineering/`)
  - Automation — 5 skills (`skills/automation/`)
  - FinOps — 4 skills (`skills/finops/`)
  - Performance — 4 skills (`skills/performance/`)
- One eval file per skill at `evals/<skill>.json`, each holding three cases with a `prompt` and an
  `expected_output`.
- `references/` deep-dive folders for 15 skills: `ci-pipelines`, `containerization`,
  `kubernetes-operations`, `infrastructure-as-code`, `well-architected-review`,
  `argocd-operations`, `metrics-and-monitoring`, `incident-response`, `secrets-management`,
  `network-troubleshooting`, `data-migration`, `internal-developer-platform`, `scheduled-jobs`,
  `cost-optimization`, and `performance-tuning`.
- `scripts/build-antigravity.py`, which generates the flat `.agents/skills/<skill-name>/` layout
  Google Antigravity discovers, mirroring each `SKILL.md` and its `references/` folder. The
  generated tree is gitignored rather than committed, because skill registries scan
  `.agents/skills/` and would otherwise index every skill twice.
- `scripts/check-skills.py`, which validates frontmatter against the Agent Skills specification
  (`name` length and character set, reserved words, `description` length and absence of XML tags),
  name/folder match, description triggers, body length under 500 lines, `Done when:` checkpoints,
  the `Report` section, code fence balance, eval files, reference links and the `## Contents` list
  required on reference files over 100 lines, the `README.md` catalogue against each skill's
  current description, `.claude-plugin/plugin.json` agreement with the skills on disk, and
  `.agents/skills/` sync.
- Claude Code plugin manifests: `.claude-plugin/plugin.json` listing all 88 skill paths, and
  `.claude-plugin/marketplace.json`.
- GitHub Actions workflow `.github/workflows/ci.yml`, which runs `scripts/check-skills.py` and
  builds the Antigravity layout first, on pushes to `main` and on pull requests.
- Issue and pull request templates under `.github/`.
- Documentation: `README.md` with the skill catalogue, `docs/installation.md`,
  `docs/authoring-skills.md`, `docs/evals.md`, `docs/architecture.md`, `docs/faq.md`,
  `AGENTS.md` for repository conventions and design rationale, `CLAUDE.md` as its pointer,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and the MIT `LICENSE`.

[Unreleased]: https://github.com/arjunprabhulal/devops-skills/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/arjunprabhulal/devops-skills/releases/tag/v1.0.0
