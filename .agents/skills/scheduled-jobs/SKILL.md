---
name: scheduled-jobs
description: Covers cron and scheduled work done right — idempotency, preventing overlapping runs, monitoring for missed and failed runs, alerting on silence, and getting time zones and DST transitions correct. Use this whenever the user is writing a cron job or Kubernetes CronJob, asks why a scheduled job ran twice or didn't run at all, is debugging a job that fired wrong after a DST change, or wants to know if a nightly job silently stopped. For the logic inside the job use `scripting-automation`, and for event-driven work instead of time-driven use `workflow-automation`.
license: MIT
---

# Scheduled Jobs

A scheduled job is unattended by design — nobody watches it fire, which means nobody notices when
it stops firing, fires twice, or fires at the wrong time until the downstream effect shows up days
later as a data gap or a stale report. Every property that makes cron convenient (fire-and-forget)
is also what makes it dangerous without deliberate guardrails.

**Design a scheduled job assuming nobody is watching it run — because nobody is, until it breaks.**

For cron syntax, DST pitfalls, locking, and Kubernetes CronJob settings, read
`references/cron-patterns.md`.

## 1. Make the job idempotent, not just retry-friendly

A scheduler that fires a job that's already running, or re-fires after a timeout that wasn't
actually a hang, needs the job itself to tolerate a duplicate execution. This is the same
idempotency discipline from `scripting-automation`, but scheduled jobs need it more: nobody is
present to notice a duplicate run happened.

- **Key the job's effect on the scheduled time or a run ID**, not on "whatever the current time
  is when it happens to execute" — a job that computes "yesterday" from `now()` breaks if it runs
  late.
- **Make writes upserts, not appends** — a job that inserts a daily summary row should overwrite
  today's row if it runs twice, not create two.
- **Verify against the last successful run's output**, not just "did the command exit zero" — exit
  zero with half the work done is a false success.

**Done when:** manually re-triggering the job for a time slot that already ran produces the same
result as the original run, not a duplicate or a corruption.

## 2. Prevent overlapping runs explicitly

A job that takes longer than its interval will eventually have two instances running at once —
both writing, both reading, both assuming they're the only one. This is one of the most common
causes of scheduled-job data corruption, and it's entirely preventable with an explicit lock.

- **Use a lock with a TTL** — a file lock, a database row, a distributed lock — so a second
  scheduled fire while one is still running skips or queues instead of racing.
- **Set the TTL longer than the worst-case run time**, or the lock expires mid-run and a second
  instance starts anyway.
- **Log and alert on a skipped-due-to-overlap event** — it's not a failure, but a pattern of
  skips means the job's interval no longer fits its actual runtime.

**Done when:** two overlapping scheduled fires cannot both execute the job body at the same time,
and a skip due to overlap is visible, not silent.

## 3. Monitor for the job not running at all

The failure mode that hurts most is silence — a job that used to run nightly stops running, and
nothing alerts because there's no failed run to alert on, just an absent one. Monitoring "did the
job fail" is not the same as monitoring "did the job run."

```yaml
# dead man's switch: job must check in within its expected window, or this pages
- alert: NightlyJobMissed
  expr: time() - job_last_success_timestamp{job="nightly-rollup"} > 26 * 3600
  labels: {severity: page}
```

- **Use a dead man's switch** — the job pings a heartbeat on success, and an external check pages
  if the heartbeat goes stale, independent of the scheduler that's supposed to trigger the job.
- **Alert on absence, not just on failure** — a scheduler that itself stopped (a paused CronJob, a
  disabled cron entry) produces zero failed runs and zero alerts under a failure-only setup.
- **Set the missed-run window wider than normal jitter** but tight enough to catch a real gap
  before it compounds — see `alerting` for the tuning discipline behind that threshold.

**Done when:** every scheduled job has a heartbeat-based check that pages when the job hasn't
succeeded within its expected window, independent of the scheduler's own health.

## 4. Get time zones and DST transitions right on purpose

A job scheduled in local time silently shifts by an hour twice a year, and "silently" is the
operative word — nothing errors, the job just runs at the wrong wall-clock time relative to
whatever business process it's supporting. This is one of the few scheduling bugs that's invisible
in testing and only shows up on the transition date, months after deployment.

- **Schedule in UTC wherever the job's timing doesn't need to track local business hours** —
  removes DST as a variable entirely.
- **When local time matters** (a report due "at 9am local"), use a scheduler that's explicitly DST
  -aware rather than a fixed UTC offset that drifts by an hour twice a year.
- **Test the schedule against both DST transition dates**, not just against today's offset.

**Done when:** the job's schedule is either UTC-based or explicitly DST-aware, and both spring-
forward and fall-back transitions have been checked against the intended fire time.

## 5. Treat a scheduled job's failure path like any other production failure

A cron job failing silently into `/dev/null` is the default in a lot of legacy setups, and it means
the first sign of trouble is the downstream consumer of the job's output noticing something's
stale or missing — far later than the job's own exit code would have told you.

- **Route failures to the same alerting path as everything else** — see `alerting` for severity
  routing — not to an email nobody reads.
- **Include the run's context in the failure alert** — which scheduled slot, how far it got, what
  it was operating on — so triage doesn't start from zero.

**Done when:** a failed scheduled run pages or tickets through the same path as any other
production failure, with enough context to start triage immediately.

## Report

State the job's idempotency guarantee, the overlap-prevention mechanism, and whether a dead man's
switch monitors for missed runs independent of the scheduler.

Name the honest gap — usually a missed-run monitor that hasn't been added yet, or a schedule that's
never been checked against a DST transition — rather than claiming the job is fully unattended-safe.
