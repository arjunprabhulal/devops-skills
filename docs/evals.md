# Evals

Every skill has a matching eval file at `evals/<skill-name>.json` — 88 skills, 88 eval files.

## What the eval files are for

A `SKILL.md` can read well and still change nothing about how an agent behaves. The eval file is
the check on that. Each case states, in plain prose, the behavior a well-guided agent should show
on a prompt the skill covers — the decision it makes, the order it does things in, the thing it
refuses to do.

Eval cases are written against behavior, not text. They do not assert that a skill mentions a term
or that an answer contains a phrase. If a skill is loaded and the response still misses what the
eval describes, the skill is not doing its job, however good the prose is.

## The three-case convention

Every eval file has exactly three cases, always in the same order and always with ids `1`, `2`, `3`.
The three cases test three different things.

**Case 1 — do the task.** An open request to perform the work the skill covers. Checks that the
skill's default path is followed without being asked for. From `evals/gitops.json`:
`"how should we lay out our deployment repo for prod and staging"`.

**Case 2 — diagnose and fix a broken situation.** A symptom described the way someone would
actually describe it, with the cause left out. Checks that the skill leads to the underlying
failure mode rather than the surface complaint. From `evals/cost-optimization.json`:
`"we bought reserved instances but the bill keeps growing"`.

**Case 3 — push back on an anti-pattern.** The user states a plan that the skill exists to argue
against. The correct behavior is to disagree, and the `expected_output` says so. From
`evals/slo-definition.json`: `"let's set the SLO to five nines so everyone knows we take
reliability seriously"`. Its `expected_output` opens with "Pushes back that a target above what the
system has ever sustained means the budget starts already spent", then names the alternative:
derive the target from historical performance and user tolerance.

Prompts across the repo are written in the register users actually type in — lowercase, terse, no
punctuation discipline. An eval prompt that reads like documentation tests a question nobody asks.

## Schema

The file is a JSON object with two keys.

| Field | Type | Meaning |
| --- | --- | --- |
| `skill_name` | string | The skill's folder name. Matches the filename and frontmatter `name`. |
| `evals` | array | Exactly three case objects. |

Each object in `evals` has four keys.

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | integer | `1`, `2`, or `3`, matching the case order above. |
| `prompt` | string | The user message given to the agent. |
| `expected_output` | string | Prose describing the behavior a correct response shows. |
| `files` | array | File paths giving the case repo context. Empty in every eval file on disk. |

A complete file, `evals/incident-response.json`:

```json
{
  "skill_name": "incident-response",
  "evals": [
    {
      "id": 1,
      "prompt": "prod is down, help me run this incident",
      "expected_output": "Names an incident commander within the first five minutes, sets a severity level that matches current customer impact, and pushes to mitigate (rollback, failover, shed load) before diagnosing root cause.",
      "files": []
    },
    {
      "id": 2,
      "prompt": "three engineers are fixing the same alert differently and nobody knows the status",
      "expected_output": "Diagnoses this as the classic no-named-IC failure mode, assigns a single incident commander to own decisions, limits who can push changes, and moves to one channel of record with a fixed communication cadence.",
      "files": []
    },
    {
      "id": 3,
      "prompt": "let's hold off on any fix until we're sure we know the root cause",
      "expected_output": "Pushes back: mitigate before you diagnose, since a reversible mitigation like rollback or traffic shift reduces customer harm now, and root-causing under live impact is optimizing for the wrong goal - understanding can follow once impact is stopped.",
      "files": []
    }
  ]
}
```

## Writing an `expected_output`

Describe behavior that an observer could confirm or deny by reading a response.

- **Name observable actions, not wording.** "Pulls the billing export before optimizing from
  memory" is observable. "Explains cost optimization well" is not.
- **Make it falsifiable.** Every clause should be something a response can fail. If no plausible
  response fails it, the clause tests nothing.
- **State the ordering when ordering is the point.** Mitigate before diagnose, rightsize before
  committing spend, rotate before purging history. Write the order into the expectation.
- **Do not restate the skill.** Name the two or three behaviors that would be absent if the skill
  had not been loaded, not a summary of `SKILL.md`.
- **Keep it to a sentence or two.** Long expectations stop being falsifiable, because some part of
  them is always satisfied.

For case 3, make the disagreement explicit. Every case-3 expectation in the repo starts with the
agent contradicting the plan, then gives the reason and the alternative.

## Running them

This repository ships no eval runner. Nothing under `scripts/` executes an eval file, and
`.github/workflows/ci.yml` runs only the validator and the generated-tree drift check — neither
sends a prompt to a model. The eval files are a specification: feed each
`prompt` to an agent with the matching skill available and judge the response against
`expected_output`, by hand or with a model-graded check, in whatever harness is being used.

What the repo does provide is a shape check:

```bash
python3 scripts/check-skills.py
```

For each skill, it confirms that `evals/<skill>.json` exists, is valid JSON, has a `skill_name`
matching the folder, has exactly three entries in `evals`, and that each entry has `id`, `prompt`,
`expected_output`, and `files`. It does not read the content of any prompt or expectation, and it
does not run anything.

## Adding an eval file for a new skill

1. Write the skill at `skills/<category>/<skill-name>/SKILL.md`.
2. Create `evals/<skill-name>.json` with `skill_name` set to the folder name.
3. Write the three cases in order: do the task, diagnose and fix, push back on an anti-pattern. Set
   `files` to `[]` unless the case needs repo context.
4. Add the skill's path to `.claude-plugin/plugin.json` and its catalogue row to `README.md`.
5. Run `python3 scripts/build-antigravity.py` to regenerate the flat `.agents/skills/` layout.
6. Run `python3 scripts/check-skills.py` and fix what it reports.

The full contribution procedure is in [CONTRIBUTING.md](../CONTRIBUTING.md).
