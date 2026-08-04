# GitHub Actions patterns

Concrete patterns for the principles in SKILL.md, in GitHub Actions syntax. Copy these, don't
reinvent them.

## Contents

- Workflow / job / step structure
- Cache keyed on the lockfile hash
- Matrix builds
- Parallel jobs with `needs`
- Reusable workflows and composite actions
- Pin third-party actions by commit SHA
- OIDC instead of long-lived cloud keys
- Concurrency groups to cancel superseded runs
- Path and branch filters

## Workflow / job / step structure

A workflow lives under `.github/workflows/`. Jobs run in parallel on separate runners by default;
steps inside a job run sequentially and share a filesystem.

```yaml
on:
  push: { branches: [main] }
  pull_request: {}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
```

Keep jobs single-purpose — a job that lints, tests, and builds in one blob means a lint failure
still burns the minutes of a full test run, which loses the "first useful signal fast" property.

## Cache keyed on the lockfile hash

Never key a cache on branch name or a hand-bumped version string — someone forgets to bump it and
you silently serve stale `node_modules`. Key on `hashFiles()` of the lockfile instead, so the
cache invalidates exactly when dependencies change, regardless of who produced it.

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

`restore-keys` gives a partial-match fallback if the exact hash misses, without ever serving a
wrong exact match. `actions/setup-node` has a built-in `cache: npm` shortcut for this — prefer it
when it fits, drop to `actions/cache` directly when you need multiple paths or a non-npm ecosystem.

## Matrix builds

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, macos-latest]
    node: [18, 20]
runs-on: ${{ matrix.os }}
steps:
  - uses: actions/setup-node@v4
    with: { node-version: ${{ matrix.node }} }
```

`fail-fast: false` matters: the default cancels the whole matrix on the first failure, hiding
results for every other cell. Turn it off when you need the full failure surface; leave it on only
when any failure is equally fatal and you just want to stop burning minutes.

## Parallel jobs with `needs`

Jobs run in parallel unless you say otherwise. Use `needs` for real dependencies, not to force
ordering — every edge is wall-clock time your fastest job waits on.

```yaml
jobs:
  lint: { runs-on: ubuntu-latest, steps: [...] }
  unit-test: { runs-on: ubuntu-latest, steps: [...] }
  integration-test:
    needs: [lint, unit-test]
    runs-on: ubuntu-latest
    steps: [...]
```

`lint` and `unit-test` start simultaneously; `integration-test` waits for both. Don't chain stages
that could run concurrently just because it reads more linearly.

## Reusable workflows and composite actions

Composite action = reusable *steps*, called inside a job. Reusable workflow = a whole reusable
*job graph*, called at the job level, with its own inputs and secrets.

```yaml
# .github/actions/setup-project/action.yml — composite action
runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with: { node-version: '20' }
    - run: npm ci
      shell: bash
```

```yaml
# .github/workflows/reusable-deploy.yml — reusable workflow, called via `uses` at job level
on:
  workflow_call:
    inputs: { environment: { required: true, type: string } }
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps: [...]
# caller:  deploy-staging: { uses: ./.github/workflows/reusable-deploy.yml, with: { environment: staging } }
```

Use a composite action when several jobs repeat the same setup steps. Use a reusable workflow when
several repos or environments need the same job-level pipeline — this keeps deploy logic in one
place instead of copy-pasted across workflow files that quietly drift apart.

## Pin third-party actions by commit SHA

`uses: actions/checkout@v4` is a mutable pointer — the tag can be repointed at different code, by
the owner or by anyone who compromises their repo. A pinned SHA is immutable.

```yaml
# floats
- uses: actions/checkout@v4
# pinned — this exact commit always runs
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

This is a supply-chain argument (see `pipeline-security`), but it's also SKILL.md rule 2's
reproducibility argument: a mutable action version is exactly as dangerous as an unpinned
dependency. Pin third-party actions always; pin first-party ones too on workflows with real deploy
credentials. Keep the `# v4.2.2` comment — nobody can eyeball a SHA and know what it is.

## OIDC instead of long-lived cloud keys

A static AWS key or GCP JSON key in repo secrets works forever if leaked, and needs manual
rotation. OIDC lets the workflow request a short-lived token from the cloud provider, scoped to
this repo and run, with nothing long-lived stored anywhere.

```yaml
permissions:
  id-token: write   # default is 'none' — must opt in
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gha-deploy
          aws-region: us-east-1
      - run: aws s3 sync ./dist s3://my-bucket
```

The IAM role's trust policy restricts which repo/branch/environment can assume it. If the workflow
is compromised, the blast radius is a token expiring within the hour, not a key that works until
someone remembers to rotate it. Treat a long-lived cloud key in a repo secret as an exception,
not the default.

## Concurrency groups to cancel superseded runs

Without this, every push to a PR queues a full new run, and old runs keep burning minutes on code
that's already superseded.

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

`github.ref` scopes this per-branch, so pushes to the same PR cancel each other without colliding
with other PRs. Drop `cancel-in-progress` (or set it false) for deploy workflows, where an
in-flight rollout must finish, not be killed mid-deploy — cancellation is a CI-speed
optimization, not a CD default.

## Path and branch filters

Don't run the full pipeline when nothing relevant changed.

```yaml
on:
  push:
    branches: [main]
    paths: ['src/**', 'package-lock.json', '.github/workflows/ci.yml']
  pull_request:
    paths-ignore: ['**.md', 'docs/**']
```

Prefer an explicit `paths` allowlist when the repo has a clear code/non-code split — it fails
safe (a new unrelated top-level dir won't accidentally trigger CI). `paths-ignore` fails open
(anything you forgot to exclude still triggers). If you gate on `paths` at all, include the
workflow file itself, or a change to the pipeline's own logic never gets tested by the pipeline.
