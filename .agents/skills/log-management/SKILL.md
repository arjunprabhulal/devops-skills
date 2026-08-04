---
name: log-management
description: Covers structured logging at scale — emitting JSON not prose, choosing sensible levels, sampling high-volume paths, setting retention against real cost, correlating log lines with trace IDs, and keeping secrets out of logs entirely. Use this whenever the user is adding logging to a service, debugging why logs are unsearchable or too expensive to keep, designing log levels or a sampling strategy, or asking how to connect a log line back to its request. For the trace those IDs point into use `distributed-tracing`, and for the paging layer use `alerting`.
license: MIT
---

# Log Management

A log line's only job is to be found and understood by someone who wasn't there when it was written. A free-text sentence optimized for a human reading it in a terminal fails that job the moment volume grows past what one person can scroll through — it can't be queried, filtered, or aggregated reliably. Structured logging exists to make every line a queryable record instead of a string.

At scale, logs stop being something a person tails in a terminal and become a dataset something else queries on that person's behalf — every choice below follows from designing for that querying system, not for the human glancing at a live stream.

**If a log line can't be filtered by field without a regex, it isn't structured yet.**

## 1. Emit structured fields, not formatted sentences

Every log line should be a JSON object (or equivalent structured format) with consistent field names across the codebase — `level`, `timestamp`, `service`, `message`, plus whatever request-specific fields apply. `"user 4821 failed login from 10.0.0.4"` cannot be filtered by user ID without a regex; `{"event":"login_failed","user_id":4821,"source_ip":"10.0.0.4"}` can be filtered, aggregated, and joined with other events in one query.

- **Use a shared field schema across services** — `user_id` in one service and `userId` in another silently breaks every cross-service query.
- **Name the event, don't just describe it in prose** — `event: "login_failed"` is filterable; a sentence about a failed login is not.
- **Keep the human-readable `message` field too**, but treat it as a summary, not the source of truth the query relies on.

**Done when:** every log line is machine-parseable and field names are consistent across every service that emits them.

## 2. Set levels by what a human should do when they see it

Levels are an action filter, not a mood indicator:

- **`ERROR`** — something failed and a human may need to act.
- **`WARN`** — something is degraded but self-recovering.
- **`INFO`** — a notable state change worth keeping around.
- **`DEBUG`** — detail only useful while actively investigating.

Getting this consistent matters more than getting it clever, because levels are what alerting and dashboards filter on downstream. The failure mode in both directions is common:

- **Logging expected, handled events at `ERROR`** — a retried request, a routine 404 — trains everyone to ignore that level entirely.
- **Logging genuine failures at `WARN`** means they never surface in an error-rate alert built to watch `ERROR`.
- **A level that means something different per team** defeats any cross-service alert or dashboard built on top of it.

**Done when:** `ERROR` in production logs reliably means something a human should look at, with no routine noise in that level.

## 3. Sample the high-volume paths instead of dropping them blind

Logging every request at full detail is affordable at low traffic and unaffordable at scale — the fix is not to stop logging the hot path, it's to sample it deliberately. Log 100% of errors and slow requests (the ones you'll actually need), and a statistically useful fraction of routine successful requests (1% is often enough to catch a trend).

- **Never sample errors or outliers away** — that's exactly the population you'll need during an investigation.
- **Sample the routine, successful path aggressively** — that's the volume driving cost with the least investigative value per line.
- **State the sample rate explicitly** somewhere discoverable, so nobody mistakes a 1% sample for a complete record during an investigation.

**Done when:** error and outlier logs are never sampled away, and routine-path sampling has an explicit, stated rate.

## 4. Correlate every log line to a trace and request ID

A log line without a correlation ID is an island — you can read it, but you can't connect it to the seven other services that touched the same request. Propagate a request or trace ID through every service call and include it as a field on every log line that request produces.

- **A single correlation ID field** turns "here's an error" into "here's the error, and here's everything that happened to this request everywhere else."
- **Set it at the entry point of the system** — the edge, the gateway, the first service that sees the request — so it exists before any service has a chance to skip it.
- **Log the ID even on success**, not just on error, so a slow-but-successful request is just as traceable as a failed one.

That single field collapses what used to be a cross-team log-grepping exercise into one query. See `distributed-tracing` for how it gets propagated across service boundaries in the first place.

**Done when:** you can pull every log line for one request across every service it touched using a single ID.

## 5. Price retention by how long the question stays worth asking

Keeping every log line at full fidelity forever is rarely worth the cost, and the right retention period differs by use: debug-level detail is often worthless after a day, INFO-level business events might matter for months for audit purposes, and error logs sit somewhere in between. Tiering storage keeps cost proportional to how often data at that age actually gets queried.

- **Hot and searchable for a short recent window** — the window where most real investigations actually happen.
- **Cold and cheap for compliance-driven longer retention** — rarely queried, but sometimes legally required to exist.
- **Revisit retention as a deliberate cost decision**, not a default nobody's touched since the system launched.

**Done when:** retention period and storage tier are set per log level or log type, not uniformly by default.

## 6. Keep secrets and PII out of logs by construction, not by review

Logs get copied, exported, and retained longer than almost anything else in the system, which makes them one of the highest-leverage places a secret or a customer's personal data can leak. Relying on someone remembering not to log a password or an API key does not scale.

- **Strip or mask known-sensitive fields at the logging library level** — auth headers, tokens, full card numbers — so it's structurally impossible to log them, not just discouraged.
- **Treat a new sensitive field type as a library change**, not a per-call-site reminder that will eventually be forgotten.
- **Audit existing logs periodically** for patterns that shouldn't be there, since the masking rule is only as good as its coverage.

See `secrets-management` for handling the credentials themselves upstream of this problem.

**Done when:** a grep for known secret patterns across recent logs returns nothing, and the logging layer — not code review — is what prevents it.

## Report

State the logging format in use, current retention per tier, whether correlation IDs are propagated end to end, and the sampling rate on high-volume paths.

Name the honest gap — usually a service still emitting unstructured text, a secret pattern that slipped through, or a retention tier that's still "keep everything" by default — rather than describing logging as fully standardized.
