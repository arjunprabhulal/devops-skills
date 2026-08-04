---
name: runbooks
description: Writes and maintains the procedural documents that let a tired, half-awake engineer resolve a known failure at 3am without needing the original author or deep system knowledge. Use this whenever the user is documenting an operational procedure, writing a "what to do when X fires" doc, building an alert-to-action mapping, or complaining that on-call has to reverse-engineer fixes each time an alert repeats. For the live coordination during an active incident use `incident-response`, and for the improvised procedures that emerge in one-off outages use `root-cause-analysis` to turn them into a permanent runbook.
license: MIT
---

# Runbooks

A runbook is not documentation about the system — it is a script for a specific person in a
specific bad moment: paged at 3am, half-asleep, unfamiliar with this particular service, under
pressure to fix it fast. Write for that reader, not for someone doing a leisurely deep-dive at
their desk. If the runbook requires understanding why the fix works, it has already failed its
purpose.

The test of a good runbook is whether someone who has never touched the service could follow
it and resolve the issue. If it only works for the person who wrote it, it is a note to self,
not a runbook.

**Write for a tired stranger, not for yourself.**

## 1. Trigger the runbook from the alert, not the other way around

A runbook nobody can find during an incident does not exist. Every alert that pages a human
should link directly to the runbook for that specific failure — not a wiki search, not "ask in
Slack," a direct link in the alert payload itself.

- **One runbook per alert, not per service** — a service with ten alerts needs ten short
  runbooks, not one long one the responder has to search.
- **Name the runbook after the symptom**, not the fix — "Disk usage above 90%" not "Cleanup
  script."
- **Put the link in the alert**, see `alerting` — a runbook is only as good as its
  discoverability under pressure.

**Done when:** paging on this alert lands the responder on the exact runbook within one click.

## 2. Write concrete steps, not concrete goals

"Investigate the cause of high latency" is a goal. "Run `kubectl top pods -n api` and check if
any pod exceeds 80% CPU; if so, run the scale-up command below" is a step. A tired reader
cannot turn a goal into an action under pressure — that translation is exactly the expertise
the runbook exists to replace.

```
1. Check queue depth:  curl -s internal/metrics/queue_depth
2. If depth > 10,000: run scale-consumers.sh --count +5
3. Re-check after 3 min. If still climbing, escalate to #data-platform (see step 5).
4. If depth is falling, monitor for 15 min then close.
5. Escalation: page @data-platform-oncall via PagerDuty, do not use Slack DM.
```

- **Every command is copy-pasteable**, with real flags, not placeholders like
  `<your-namespace>`.
- **State the expected output** so the reader can tell whether the step worked.
- **Number the steps** — a numbered list survives being read out loud over a phone call; prose
  doesn't.

**Done when:** a reader unfamiliar with the service could execute every step without needing
to interpret intent.

## 3. Make the decision points explicit

Every runbook has branches — "if this, then that; otherwise, escalate." Leaving the branch
implicit forces the responder to make a judgment call they are the least equipped to make at
3am. Write the branch down, including what "otherwise" means.

- **State the threshold, not a vague description** — "if error rate exceeds 2%" not "if error
  rate looks high."
- **Give an explicit escalation path for every branch**, including who to page and what
  channel to use — see `on-call-management`.
- **Cap the number of retries or attempts** before the runbook itself says "stop, escalate
  now" — a runbook that lets someone loop for an hour has a bug.

**Done when:** every decision point in the runbook states a measurable threshold and a named
next action.

## 4. Keep the blast radius of every step visible

A runbook step that restarts the wrong thing, or a rollback command with an unstated scope,
can turn a contained incident into a bigger one. State what each command affects before the
responder runs it, especially anything destructive or irreversible.

- **Label destructive steps explicitly** — "this restarts all pods in the deployment, expect
  ~30s of 5xx."
- **Prefer the smallest-blast-radius fix first**, escalate to bigger interventions only if it
  doesn't work.
- **Never bury a `DELETE` or `--force` flag mid-paragraph** — put it on its own line with a
  warning.

**Done when:** no step's side effects would surprise the person running it.

## 5. Test runbooks the same way you test code

An untested runbook is a hypothesis, not a procedure. Commands drift, tools get renamed,
permissions change, and a runbook that worked six months ago silently rots. The only way to
know it still works is to run it.

- **Run every runbook during a game day** — see `chaos-engineering` — not just read it.
- **Assign an owning team**, not an owning individual, so it survives someone leaving.
- **Set a staleness check** — a runbook not reviewed in the last quarter is a suspect runbook;
  flag it.

**Done when:** the runbook has been executed successfully by someone other than its author
within the last review cycle.

## 6. Retire runbooks as aggressively as you write them

A stale runbook is worse than no runbook — it sends a tired responder down a path that no
longer applies to the current system. When the underlying failure mode is fixed, or the
service is decommissioned, the runbook needs to go with it, not linger as a trap.

- **Delete, don't archive-and-forget** — a runbook folder full of dead procedures erodes trust
  in all of them.
- **Link runbook updates to the change that invalidates them** — if a deploy changes the
  recovery command, the runbook PR ships in the same change.

**Done when:** every runbook currently linked from an alert reflects the system as it exists
today.

## Report

State how many runbooks were written or updated, which alerts they're now linked from, and
whether they've been execution-tested or only reviewed on paper. Name explicitly which ones
are still unvalidated in practice — an untested runbook read as complete is more dangerous
than an obviously missing one, because it creates false confidence at the exact moment
confidence is needed least.
