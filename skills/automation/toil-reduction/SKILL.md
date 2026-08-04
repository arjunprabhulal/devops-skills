---
name: toil-reduction
description: Covers finding and eliminating operational toil — measuring it honestly instead of by gut feel, automating the manual and repetitive, protecting a real automation budget against feature pressure, and telling toil apart from valuable work that just looks repetitive. Use this whenever the user asks what to automate next, complains on-call is all manual tickets, wants to justify time spent on tooling over features, or is deciding whether a recurring task is worth eliminating. For the automation that replaces toil once found use `workflow-automation` or `scripting-automation`.
license: MIT
---

# Toil Reduction

Toil is work that's manual, repetitive, automatable, tactical, and scales linearly with growth —
and it's dangerous precisely because each instance feels small. Nobody schedules a project called
"toil"; it accumulates one "just do it by hand this once" at a time until an engineer's week is
gone before they've built anything.

The fix isn't a blanket instinct to automate everything — some repeated work is judgment, not
toil, and automating it badly just moves the risk somewhere less visible. **Toil reduction starts
with measuring honestly what's actually eating time, not with automating whatever's most annoying
today.**

## 1. Measure toil before you fight it

Teams that "know" what's eating their time are usually wrong about the proportion, if not the
source — the loud, annoying task isn't always the biggest time sink; the quiet one done fifty times
a week often is. Without a number, every automation decision is a guess dressed up as priority.

- **Track time spent per recurring task category**, even roughly, for a few weeks before deciding
  what to fix first.
- **Count frequency, not just duration** — a five-minute task done twenty times a day outweighs an
  hour-long task done monthly.
- **Re-measure after automating** — confirm the toil actually dropped instead of assuming the fix
  worked because it shipped.

**Done when:** you can name the top three toil sources by measured time, not by whoever complained
most recently.

## 2. Automate the repetitive, not the judgment

Not every recurring task is toil. A task that requires a human to weigh context, make a call, or
handle a genuinely novel situation each time is engineering work that happens to repeat, and
forcing it into automation either fails on the first edge case or quietly removes judgment that
was load-bearing.

- **Toil**: the steps are the same every time, and a checklist or script fully covers it.
- **Not toil**: the steps depend on context that changes the right answer each time.
- **When unsure, automate the mechanical parts and leave the decision to a human** — a script that
  gathers the evidence for a judgment call still eliminates real toil without removing the call.

**Done when:** every task on the toil-reduction list has been checked against "does this require
judgment," and judgment-heavy tasks have been removed from the list, not automated away.

## 3. Protect an actual automation budget

Toil reduction competes directly with feature work for the same engineers' time, and feature work
almost always has a louder, more immediate advocate. Without an explicit, protected allocation —
a percentage of sprint capacity, a standing rotation, whatever fits the team — toil reduction loses
every time it's not urgent, which is most of the time, right up until it is.

- **Name a fixed share of capacity for toil reduction** and defend it in planning the same way
  you'd defend a security fix.
- **Track toil-reduction work with the same visibility as features** — if it's invisible in
  planning, it's the first thing cut under deadline pressure.
- **Cap toil at a threshold** (a commonly cited target is under half of operational time) and treat
  crossing it as a planning failure, not a fact of life.

**Done when:** toil-reduction work has a protected, tracked allocation that survives a busy sprint
instead of being the first thing dropped.

## 4. Fix the source before automating the symptom

Automating a manual workaround around a bad system locks the workaround in permanently — now it's
fast and invisible instead of slow and annoying, which makes the underlying problem harder to
justify fixing later. Before automating a recurring task, ask whether the task should exist at all.

- **Ask "why does this happen" before "how do I automate it"** — a recurring manual restart might
  mean a bug worth fixing, not a script worth writing.
- **Prefer eliminating the trigger** over automating the response, where the trigger is itself the
  problem.
- **When elimination isn't possible**, automate — but flag the underlying cause so it doesn't get
  forgotten once the symptom stops hurting.

**Done when:** for each toil source, someone has explicitly decided "eliminate the cause" or
"automate the response" — not defaulted to automation because it was easier to start.

## 5. Give self-service the credit it deserves

A large share of toil is other teams needing something from your team repeatedly — access, an
environment, a config change. Turning that into a self-service path eliminates the toil at its
root instead of automating your side of a request that shouldn't need a human on either end.

- **Any recurring "can you do X for me" request** is a self-service candidate before it's a
  scripting candidate.
- **A golden path that lets requesters serve themselves** removes the toil entirely, not just the
  manual-execution part of it.

See `internal-developer-platform` and `golden-paths` for building that self-service path once
you've identified the recurring request.

**Done when:** every recurring cross-team request has been evaluated for self-service, not just
routed to a faster internal script.

## Report

State the top measured toil sources, the protected automation-budget allocation, and what's been
eliminated versus automated versus left as judgment work.

Name the honest gap — usually a toil source everyone agrees is real but hasn't been measured, or an
automation budget that exists on paper but got consumed by the last deadline — rather than claiming
toil is under control.
