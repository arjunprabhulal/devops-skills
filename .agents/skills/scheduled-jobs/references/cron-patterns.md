# Cron patterns

Cron's syntax is small enough to misremember confidently, and its failure modes (a job firing at 2am on a day 2am doesn't exist, two instances racing because nothing enforced exclusivity) stay invisible until the specific day they happen. This reference covers the five-field syntax, timezone/DST traps, idempotency via upsert-by-key, overlap prevention with a TTL lock, dead-man's-switch monitoring, Kubernetes CronJob settings, and safe retry/backoff.

## Contents

- The five fields
- Timezone and DST pitfalls
- Idempotency via upsert-by-key
- Overlap prevention with a TTL lock
- Missed-run detection: dead man's switch
- Kubernetes CronJob specifics
- Safe retry and backoff

## The five fields

```
 minute   hour   day-of-month   month   day-of-week
   *        *         *           *          *
  0-59    0-23       1-31        1-12      0-6 (0 = Sunday, 7 also accepted)
```

`*` means "every value." A comma list (`1,15`), a range (`1-5`), and a step (`*/15`) combine freely: `*/15 9-17 * * 1-5` is "every 15 minutes, 9am-5pm, Monday-Friday." When both day-of-month and day-of-week are restricted (neither is `*`), most implementations OR them together, not AND — `0 0 15 * 1` fires on the 15th of every month AND every Monday, not "the 15th, but only if it's a Monday."

| Schedule | Expression | Meaning |
|---|---|---|
| Every 5 minutes | `*/5 * * * *` | polling, light health checks |
| Hourly, on the hour | `0 * * * *` | rollups, cache refresh |
| Nightly at 2am | `0 2 * * *` | batch jobs, off-peak processing |
| Weekdays at 9am | `0 9 * * 1-5` | business-hours reports |
| Weekly, Sunday midnight | `0 0 * * 0` | weekly aggregates, cleanup |
| Monthly, 1st at midnight | `0 0 1 * *` | billing runs, monthly reports |

## Timezone and DST pitfalls

A schedule expressed in local time silently shifts by an hour twice a year, and nothing errors when it does — the job just runs at the wrong wall-clock moment relative to whatever it's supporting.

- **Schedule in UTC unless the job's timing genuinely has to track local business hours.** UTC has no DST, so a UTC schedule fires at the same real-world moment every day of the year — this removes the entire bug class for anything that doesn't need to align with "9am for people in this office."
- **The 2am-doesn't-exist problem (spring forward).** Clocks jump from 1:59am to 3:00am, so a job scheduled for `0 2 * * *` in local time never has a 2:00am to fire at. Depending on the scheduler it either skips that day silently or fires immediately at 3:00am — behavior differs across implementations and is rarely documented clearly.
- **The 2am-happens-twice problem (fall back).** Clocks fall from 1:59am back to 1:00am, so local time between 1am and 2am occurs twice. A naive scheduler can fire twice in one night — exactly the case idempotency (below) has to cover even when overlap prevention works correctly, since these are two genuinely separate fires, not a race.
- **When local time does matter** ("the report is due at 9am for people in New York"), use a scheduler that's explicitly DST-aware — Kubernetes CronJob's `.spec.timeZone`, or a real IANA tz name (`America/New_York`) — never a fixed offset like `UTC-5`, which drifts by an hour the moment DST flips and stays wrong for months. Test both transition dates explicitly rather than inferring safety from today's behavior.

## Idempotency via upsert-by-key

A double-run — from an overlap, a retry, or a DST fall-back duplicate — should never produce duplicate or corrupted output. The mechanism is keying every write on the scheduled slot, not on `now()`, and writing with an upsert instead of an insert.

```sql
-- Keyed on the scheduled day, not on when the job happened to run -- a second
-- run for the same day updates the row instead of creating a duplicate
INSERT INTO daily_summary (day, total)
VALUES ('2026-08-03', 4210)
ON CONFLICT (day) DO UPDATE SET total = EXCLUDED.total, updated_at = now();
```

- **Derive the key from the scheduled slot, not the wall-clock time the job happens to execute at** — a job that runs late and computes "yesterday" from `now()` produces the wrong day's data even on a single, non-duplicate run.
- **`ON CONFLICT ... DO UPDATE`, `MERGE`, and a `PUT` to a fixed object key are the same pattern** — the second write overwrites the first cleanly instead of appending beside it, whether the effect is a database row, a file, or a dedup-checked email/webhook call keyed on the same scheduled-slot ID.

## Overlap prevention with a TTL lock

A job whose runtime occasionally exceeds its interval will eventually have two instances alive at once unless something explicitly stops it. Acquire a lock before starting, release it on exit, and let the TTL expire the lock if the process dies without releasing.

