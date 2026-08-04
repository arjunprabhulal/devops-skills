---
name: error-budgets
description: Turns an SLO into a spendable number that makes the velocity-versus-reliability tradeoff explicit — deriving the budget from the SLO, tracking how fast it's consumed, and enforcing freeze policies when it runs out, instead of arguing about "is it reliable enough" from gut feeling. Use this whenever the user mentions error budgets, asks whether they can ship given recent reliability, or wants a release-freeze policy tied to reliability. For defining the SLO the budget derives from use `slo-definition`; for the live incident burning the budget use `incident-response`.
license: MIT
---

# Error Budgets

Every organization has an implicit, unstated tradeoff between shipping fast and staying
reliable — it just usually gets negotiated informally, incident by incident, by whoever's
loudest in the room. An error budget makes that tradeoff explicit and quantitative: given your
SLO, you're allowed a specific, calculated amount of unreliability, and you get to decide how
to spend it — on risky launches, on infrastructure migrations, on just moving fast — instead
of debating each decision from scratch.

The budget only does its job if spending it has a real consequence. A budget that's tracked
but never enforced is a dashboard, not a policy — it changes nobody's behavior and reliability
erodes exactly like it would without one.

**The budget is a spendable number, not a report card — and it must have teeth.**

## 1. Derive the budget mechanically from the SLO

The error budget isn't a separate target you set — it's the direct complement of the SLO. A
99.9% availability SLO over 30 days means 43.2 minutes of allowed downtime in that window,
full stop. Don't negotiate the budget as its own number; it falls out of whatever SLO was
already agreed with the business, see `slo-definition`.

```
SLO: 99.9% availability over 30 days
Budget = (1 - 0.999) * 30 days = 43.2 minutes of allowed downtime
```

- **The budget's time window should match the SLO's window** — a monthly SLO needs a monthly
  budget, not an arbitrary rolling period picked separately.
- **One budget per SLO**, not one aggregate budget across unrelated services — a healthy
  service shouldn't fund an unhealthy one's risk-taking.
- **Recalculate whenever the SLO changes** — a budget derived from a stale SLO is measuring
  against the wrong target.

**Done when:** the error budget's number and window are mechanically derived from the current
SLO, not chosen independently.

## 2. Track burn rate, not just remaining balance

Knowing you have 20 minutes of budget left tells you less than knowing you're burning it at
ten times the sustainable rate. Burn rate — how fast the budget is being consumed relative to
the time remaining in the window — is the leading indicator that lets you react before the
budget is actually gone, which is the whole point of having one instead of just waiting for an
SLO breach.

- **Alert on burn rate, not just on SLO breach** — a fast burn early in the window predicts
  exhaustion before it happens; see `alerting` and `slo-definition` for the mechanics.
- **Distinguish a fast, short burn from a slow, sustained one** — they call for different
  responses, one urgent, one a longer-term trend to fix.
- **Make burn rate visible on a dashboard the whole team sees**, not something only surfaced
  during a postmortem — see `dashboards`.

**Done when:** burn rate is monitored continuously and alerts fire before the budget is fully
exhausted, not only after.

## 3. Spend the budget deliberately, not accidentally

A healthy budget gets spent on purpose — a riskier launch, a bigger migration, an
infrastructure change with a real chance of causing a blip — because the team decided the
tradeoff was worth it. An unhealthy budget gets spent by accident, through recurring incidents
and unaddressed toil, with nobody having actually chosen that tradeoff. The difference
matters: one is informed risk-taking, the other is drift.

- **Ask "is this worth spending budget on"** before a risky change, the same way you'd ask
  about a monetary budget.
- **Track what the budget was actually spent on** — deliberate launches versus unplanned
  incidents — to see which dominates.
- **A budget spent entirely on unplanned incidents** is a sign the reliability bar itself, or
  the engineering practices behind it, need attention — not just the next release.

**Done when:** budget spend is categorized as deliberate or incidental, and the split is
visible to the team making the tradeoff.

## 4. Enforce the freeze policy when the budget runs out

The freeze is the entire mechanism that gives the budget teeth. When the budget is exhausted,
the team's priority shifts by policy, not by debate, to restoring reliability before shipping
new risk — new feature launches pause, and the roadmap yields to reliability work. Skipping
the freeze once, for a "just this one launch" exception, teaches the org that the budget is
decorative, and every future budget conversation gets weaker.

- **Define the freeze scope in advance** — what's paused (feature launches) versus what still
  ships (bug fixes, the reliability work itself).
- **Make the freeze automatic on exhaustion**, not a discussion each time — the whole value is
  removing the debate.
- **Require an explicit, visible exception process** if leadership overrides a freeze — a
  quiet override defeats the mechanism as surely as never freezing at all.

**Done when:** there's a written freeze policy that has actually been triggered and observed
at least once, not just documented.

## 5. Review budget trends, not just individual burns

A single fast burn is an incident. A budget that's exhausted every month, or a service that
never comes close to spending its budget, are both signals about the SLO itself, not just
about individual incidents. Review the pattern over multiple windows to catch either failure
mode.

- **A service that never spends its budget** may have an SLO set too loose for what the
  business actually needs, or too tight for the risk the team should be taking — either way,
  revisit it.
- **A service that's chronically exhausted** signals a systemic reliability problem that ad
  hoc incident fixes won't solve — see `root-cause-analysis` for finding the contributing
  factors across the pattern, not just one incident.
- **Report budget health alongside SLO attainment** in the same recurring review, so the
  tradeoff stays visible to whoever owns the roadmap.

**Done when:** budget trend across multiple windows is reviewed on a recurring cadence,
separate from any single burn event.

## Report

State the current SLO, the derived budget and window, current burn rate, and remaining
balance. Name explicitly whether the freeze policy has ever actually been enforced or only
exists on paper — a budget with no teeth is indistinguishable from no budget at all, and that
gap is worth stating plainly rather than letting the dashboard imply a discipline that isn't
actually being practiced.
