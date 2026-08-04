---
name: on-call-management
description: Designs a sustainable on-call system — fair rotations, clear escalation paths, clean handoffs, and a humane alert load — and treats on-call health itself as a reliability metric rather than an unmeasured cost absorbed by whoever holds the pager. Use this whenever the user is setting up or fixing an on-call rotation, mentions alert fatigue or burnout, is designing escalation policies, or asks how pages should route. For handling a page once it fires use `incident-response`; for reducing pages by fixing their cause use `alerting` and `toil-reduction`.
license: MIT
---

# On-Call Management

On-call is usually designed around the system's needs — coverage, escalation, response time —
and rarely around the human needs of the person holding the pager. That asymmetry is why
on-call burns people out: the system gets 24/7 coverage and the human gets disrupted sleep,
anxiety about the phone, and no formal accounting for any of it. A sustainable on-call program
treats the person's wellbeing as a first-class design constraint, not a cost the rotation
silently absorbs.

The signal that on-call is broken is rarely a missed SLA — it's an engineer quietly dreading
their week, or the best people avoiding teams with bad rotations. That signal shows up as
attrition and burnout long before it shows up in an incident report.

**Treat on-call health as a reliability metric, not a personal cost the rotation absorbs
silently.**

## 1. Design the rotation for fairness before convenience

An on-call schedule that consistently lands the worst weeks — holidays, launches, a
known-flaky migration window — on the same one or two people isn't an accident, it's a design
flaw that compounds into resentment and eventual attrition. Fairness has to be designed in
explicitly; it doesn't emerge from a scheduling tool's default.

- **Rotate who gets the bad weeks**, don't let seniority or convenience quietly exempt the
  same people every time.
- **Size the rotation to the actual page volume** — a rotation of three people taking pages
  nightly is understaffed regardless of what the org chart says is "enough."
- **Compensate on-call explicitly** — pay, time off in lieu, or both — an uncompensated burden
  is a burden that erodes goodwill fastest.

**Done when:** the rotation schedule and its exceptions are visible to the whole team and
match a stated fairness policy, not informal habit.

## 2. Make escalation paths explicit and rehearsed

A responder who doesn't know who to escalate to, or whether escalating is "allowed," will sit
alone on a problem too long out of uncertainty, not incompetence. The escalation path —
primary, secondary, manager, adjacent team — needs to be written down, current, and normalized
as something to use early, not a last resort that signals failure.

| Level | Who | When |
|---|---|---|
| Primary | On-call engineer | First page |
| Secondary | Backup on-call | No ack within SLA, or primary needs help |
| Manager / IC pool | Team lead or on-call manager | SEV1, or primary escalates by judgment |

- **Escalating early is a sign of good judgment**, not weakness — say this explicitly and
  reinforce it when it happens.
- **Keep the escalation contact info current** — a stale phone number in a policy doc is
  discovered at the worst possible time.
- **Cross-team escalation paths need the same rigor** as within-team ones — see
  `incident-response` for the coordination once escalation lands.

**Done when:** every engineer on the rotation can state the escalation path from memory, and
it's been used or drilled recently enough to trust.

## 3. Keep handoffs deliberate, not a silent shift-change

An on-call handoff without a real conversation loses context — ongoing issues, recent changes,
things to watch — and the incoming engineer starts their week blind to problems the outgoing
one already half-diagnosed. A five-minute sync at handoff time is cheap insurance against
re-discovering the same thing from scratch.

- **State open issues, recent risky changes, and anything flapping** at every handoff, written
  or spoken.
- **Don't let handoffs happen silently at a schedule boundary** with no communication — treat
  it as a real transition, not a timestamp flip.
- **Log the handoff notes somewhere durable** — the next rotation, weeks later, benefits from
  the history too.

**Done when:** every handoff includes a stated summary of open issues and recent risky
changes, not just a schedule change.

## 4. Measure and actively manage alert load

The number of pages per on-call shift is a direct proxy for both system health and human cost,
and it should be tracked the same way error rate or latency is tracked. A rotation that pages
ten times a night isn't sustainable regardless of how good the responders are — the fix is
almost never "toughen up the rotation," it's fixing what's paging.

- **Track pages per shift over time** — a rising trend is a leading indicator of both system
  decay and human burnout, treat it with the same urgency as an SLO breach.
- **Every page should be actionable** — a page nobody can act on at 3am is noise dressed as
  signal; route it to a ticket or business-hours channel instead, see `alerting`.
- **Set a stated threshold for "this rotation is unsustainable"** and have a real response
  when it's crossed — adding headcount, fixing root causes, or reducing scope — not just
  enduring it.

**Done when:** pages-per-shift is tracked over time and there's a stated response for when it
exceeds a defined threshold.

## 5. Treat burnout as an input, not a personal failing

By the time someone says out loud that they're burned out, the cost has usually been
accumulating for months. Build in regular, low-stakes check-ins about on-call load
specifically — not folded into a generic engagement survey — so the signal surfaces before
someone quits or the rotation quietly loses its best people to teams with better on-call.

- **Ask about on-call specifically**, separate from general job satisfaction — it's a distinct
  source of stress with its own fix.
- **Give real recovery time after a bad night or a bad incident** — a rough overnight page
  followed by a normal 9am standup is how burnout compounds.
- **Rotate people off on-call periodically**, not just off shifts — sustained months-long
  tenure on a rotation, even a good one, has diminishing returns.

**Done when:** there's a recurring, on-call-specific check-in, and at least one concrete
change has resulted from what it surfaced.

## Report

State the rotation size and fairness policy, the current pages-per-shift trend, and the
escalation path's last test date. Name explicitly where alert load is still unsustainable or
where burnout signals haven't been acted on — treating on-call health as solved because the
schedule is filled is the exact complacency that produces the next round of attrition.
