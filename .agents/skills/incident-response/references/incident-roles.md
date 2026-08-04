# Incident Roles, Severity, and Communication Templates

This is the reference to open when you're three minutes into an incident and need to know exactly who does what, how bad this is, and what to type. Skim the headers, copy the templates, come back for detail later.

## Contents

- The core roles
- Severity matrix
- Status update cadence
- Escalation triggers
- Declaring and standing down
- Handoff template for long incidents

## The core roles

Every incident above the lowest severity needs at minimum an IC. Above SEV3, add comms. Above SEV2, add a scribe. One person can hold multiple roles on a small incident, but say out loud which hats you're wearing — "I'm IC and ops for now" — so no one assumes coverage that isn't there.

### Incident Commander (IC)

**Does:** owns the decision of what happens next; holds the shared model of current state — what's broken, tried, and in flight; assigns and reassigns roles; sets and revises severity; decides when to escalate and stand down; protects responders by moving side debates to threads and blocking uncoordinated changes.

**Does not:** run commands or SSH into anything — the moment an IC starts typing kubectl, no one is holding the whole board. Does not draft updates word for word — comms drafts, IC approves. Does not need to be the most senior engineer or the best system expert; page the expert as ops, not as IC.

### Communications Lead (Comms)

**Does:** drafts and posts status updates on the fixed cadence; is the single point of contact for stakeholders asking "what's going on," so the IC and ops aren't fielding the same question five times; keeps the status page and channel in sync; flags to the IC when a draft claims something not yet confirmed.

**Does not:** decide what an update says technically — pulls facts from IC and ops, doesn't invent or soften them. Does not get pulled into debugging — if comms is reading stack traces, no one is managing the stakeholders.

### Operations Lead (Ops)

**Does:** does the hands-on-keyboard work — runs the rollback, flips the flag, fails over the region, pages the specialist who can; reports findings back to the IC in the main channel; executes the IC's call even when they'd have picked differently, surfacing disagreement fast rather than silently freelancing.

**Does not:** unilaterally decide the incident is resolved or change severity — that's the IC's call, informed by ops. Does not go dark — "still trying the rollback, ETA 5 min" beats a silent stretch every time.

### Scribe

**Does:** keeps a running timeline — timestamped actions, decisions, who did what and when; captures the exact moment mitigation lands and impact starts/stops, since these numbers become the postmortem's backbone; frees the IC from remembering details while also making calls.

**Does not:** editorialize or draw conclusions in the timeline — facts and timestamps, analysis comes later. Not required below SEV2, but on a long-running SEV3 add one anyway — nobody reconstructs a four-hour incident from memory correctly.

## Severity matrix

Set severity in the first five minutes on the facts you have, and revise it as facts change — severity reflects current customer impact, not what it might become.

| Severity | Definition | Response expectation | Who to page |
|---|---|---|---|
| SEV1 | Widespread outage, majority of customers affected, or any data loss/integrity risk | IC and ops paged immediately, updates every 15-30 min, exec visibility | On-call IC, on-call ops, eng leadership, comms lead |
| SEV2 | Significant degradation for a subset of users or a single major feature down | IC paged immediately, updates hourly, dedicated incident channel | On-call IC, on-call ops for the affected system, comms if customer-visible |
| SEV3 | Minor customer impact, or internal-only (tool down, elevated errors with no confirmed harm) | Owning team engages during business hours unless worsening, updates at milestones | On-call for the affected service; IC optional if it drags on |
| SEV4 | No current customer impact — a near-miss or cosmetic issue | Log it, fix it in normal workflow, no incident channel | No paging, track as a ticket |

Default to the higher severity when unsure — downgrading in five minutes with more signal is cheap; recovering from an under-resourced SEV1 wrongly called a SEV3 is not.

## Status update cadence

The cadence above is the ceiling, not a target to wait for. If something material changes — mitigation lands, severity changes, a new team joins — post immediately, then resume the cadence. Post "still investigating, next update in N minutes" even with nothing new; silence reads as nobody working the problem.

Copy-paste template:

```
[SEV1] <one-line description of customer impact>
Status: <Investigating | Mitigating | Monitoring | Resolved>
Impact: <who/what is affected, and how badly, in customer terms>
Current action: <what's being done right now, by whom>
Next update: <clock time, not "soon">
```

Example: `[SEV2] Checkout failing for ~15% of EU customers / Status: Mitigating / Impact: EU customers on payment step 3 seeing 500s since 02:14 UTC / Current action: rolling back payments-api deploy from 01:50 UTC, ETA 10 min / Next update: 03:00 UTC`

## Escalation triggers

Escalate — more people, higher severity, or both — the moment any of these is true, don't wait for the next scheduled update:

- The current mitigation fails or makes things worse.
- Impact is spreading to more users, regions, or systems than the initial read.
- You're past 30 minutes on a SEV1/SEV2 with no viable mitigation identified.
- The fix needs access, expertise, or authority nobody in the incident currently has.
- Customer data may have been exposed, lost, or corrupted — escalate to security and leadership regardless of current severity.
- The on-call IC or ops doesn't ack within the page's expected window — go to the secondary immediately, don't wait and retry.

## Declaring and standing down

**Declare** as soon as you'd hesitate to say "this is fine" out loud to a customer — opening a channel and downgrading five minutes later costs nothing; formalizing a response after twenty minutes of ad hoc DMs costs real time.

**Stand down** only when: impact has stopped, confirmed by the metric that showed the problem, not by the fix having merely deployed; that metric has held through one full natural cycle (a traffic peak, a batch run, whatever period would re-surface it); the timeline is captured well enough to reconstruct later; and a postmortem is on the calendar for SEV2+ (see `root-cause-analysis`).

Standing down is not the same as fully understood — closing an incident as "mitigated, root cause not yet confirmed" is fine, and often correct.

## Handoff template for long incidents

Use this whenever an incident crosses a shift boundary, runs past a couple hours, or a responder swaps out. A fresh responder without this context re-derives everything the outgoing one already knows — slower and error-prone at 3am.

```
HANDOFF — <incident name/id> — <time, UTC>

Outgoing IC: <name>       Incoming IC: <name>
Severity: <current, and whether it's trending up/down>

What's broken: <one or two sentences, current understood impact>
What we've tried: <mitigations attempted, which worked, which didn't>
What's in flight right now: <any action currently running, who owns it, ETA>
What's next if current action fails: <the fallback plan, if one exists>
Where to look: <dashboards, logs, the channel/doc with the timeline>
Open questions: <anything unresolved the incoming IC should know is still a mystery>
```

Say the handoff out loud in the incident channel, not just in a doc — "I'm handing IC to <name>, they have full context" — so nobody keeps addressing questions to the person who just left.
