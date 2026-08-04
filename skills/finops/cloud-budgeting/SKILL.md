---
name: cloud-budgeting
description: Forecasts cloud spend from trend and known upcoming changes, sets budgets and alerts that fire before an overrun becomes a surprise invoice, catches anomalies early, and turns raw spend into unit economics and showback/chargeback that leadership can act on. Use this whenever the user asks for a spend forecast, wants a budget alert or anomaly detector, is building a showback or chargeback report, or asks what a feature or customer costs to run. For cutting the spend a budget flags as too high use `cost-optimization`, and for the tags budgets are sliced by use `resource-tagging`.
license: MIT
---

# Cloud Budgeting

A budget that exists only as a number in a spreadsheet, checked once a month, catches an overrun
after the money is already spent. The point of budgeting isn't the forecast itself — it's the
early-warning system that lets someone act while there's still spend left to prevent, not just
spend left to explain after the fact.

Budgeting also has to answer a harder question than "are we over": whether the spend is
proportionate to the value it's producing. A bill that doubles because usage doubled is healthy;
a bill that doubles while usage is flat is not — and only unit economics can tell the two apart.

**A budget's job is to give you time to act before the overrun, not a report after it.**

## 1. Forecast from trend plus known changes, not last month's total

Last month's total is a lagging number — it says nothing about a migration, a new feature launch,
or a customer onboarding that's about to change the trajectory. A forecast built from the recent
trend line, adjusted for known upcoming changes (a launch date, a planned decommission, a seasonal
pattern), is far more useful than an extrapolation of a single flat number.

- **Use a rolling trend**, not a single prior period, to smooth out one-off spikes.
- **Adjust explicitly for known changes** — don't let the model be blindsided by something already
  on the roadmap.

**Done when:** the forecast cites the trend window and the known changes it was adjusted for, not
just last month's number carried forward.

## 2. Set budgets and alerts before the money is spent, not after

An alert that fires once the monthly bill is already final tells you what happened, not what to
stop. Budget alerts tied to forecasted trajectory — "on pace to exceed budget by day 20" — give a
team the runway to intervene mid-cycle instead of just explaining the overrun after close.

```text
budget: $50,000/month
alert at 50% of budget consumed by day 10  -> informational
alert at forecasted-to-exceed by >10%      -> page the budget owner
alert at 100% of budget consumed           -> escalate, don't wait for month-end
```

**Done when:** every budget has an alert tied to forecasted trajectory, not only to the final
month-end total.

## 3. Catch anomalies with rate-of-change, not just absolute thresholds

A flat spend threshold either fires on normal week-to-week noise or misses a real problem that's
still under the ceiling — a runaway job doubling a small line item is invisible to a threshold
sized for the whole account. Detecting anomalies by rate-of-change against that resource's own
recent baseline catches a spend spike quickly regardless of its absolute size.

**Done when:** anomaly detection flags unusual rate-of-change per cost category, not only breaches
of one account-wide dollar ceiling.

## 4. Turn cost into unit economics leadership can act on

A total dollar figure tells leadership nothing about whether spend is healthy. Cost per customer,
per request, or per transaction reframes the same number as a ratio that can be judged against
revenue or usage growth — a rising total with a falling or flat unit cost is a business scaling
correctly, not a cost problem to fix.

- **Pick the unit that matches how the business is sold** — per customer for SaaS, per
  transaction for a payments platform, per build for a CI product.
- **Track the trend of the ratio**, not just its current value — a slowly rising unit cost is the
  earliest signal of a problem worth investigating before it's large.

**Done when:** at least one unit-economics metric is tracked over time and reviewed alongside raw
spend.

## 5. Show back before you charge back

Showback — reporting what each team costs without moving money — builds the trust and data
accuracy that chargeback later depends on. Skipping straight to chargeback before teams trust the
numbers turns every dispute into a fight about tag accuracy instead of a conversation about actual
spend, and stalls the whole program.

**Done when:** every team has seen and validated its own showback numbers before any chargeback
mechanism is switched on.

## 6. Review the budget against reality on a cadence

A budget set once at the start of the year and never revisited becomes disconnected from what the
business actually needs within a quarter — new services launch, old ones get decommissioned, and
growth assumptions age quickly. Reviewing budgets against actuals on a fixed cadence keeps them a
useful control instead of a stale number nobody trusts enough to alert on.

**Done when:** every budget has been reconciled against actual spend within the last review
period, with variances explained.

## Report

State the current forecast versus budget for the period, which alerts are active, and the unit
economics metric being tracked. Name the honest gap — usually a cost category not yet reconciled
into the forecast, or a team still working from showback numbers it hasn't fully validated —
rather than claiming spend is fully predictable.