```sql
-- Lock-row pattern with an explicit TTL, portable to any database that supports
-- a simple UPSERT (pg_try_advisory_lock is simpler where available -- it
-- releases automatically on disconnect, so there's no TTL to size at all)
INSERT INTO job_locks (job_name, locked_until)
VALUES ('nightly-rollup', now() + interval '30 minutes')
ON CONFLICT (job_name) DO UPDATE
  SET locked_until = EXCLUDED.locked_until
  WHERE job_locks.locked_until < now()
RETURNING job_name;
-- proceed only if a row came back; an unexpired lock blocks the UPDATE
```

- **Set the TTL longer than the worst observed run time, not the typical one** — a TTL close to the median lets a single slow run expire mid-execution, and a second instance starts believing it holds the lock alone. Prefer a lock that releases itself on process death over one only a graceful `finally` releases — a killed process or an OOM leaves a `finally`-only lock held until the TTL expires.
- **A blocked-by-lock event is not a failure and should not page** — log and count it. A pattern of frequent skips is a signal the job's interval no longer matches its actual runtime.

## Missed-run detection: dead man's switch

Monitoring "did the job fail" catches nothing when the job never ran at all — a paused CronJob, a disabled cron entry, or a scheduler outage produces zero failed runs and, under a failure-only setup, zero alerts. A dead man's switch flips that: the job proves it's alive, and silence itself is the alert condition.

```yaml
# The job pushes a heartbeat timestamp on every successful completion. This
# alert is independent of the scheduler -- it fires even if the scheduler
# itself stopped triggering anything.
- alert: NightlyRollupMissed
  expr: time() - job_last_success_timestamp{job="nightly-rollup"} > 26 * 3600
  labels: {severity: page}
  annotations:
    summary: "nightly-rollup has not reported success in over 26h (expected: daily)"
```

- **The window is wider than the interval, not equal to it** — a daily job checked with a 24h-exact window pages on ordinary jitter; a 26h window absorbs normal variance while still catching a genuinely missed day.
- **The heartbeat has to come from an external system**, not from the scheduler counting its own fires — if the scheduler is what's broken, a self-reported "I fired the job" is exactly the signal that goes silent along with everything else. Alert on absence as its own class, separate from failure — "hasn't run" and "ran and failed" point at different causes and shouldn't collapse into one generic page.

## Kubernetes CronJob specifics

A Kubernetes CronJob adds its own overlap and missed-run knobs on top of the base cron syntax, and the defaults are not the safe choice for most jobs.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: {name: nightly-rollup}
spec:
  schedule: "0 2 * * *"
  timeZone: "Etc/UTC"          # explicit; don't rely on the controller's local TZ
  concurrencyPolicy: Forbid    # skip a new run if the previous one is still active
  startingDeadlineSeconds: 300 # a fire more than 5m late is abandoned, not queued
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
  jobTemplate:
    spec: {backoffLimit: 2, template: {spec: {restartPolicy: OnFailure}}}
```

- **`concurrencyPolicy: Forbid`** is the Kubernetes-native version of the TTL lock above — the controller itself refuses to start a new Job if the previous one's Job object is still active. `Allow` (the default) permits overlap; `Replace` kills the running one and starts fresh, its own kind of dangerous mid-write. Forbid is the right default for almost every scheduled job.
- **`startingDeadlineSeconds`** bounds how late a missed fire is allowed to start, so a controller that was down for an hour doesn't try to catch up on every missed slot the moment it returns.
- **`successfulJobsHistoryLimit` / `failedJobsHistoryLimit`** control how many completed Job objects Kubernetes keeps around. Leaving these unset keeps every historical Job forever, which quietly accumulates until it shows up as etcd or API-server pressure — set them explicitly.
- **A paused CronJob (`spec.suspend: true`) produces no Job objects and no failed runs** — precisely the silent-stop case the dead man's switch above exists to catch; `kubectl get cronjob` alone isn't sufficient without the heartbeat.

## Safe retry and backoff

A scheduled job's own retry needs to compose with the scheduler's next fire, or the two can stack retries on top of a normal next run and turn one failure into several concurrent attempts.

- **Bound retries with `backoffLimit` (Kubernetes) or an equivalent cap in whatever runs the job** — an unbounded retry loop against a dependency that's actually down just adds load to a failing system instead of surfacing the failure.
- **Use exponential backoff between retries, not a fixed short interval** — a fixed 10-second retry against a database that's failing over hammers it 6 times a minute for however long the failover takes; exponential backoff gives the dependency room to recover.
- **Let the lock (above) prevent a retry from colliding with the next scheduled fire.** If a retry is still running when the next scheduled invocation starts, the same TTL lock that stops two scheduled fires from overlapping stops a retry and a fresh fire from overlapping too, as long as every entry path acquires it. Cap total retry time under the interval to the next scheduled fire, or the two collapse into the overlap case above.
