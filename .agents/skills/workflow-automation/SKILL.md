---
name: workflow-automation
description: Covers automating multi-step operational workflows — event-driven triggers, orchestrating steps across systems, making every step idempotent and safely retryable, and keeping a human in the loop where judgment or blast radius demands it. Use this whenever the user wires up automation that reacts to an event, chains several operational steps together, decides whether an action can run unattended, or asks why a retried workflow left things in a bad state. For time-triggered work use `scheduled-jobs`, and for the scripts implementing individual steps use `scripting-automation`.
license: MIT
---

# Workflow Automation

An operational workflow is rarely one action — it's a chain: detect a condition, decide, act,
verify, notify. Most automation failures happen not because a single step was wrong, but because
the chain assumed the happy path and had no plan for a step failing halfway through, running
twice, or firing on a burst of duplicate events.

Treat a workflow as a state machine you can inspect mid-flight, not a script that either finishes
or silently dies. **The workflow's job is to reach a known-good end state, not to execute a fixed
sequence of commands.**

## 1. Trigger on events, not on polling when you can help it

Polling wastes cycles and adds latency proportional to the poll interval; it also invites a race
where two pollers both see the same unhandled condition. An event-driven trigger — a webhook, a
queue message, a Kubernetes watch — reacts immediately and, if built on an at-least-once delivery
system, gives you an explicit signal to deduplicate against instead of an implicit one you have to
infer from timing.

- **Prefer push over pull** — a webhook or queue beats a cron job polling an API for changes.
- **Carry a unique event ID** through the whole chain so downstream steps can deduplicate.
- **Treat "at least once" delivery as the default assumption**, not an edge case to handle later.

**Done when:** the workflow's trigger is the event itself, not a poll loop guessing at freshness.

## 2. Make every step idempotent before you make it automatic

An automated step will eventually run twice — a retried webhook, a redelivered queue message, an
operator re-running by hand after an ambiguous failure. If "create the resource" isn't safe to run
twice, the second run either errors confusingly or creates a duplicate. Idempotency turns retries
from a hazard into a free safety net.

- **Key every action on a stable identifier** (an ID, a desired-state hash) so re-running converges
  instead of duplicating.
- **Check current state before acting** — "ensure X exists" instead of "create X."
- **Make the check and the act atomic** where the underlying system allows it, so two concurrent
  runs don't both pass the check and both act.

**Done when:** running any step twice in a row produces the same end state as running it once.

## 3. Give retries a limit and a backoff, and a place to stop

An unbounded retry loop on a permanently broken step just burns resources while paging no one; an
unbounded retry loop that isn't idempotent actively worsens the state with every attempt. Retries
need three things: a cap, exponential backoff so a struggling downstream system gets relief instead
of a hammering, and a terminal failure path that surfaces to a human instead of looping forever.

- **Cap retry count or duration** — after N attempts, stop and escalate.
- **Back off between attempts** — a fixed-interval retry against an overloaded dependency is a
  self-inflicted denial of service.
- **Land failed runs somewhere visible** — a dead-letter queue, a failed-runs dashboard — not a log
  line nobody reads.

**Done when:** a permanently failing step stops retrying on its own and produces a visible,
actionable failure instead of a silent infinite loop.

## 4. Decide up front which steps a human must approve

Not every action belongs fully automated. The dividing line isn't "how often does this run," it's
blast radius and reversibility — an action that's hard to undo or affects many users at once
deserves a human checkpoint even if the automation to skip that checkpoint is easy to build.

- **Auto-run** what's cheap, reversible, and well-tested — restarting a crashed pod, rotating a log.
- **Require approval** for what's expensive to undo — deleting data, a production-wide config
  change, anything touching customer-visible state at scale.
- **Make the approval step part of the workflow**, not a side-channel Slack message the automation
  doesn't wait for.

See `incident-response` for how this same human-in-the-loop judgment applies under time pressure,
and `runbooks` for documenting the manual fallback when automation isn't trusted yet.

**Done when:** every workflow step is explicitly classified as auto-run or approval-required, and
that classification is enforced by the workflow engine, not by convention.

## 5. Instrument the workflow, not just its steps

A workflow that logs each step's success but never records the whole chain's state leaves an
operator reconstructing "where did this run get to" from scattered logs during an incident. Treat
the workflow instance itself as a first-class object with a status.

- **Emit a start and end event for the whole workflow run**, correlated by the event ID from step 1.
- **Expose current state** — which step it's on, how many attempts, what it's waiting for — somewhere
  queryable, not just in logs.
- **Alert on workflows stuck mid-chain** the same way you'd alert on a failed one; a workflow that
  never finishes is often worse than one that fails fast.

**Done when:** an operator can answer "what is this workflow doing right now" without reading logs
line by line.

## Report

State which trigger type the workflow uses, whether every step is confirmed idempotent, the retry
limit and backoff, and which steps require human approval.

Name the honest gap — usually a step that's "probably idempotent" but untested against a double-run,
or a human-approval gate that exists in documentation but isn't enforced by the engine — rather than
claiming the workflow is fully safe to retry blindly.
