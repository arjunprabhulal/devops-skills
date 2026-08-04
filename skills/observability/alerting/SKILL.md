---
name: alerting
description: Covers designing alerts that page a human only when a human needs to act — symptom-based alerting over cause-based, multi-window burn-rate alerts on error budgets, severity tiers that route between page/ticket/dashboard, requiring every page to link a runbook, and tuning out alert fatigue. Use this whenever the user is writing a new alert rule, asking why on-call is paged too often or missing real incidents, choosing an alert threshold, or designing severity routing. For the SLO the burn-rate math comes from use `slo-definition`, and for what a runbook should contain use `runbooks`.
license: MIT
---

# Alerting

Every alert that fires and requires no action trains the person who gets paged to trust alerts a little less. That erosion compounds — a team that's been paged for three false alarms this month will be slower, not faster, to react to the fourth page, even if it's real. The job of an alerting system isn't maximizing coverage, it's maximizing the fraction of pages that were worth waking up for.

Coverage and trust trade off against each other more often than teams admit — an alert added "just in case" is rarely free, because it competes for attention with every alert that already exists.

**An alert that doesn't require a human to do something right now shouldn't page a human right now.**

## 1. Alert on symptoms, not on causes

A symptom is something the user is experiencing — elevated error rate, high latency, failed checkouts. A cause is an internal condition that might explain a symptom — a pod restarted, disk is at 82%, one replica is unhealthy behind a load balancer with four others. Alerting on causes pages people for things that often don't matter (a disk at 82% with an autoscaler about to add capacity) and misses things that do (five separate low-severity causes combining into a real user-facing outage).

- **Symptoms page** — error rate, latency, failed checkouts, budget burn.
- **Causes inform the response**, surfaced on a dashboard the paged engineer opens after the page, not baked into the page itself.
- **A cause-based alert that's "usually fine"** trains people to ignore it — which is exactly the erosion this skill exists to prevent.

Alert on the symptom; use the causes as the first thing you check once paged.

**Done when:** every paging alert is defined in terms a user of the system would recognize, not in terms of infrastructure state.

## 2. Page on error-budget burn rate, not on a flat threshold

A flat threshold ("error rate > 1% for 5 minutes") either fires on noise at low traffic or takes too long to catch a severe, fast burn at high traffic. Multi-window burn-rate alerting fixes this by asking "at this rate, how much of the error budget would this consume, and how fast" — a short window catches a severe, fast burn quickly, and a longer window with a lower threshold catches a slow, sustained burn that a short window would miss entirely:

```yaml
# fast burn: consuming budget 14x normal rate — page now
- alert: ErrorBudgetBurnFast
  expr: budget_burn_rate_1h > 14 and budget_burn_rate_5m > 14
  labels: {severity: page}
# slow burn: consuming budget 3x normal rate sustained — ticket, not page
- alert: ErrorBudgetBurnSlow
  expr: budget_burn_rate_6h > 3 and budget_burn_rate_1h > 3
  labels: {severity: ticket}
```

This is the sharpest form of symptom-based alerting because it's directly tied to the number that actually matters to users and to the release-velocity decision.

See `slo-definition` for where the underlying budget comes from.

**Done when:** every service with an SLO pages on budget burn rate, not on a hand-picked latency or error threshold.

## 3. Route by required response time, not by how bad it sounds

Not every real problem needs a human awake at 3am. A severity tier system should route strictly by "how fast does this need a human," independent of how severe the underlying cause is:

- **Page** — needs action within minutes and can't wait for business hours.
- **Ticket** — real, but can wait for the next work day.
- **Dashboard-only** — worth seeing, not worth interrupting anyone for.

Collapsing these into one undifferentiated alert stream is how paging alerts get ignored — the loud, unimportant ones drown out the rare, critical ones.

**Done when:** every alert has an explicit severity tier chosen by required response time, and page-tier alerts are a small minority of the total.

## 4. Never ship an alert without a runbook link

An alert that fires with no documented next step forces the paged engineer to reconstruct the investigation from scratch, at 3am, under pressure — the worst possible conditions to be doing first-principles debugging.

- **What the alert means** — in plain language, not just the expression that triggered it.
- **The first three things to check** — the fastest path to confirming or ruling out the usual causes.
- **How to mitigate even without knowing the root cause** — buy time first, diagnose fully later.

See `runbooks` for what that document should actually contain.

**Done when:** every page-tier alert links a runbook, and the runbook it links to actually exists and is current.

## 5. Prune alerts on a schedule, not just after a bad on-call week

Alert fatigue doesn't arrive as one obviously bad alert — it accumulates as many individually-defensible alerts that together exceed what a human can meaningfully respond to.

- **Review page volume per alert regularly**, not just after a bad on-call week prompts a one-off complaint.
- **An alert that fires often with no action taken** is a candidate for demotion to ticket-tier or deletion, not a sign on-call needs to toughen up.
- **Treat every alert as owned and reviewed**, not as a rule that, once merged, runs forever unquestioned.

**Done when:** every page-tier alert has fired at least once with a real action taken in the last review period, or it's been demoted.

## Report

State the current page-tier alert count, what fraction are burn-rate based versus flat-threshold, and whether every page-tier alert links a working runbook.

Name the honest gap — usually a handful of cause-based alerts still in the page tier, or a runbook link that points at something stale — rather than reporting the alerting setup as fully symptom-based and fatigue-free.
