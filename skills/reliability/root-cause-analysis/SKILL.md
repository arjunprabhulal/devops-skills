---
name: root-cause-analysis
description: Turns an incident into a blameless postmortem that actually changes something — a factual timeline, multiple contributing factors instead of one scapegoat cause, and action items with real owners and dates that get tracked to completion. Use this whenever the user is writing a postmortem, doing a retro after an outage, asking "why did this really happen," or an incident has been mitigated and needs a writeup. For running the incident itself use `incident-response`, and for turning findings into a tested procedure use `runbooks`.
license: MIT
---

# Root Cause Analysis

The phrase "root cause" is misleading — most real incidents don't have one cause, they have a
chain of contributing factors that each individually looked reasonable, and only in
combination produced an outage. A postmortem that names a single root cause almost always
stops digging too early, usually at "the engineer who pushed the change" or "the alert that
didn't fire," and misses the systemic conditions that let that trigger become an outage.

The only postmortem worth writing is one that changes something. A document that accurately
describes what happened but produces no action items is a historical record, not an analysis —
write it as an artifact for future action, not a ritual for closure.

**Find the contributing factors, not a scapegoat — and change something as a result.**

## 1. Build the timeline from facts, not memory

Postmortems written days later from memory drift toward whoever tells the most coherent story,
which is rarely the most accurate one. Reconstruct the timeline from logs, metrics, deploy
history, and the incident channel transcript — actual timestamps, not "around then" — before
anyone starts interpreting what it means.

- **Pull from systems, not recollection** — deploy logs, alert history, chat transcripts, git
  blame — and cite the source for each entry.
- **Separate the timeline from the analysis** — write down what happened first, argue about
  why second; mixing them biases the facts toward whichever theory got there first.
- **Include the near-misses and what didn't happen** — an alert that should have fired and
  didn't is as much a fact as one that did.

**Done when:** the timeline is built entirely from cited sources and would be the same
regardless of who wrote it.

## 2. Run blameless, and mean it structurally

"Blameless" is not a tone, it's a structural choice: you assume every person in the timeline
made a reasonable decision given what they knew at the time, and the investigation's job is to
find out what made that decision look reasonable — a missing alert, a confusing runbook, an
untested assumption. The moment a postmortem asks "who did this," people stop giving the
honest details that make the analysis useful, and every future postmortem in that organization
gets thinner.

- **Write in passive or systemic voice for the causal chain** — "the deploy proceeded without
  the new config being validated," not "X forgot to validate the config."
- **Ask "what made this look like the right call at the time?"** for every human decision in
  the chain, not "why didn't they know better."
- **A leader publicly defending blamelessness after an uncomfortable postmortem** matters more
  than any written policy — the first time someone gets quietly punished for an honest
  postmortem, the practice dies.

**Done when:** the postmortem describes every human decision in terms of what information was
available, not in terms of individual fault.

## 3. Find contributing factors, plural, not a single root cause

Real incidents are usually a stack: a code change that introduced a bug, a test suite that
didn't cover the case, a review process that approved it anyway, an alert threshold set too
loose to catch it early, and an on-call engineer unfamiliar with the service because of a
recent reorg. Each of those is independently fixable, and fixing only the first one —
reverting the bad code — leaves the other four in place for the next incident.

- **Ask "five whys" as a technique, not a religion** — stop when you reach an organizational
  or process factor you can actually act on, not an infinite regress or an unfalsifiable "root
  cause."
- **Look across the whole stack**: code, tests, review, deploy process, monitoring, alerting,
  and response — a factor in any layer is worth naming.
- **Resist compressing the list back to one headline cause** for the sake of a tidy summary —
  the list is the value.

**Done when:** the postmortem lists multiple independent contributing factors, spanning more
than one layer of the system or process.

## 4. Write action items that are actually fixable and actually owned

An action item like "improve monitoring" with no owner and no date is a wish, not a
commitment, and it will still be open — unstarted — at the next incident review. Every action
item needs a specific owner, a specific deliverable, and a date, or it doesn't go in the
document.

```
- [ ] Add alert on queue depth > 8k (currently only alerts on consumer lag)
      Owner: @data-platform, Due: 2026-08-17
- [ ] Add integration test for partial-config deploy path
      Owner: @backend-team, Due: 2026-08-24
```

- **Prefer systemic fixes over point fixes** — a test that prevents the whole class of bug
  beats a patch for this one instance.
- **Distinguish "must do" from "nice to have"** explicitly — not everything discovered needs
  to become a tracked action item.
- **If an action item is deferred**, say why and by whom, rather than letting it silently
  vanish from the tracker.

**Done when:** every action item has a named owner, a due date, and lives in the same tracker
as regular work, not a separate postmortem graveyard.

## 5. Track action items to completion, not just to filing

The postmortem's real failure mode isn't a bad document — it's a good document whose action
items never ship because nobody revisits them. Review open action items on a recurring
cadence, separate from writing new postmortems, and treat a stale one as a finding in itself.

- **Review open items monthly** across all recent postmortems, not just at the retro meeting.
- **Re-open the incident lineage** if an unshipped action item's failure mode recurs — that's
  a direct, measurable cost of not following through.
- **Report completion rate** as an organizational health metric, the same way you'd report SLO
  attainment.

**Done when:** there's a recurring review of open postmortem action items, separate from the
postmortem meeting itself, with a visible completion rate.

## Report

State the timeline's key events with sources, the contributing factors identified across the
stack, and the action items with owners and dates. Name explicitly which contributing factors
did not get an action item and why — a postmortem that lists five factors and acts on only
two, without saying so, quietly signals that the other three are accepted risk, which should
be a deliberate call, not an omission.
