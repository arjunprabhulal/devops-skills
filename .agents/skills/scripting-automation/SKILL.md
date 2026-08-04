---
name: scripting-automation
description: Covers writing operational scripts that survive contact with production — idempotency, real error handling and exit codes, structured logging, a dry-run mode, and recognizing when a script has outgrown scripting. Use this whenever the user is writing a bash or Python script that touches production, asks why a script failed silently or left things half-changed, wants a `--dry-run` flag added, or is deciding whether a script should become a proper tool or service. For chaining scripts into a multi-step process use `workflow-automation`, and for running one on a schedule use `scheduled-jobs`.
license: MIT
---

# Scripting Automation

A script written for a one-off task gets run again next week, then gets copied to another team,
then ends up wired into a cron job nobody remembers writing. Most ops scripts are, in practice, load
-bearing infrastructure that never got the review a production system would get — and the gap
between "works when I ran it" and "safe for someone else to run at 3am" is exactly where scripting
automation earns its keep.

**A script that fails should fail loudly, leave the system in a known state, and tell the next
person what happened — an assumption baked in silently is a bug you haven't met yet.**

## 1. Fail loudly and stop, don't limp forward

The default in most shells is to keep going after a command fails, which turns one missing file
into a cascade of confusing downstream errors. Explicit failure handling turns "the script did
something weird" into "the script told me exactly where it stopped."

```bash
set -euo pipefail    # exit on error, unset variable, or failed pipe stage
trap 'echo "failed at line $LINENO" >&2' ERR
```

- **Exit non-zero on any real failure**, and use distinct codes for distinct failure classes if a
  caller needs to branch on them.
- **Check preconditions before acting** — required tools installed, required variables set, target
  reachable — and fail before the first side effect, not mid-way through.
- **Never swallow an error to "keep the script clean"** — a silenced failure is a false success
  report to whoever runs it next.

**Done when:** a failure anywhere in the script produces a non-zero exit code and a clear message
naming what failed, with no partial success reported as success.

## 2. Make re-running safe by default

A script that's safe to run once but not twice will eventually be run twice — by a retry, by a
confused operator, by a scheduler that fired while the last run was still cleaning up. Idempotency
is the same discipline `workflow-automation` requires of workflow steps, applied to the script
itself.

- **Check state before changing it** — "does this exist" before "create this."
- **Make partial completion resumable** — if the script dies at step 4 of 7, re-running should pick
  up cleanly, not redo steps 1–3 destructively or skip them incorrectly.
- **Avoid append-only side effects without a guard** — a script that appends a line to a config file
  on every run will eventually append it a hundred times.

**Done when:** running the script twice in a row, including after an interrupted first run,
produces the same end state as running it once.

## 3. Ship a dry-run mode before you ship the real one

The single highest-leverage feature in an ops script is a flag that shows exactly what it would do
without doing it. It catches wrong assumptions before they touch production and gives a reviewer
something concrete to check against intent.

- **`--dry-run` should exercise the real logic path**, not a separate parallel implementation that
  can drift out of sync with what actually runs.
- **Print the specific action, not a generic "would modify resource"** — the operator reviewing
  dry-run output needs to see the actual diff or command.
- **Default to dry-run for anything destructive** and require an explicit flag to go live, not the
  other way around.

**Done when:** every destructive script has a dry-run mode that reflects real execution logic, and
that mode is what a reviewer runs before approving the real one.

## 4. Log what happened, not just that something ran

A script's log is the only record of what it did once the terminal closes. "Done." tells the next
person nothing; a log that names every resource touched, every decision made, and every skip
reason lets them reconstruct the run without re-executing it.

- **Log at the start**: what the script is about to do and against what target.
- **Log every state-changing action** with enough detail to reverse it by hand if needed.
- **Send logs somewhere durable** if the script runs unattended — a local stdout that scrolls off a
  terminal is not a log, it's a rumor.

**Done when:** someone who wasn't watching the terminal can read the log afterward and know exactly
what the script changed.

## 5. Know when a script should stop being a script

A script accumulates flags, retries, and edge-case handling until it's effectively an application
without the tests, ownership, or deployment story of one. That's the point to graduate it — into a
proper CLI, a scheduled job with monitoring, or a service — rather than adding the twentieth flag.

- **Growing beyond a few hundred lines, or beyond one owner's head**, is a graduation signal.
- **Needing its own test suite** to trust changes means it needs the structure a script directory
  doesn't provide.
- **Being invoked by other automation regularly** means its failure mode now affects more than one
  person's terminal — treat it with the rigor of `workflow-automation`.

**Done when:** you can name, honestly, whether this script is still a script or should already be
something else — and if it should, that decision is written down, not deferred indefinitely.

## Report

State the script's failure behavior (exit codes, what stops it), whether it's confirmed idempotent
on a second run, and whether it has a working dry-run mode.

Name the honest gap — usually a code path that hasn't been tested against a mid-run interruption, or
a dry-run mode that's drifted from the real logic — rather than claiming the script is fully
production-safe.
