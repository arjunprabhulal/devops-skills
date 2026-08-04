---
name: incident-response
description: Runs a live incident from first alert to resolution — assigning clear roles, mitigating before diagnosing, setting severity, and communicating in a structured cadence so a system under stress does not also become a communication failure. Use this whenever the user says production is down, an alert just fired, customers are affected, they need an incident commander, or they ask how to run or structure an active incident. For the after-the-fact writeup use `root-cause-analysis`, for the step-by-step fix procedures use `runbooks`, and for the on-call rotation that catches the page use `on-call-management`.
license: MIT
---

# Incident Response

An incident is not a debugging session with an audience — it is a distinct mode with its own
goals. The instinct of a good engineer is to understand the problem before acting; the
discipline of incident response is to reduce customer harm before you understand anything at
all. Those two goals conflict, and the second one wins until stated otherwise.

The single biggest failure mode in live incidents is not technical, it is organizational:
nobody is in charge, three people fix the same thing three different ways, and no one can say
what changed. Fixing that costs nothing and saves the most time.

**Mitigate first, understand second, and let one person own the decisions.**

For role definitions, a severity matrix, and copy-paste status-update templates, read
`references/incident-roles.md`.

## 1. Name an incident commander in the first five minutes

The IC does not fix anything. Their job is to hold the shared model of what is happening, make
the call on what to try next, and stop responders from working at cross purposes. Without a
named IC, every responder is independently trying to be the hero, which means duplicated
effort and nobody watching the whole board.

- **One IC per incident**, full stop — if it feels like it needs two, split into two
  incidents.
- **Ops does the hands-on-keyboard work**, comms talks to stakeholders, IC decides — do not
  let one person try to be all three on anything above the lowest severity.
- **The IC can be reassigned** mid-incident if someone more senior joins or the first IC needs
  to become hands-on; say so out loud when it happens.

**Done when:** everyone in the incident channel can name the current IC without asking.

## 2. Mitigate before you diagnose

Rolling back a bad deploy, failing over to a healthy region, or shedding load buys time and
stops the bleeding, even if you don't yet know why the system broke. Root-causing while the
customer is still down is optimizing for the wrong thing. The fix does not need to be
permanent — it needs to be now.

- **Ask "what changed?" before "why did it break?"** — most incidents trace to a recent
  deploy, config change, or scaling event, and reverting it is faster than understanding it.
- **Prefer reversible mitigations** — a rollback or a traffic shift you can undo beats a
  targeted code fix you're improvising under pressure.
- **A mitigated incident is not a closed incident** — it moves to lower urgency, not to done.

**Done when:** customer-facing impact has stopped or measurably reduced, independent of
whether the cause is understood.

## 3. Set severity and let it drive everything else

Severity determines who gets paged, how often you communicate, and whether you wake up a VP.
Getting it wrong in either direction has a cost: too high burns out responders on
non-incidents, too low leaves a real outage under-resourced. Set it early, and revise it as
facts come in — severity is a snapshot of current customer impact, not a prediction.

| Severity | Signal | Cadence |
|---|---|---|
| SEV1 | Widespread outage or data loss risk | Updates every 15–30 min, exec visibility |
| SEV2 | Degraded for a subset of users/features | Updates hourly |
| SEV3 | Minor or internal-only impact | Updates at milestones |

**Done when:** the incident has a stated severity that matches current, not worst-case,
customer impact.

## 4. Communicate on a fixed cadence, not when you feel like it

Silence during an incident is read as "nobody is working on it," even when three engineers are
heads-down. A predictable update cadence — even a boring "still investigating, next update in
30 minutes" — is what keeps stakeholders off the responders' backs and prevents the same
question being asked in five channels at once.

- **One channel of record** — status page, incident channel, whatever it is, say it once and
  point everyone there.
- **State impact, current action, and next update time** — every update, not just the first
  one.
- **Comms lead drafts, IC approves** — keep the IC out of wordsmithing under pressure.

**Done when:** a stakeholder who wasn't in the room can read the channel and know current
status without asking.

## 5. Protect the responders' attention

An incident channel that fills with speculation, side debugging, and "have you tried"
suggestions from well-meaning bystanders slows the people actually holding context. The IC's
job includes triage of *people*, not just systems.

- **Move deep-dive debugging to a thread or side channel**, keep the main channel for status
  and decisions.
- **Limit who can push changes** during the incident — uncoordinated fixes are how a SEV2
  becomes a SEV1.
- **Call a break** on long incidents — a swapped-in fresh responder catches things a
  six-hour-deep one won't.

**Done when:** the main incident channel is readable as a decision log, not a debugging
transcript.

## 6. Close the loop before closing the incident

An incident isn't over when the graph looks normal — it's over when you've confirmed the
mitigation holds and handed off what's left. Declaring victory too early is how the same page
fires again an hour later.

- **Watch the metric through at least one full cycle** (a full traffic period, a full batch
  run) before declaring resolved.
- **Capture the timeline while it's fresh** — timestamps, who did what, get lost fast once
  people move on.
- **Schedule the postmortem before people scatter** — see `root-cause-analysis`.

**Done when:** the incident is marked resolved with a confirmed-stable window and a postmortem
is on the calendar.

## Report

State the final severity, who was IC, what mitigated the impact and when, and how long
customers were affected. Name explicitly what is still not understood about root cause — an
incident report that claims full understanding under time pressure is usually wrong, and
saying "mitigated, cause not yet confirmed" is more honest and more useful than a guess
dressed up as a conclusion.
