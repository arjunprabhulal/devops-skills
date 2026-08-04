---
name: dashboards
description: Covers building dashboards people actually open during an incident instead of ignoring — one question per panel, RED/USE-based layout, designing for a specific audience and decision, and avoiding the wall-of-graphs nobody reads. Use this whenever the user is building a new dashboard, asking why an existing one never gets used, deciding what panels a service needs, or reducing a sprawling dashboard down to something useful. For the metrics that fill the panels use `metrics-and-monitoring`, and for the paging layer that should point at these dashboards use `alerting`.
license: MIT
---

# Dashboards

A dashboard exists to answer a specific question fast, under pressure, for a specific person. Most dashboards fail that job not because the data is wrong but because they were built to show everything available rather than to answer anything in particular — thirty panels of "might be useful," none of which the on-call engineer can parse in the first ninety seconds of an incident.

That's a design failure, not a data failure — every one of those thirty panels might be technically correct and still add up to a dashboard nobody can act on under pressure.

Treat dashboard-building as an editing exercise, not an exporting one — the value is almost always in what you deliberately leave out.

If you can't say which question a dashboard answers and for whom, it will be built once and never opened again.

**A dashboard is a designed answer to a question, not an export of every metric a service happens to emit.**

## 1. Name the question and the audience before building a single panel

"Show me service health" is not a question, it's a mission statement. "Is this service currently causing the checkout failures customers are reporting" is a question, and it implies a very different, narrower set of panels than "show me everything about the payment service."

The narrower question is almost always the more useful dashboard, because it maps directly onto a decision someone actually needs to make. Every dashboard should be buildable to a one-sentence brief:

- **Who opens this** — on-call engineer, service owner, leadership reviewing a trend.
- **Under what circumstance** — mid-incident, weekly review, capacity planning.
- **What decision they make from it** — mitigate now, file a follow-up, adjust a forecast.

A dashboard with no stated audience or trigger condition is the one that rots first.

**Done when:** you can state, for any dashboard, who opens it, when, and what they decide from it — in one sentence.

## 2. Give every panel exactly one question, and title it as that question

A panel with five overlapping lines and two Y-axes is answering "everything at once," which means it's actually answering nothing at a glance. Split it: one panel for request rate, one for error rate, one for latency percentiles — each independently readable in the two seconds someone spends looking at it during an incident.

- **One line of reasoning per panel** — if explaining a panel takes more than one sentence, it's actually two panels.
- **Title panels as the question they answer** — "Error rate by endpoint," not "Errors" — so scanning titles alone tells you what's on the page.
- **Avoid dual Y-axes entirely** — they invite misleading visual correlation between two numbers that don't share a scale.

**Done when:** every panel can be described by its title alone, and no panel requires reading its legend to know what question it answers.

## 3. Lay out by RED and USE, top to bottom, most-actionable first

For a request-driven service, the fastest-loading, top-most row should be Rate/Errors/Duration — the three numbers that tell you *whether* something's wrong. Only below that should USE panels for underlying resources appear, because they explain *why*, and you only need why once you know something's wrong.

- **Top row: Rate, Errors, Duration** — whether something's wrong, answerable in the first glance.
- **Below that: Utilization, Saturation, Errors** for the resources this service depends on — why it's wrong, once you already know it is.
- **A wall of infrastructure gauges above the RED row** forces every viewer to scroll past what doesn't matter yet to reach what does, every time.

**Done when:** the top of every service dashboard shows Rate, Errors, and Duration before anything else.

## 4. Match time range and granularity to the decision, not the data retention

A dashboard meant for spotting an active incident should default to a short, high-resolution window — last hour, one-minute resolution — so a spike is visible as a spike, not smoothed into a flat line.

A dashboard meant for capacity or trend review should default to weeks or months at coarser resolution, because a one-hour view of a slow trend just looks like noise. Shipping every dashboard with the same default 24-hour window regardless of its purpose is a common, easy-to-fix mismatch between the tool and the question it's meant to answer.

**Done when:** each dashboard's default time range matches the kind of decision it's built to support.

## 5. Delete panels and dashboards that nobody has opened

Dashboards accumulate the same way alerts do — someone adds a panel during an investigation, it's useful once, and it never gets removed.

- **Most dashboard tools can report view counts** — use that data instead of guessing what's still useful.
- **A dashboard nobody's opened in months is not a safety net** — it's clutter that makes the ones people do use harder to find.
- **A panel nobody looks at** is one more thing slowing the page load of the ones that matter.

**Done when:** dashboard and panel inventory has been reviewed against actual view counts in the last review period, and unused ones are gone.

## 6. Point every page-tier alert at the dashboard that explains it

An alert says something is wrong; a dashboard should be one click away explaining what and how badly, without the paged engineer having to build a query from scratch under pressure.

Every page-tier alert (see `alerting`) should link the specific dashboard, or the specific panel, that shows the condition it fired on — not a link to a generic team dashboard the engineer then has to search through.

**Done when:** every page-tier alert links directly to the dashboard view that shows the condition it alerted on.

## Report

State how many dashboards exist per service, whether each has a stated audience and question, and whether page-tier alerts link directly to the relevant dashboard view.

Name the honest gap — usually a legacy dashboard nobody has pruned, or a service whose only dashboard is a generic template rather than one built around its actual RED/USE panels — rather than claiming the dashboard set is fully curated.
