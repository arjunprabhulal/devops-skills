---
name: distributed-tracing
description: Covers following a single request across service boundaries — context propagation, span and attribute design, sampling that keeps the traces worth keeping, and using traces to find where latency actually accumulates. Use this whenever the user debugs a slow request touching multiple services, instruments a service with OpenTelemetry or similar, asks why a trace has gaps, or decides what to sample when full tracing is too expensive. For metrics that flag a latency problem use `metrics-and-monitoring`, for one service's hot path use `profiling`.
license: MIT
---

# Distributed Tracing

A metric can tell you p99 latency went up. It cannot tell you which of the eleven services a request passed through added the extra 400ms. A trace can — it's the record of one request's actual path through the system, as a tree of timed spans, and it's the only signal built specifically to answer "where did the time go" across a distributed call graph.

That answer is only available if the trace is complete. A trace with a gap doesn't just lose detail about the missing service — it loses the ability to say anything conclusive about where the time went at all, because the missing piece could be where it all happened.

Tracing only works if every hop in that graph agrees to pass the same identifier forward. **A trace is only as complete as its weakest propagation link — one service that drops the context breaks the chain for everyone downstream of it.**

## 1. Propagate context through every hop, not just the ones you own

A trace is stitched together from a shared trace ID and parent span ID passed along with the request — as an HTTP header, a gRPC metadata field, or a message queue attribute.

If any service in the path doesn't read and forward that context, the trace doesn't just lose that service's spans, it loses everything downstream of it too, because there's no ID left to attach them to. This is why third-party clients, message queues, and background job runners are the most common places tracing silently breaks: they weren't built with a context-propagation hook in mind, so someone has to add it explicitly.

- **Synchronous HTTP and gRPC calls** propagate through standard headers most tracing libraries handle automatically.
- **Message queues and async workers** need the trace context stored in the message payload explicitly, since there's no live header to carry it.
- **Third-party or legacy clients** that strip unknown headers are the most common silent break — verify propagation through them directly, don't assume.

**Done when:** a single request can be traced end to end through every service and queue it touches, with no unexplained gaps.

## 2. Model spans around units of work, not around code structure

A span should represent something you'd want to see the duration of on its own — an HTTP call, a database query, a cache lookup, a queue publish — not every function call in the codebase.

Over-instrumenting turns a trace into noise that's as hard to read as no trace at all; under-instrumenting leaves the actual slow step invisible inside one giant span. Attach attributes (not new spans) for detail that doesn't need its own duration: query text, cache hit/miss, retry count, the same status-code and endpoint dimensions used in metrics.

- **A span per unit of work worth timing on its own** — an HTTP call, a query, a cache lookup, a queue publish.
- **Attributes for everything else** — anything that describes the span but doesn't need its own start and end time.
- **No span for every function call** — that's noise that makes the real signal in the waterfall harder to find, not easier.

**Done when:** every span in a trace corresponds to a real unit of work someone would want timed on its own, and the slow step is visible as its own span, not buried inside a bigger one.

## 3. Sample by keeping what's abnormal, not by keeping a flat percentage

Tracing every request at full detail is rarely affordable once traffic is real, but a flat 1% sample rate throws away exactly the traces most worth having — the slow ones and the failed ones are rare by definition, so a flat sample mostly captures boring, fast, successful requests. Tail-based sampling (decide whether to keep a trace after it finishes, based on whether it was slow or errored) keeps the interesting population at low cost; head-based sampling (decide before the request starts) is cheaper to run but structurally can't make that distinction.

- **Keep 100% of errored and slow traces** — decided at the tail, once the outcome is known.
- **Sample routine, fast, successful traces** at a low rate, just enough to see the shape of normal.
- **Head-based sampling is fine for cost control** on the routine population, but never as the only mechanism for the interesting one.

**Done when:** slow and errored requests are captured at a much higher rate than routine successful ones, by design, not by luck.

## 4. Read a trace by finding the widest gap, not the deepest span

The fastest way to find where latency actually accumulated is to look for the span with the largest gap between its start and its children's start, or the largest span with no children of its own — that's either unaccounted-for time (queueing, connection setup, GC) or a leaf operation that's genuinely slow. A trace waterfall view makes this visual: a request that looks slow "in service B" often turns out to be entirely spent waiting for a lock or a connection pool inside B, not doing B's actual work, and only the span breakdown reveals that.

- **A gap between a span and its children** is unaccounted-for time — queueing, connection setup, garbage collection — worth naming, not ignoring.
- **A leaf span with no children and a long duration** is the actual slow operation, not just a slow-looking service.
- **"Slow in service B" is a starting point, not a conclusion** — the waterfall usually reassigns blame once you actually look.

**Done when:** for a given slow trace, you can name the specific span responsible for the majority of the added latency, not just the service.

## 5. Correlate traces with logs and metrics instead of treating them as separate tools

A trace tells you where the time went; it rarely tells you why a specific query was slow or what the error message actually was.

- **Attach the trace ID to every log line the request produces** — see `log-management` for how that field should be structured.
- **Tag the relevant metrics with the same dimensions** used in span attributes, so a metric spike and a trace agree on what they're describing.
- **A shared ID turns a manual timestamp-and-hope search** into a direct pivot from trace to logs for the exact same request.

**Done when:** from any slow or errored trace, you can jump directly to the matching logs for that same request.

## 6. Treat trace backend cost as a sampling-policy problem, not a storage problem

Trace storage grows with span count × attribute size × retention, and it's tempting to solve rising cost by trimming attributes or shortening retention uniformly. That degrades the traces you kept without addressing why you're keeping so many boring ones.

- **Check sampling rate first** — a cost spike is usually more boring traces getting through, not more expensive ones.
- **Check attribute cardinality second** — a high-cardinality attribute on every span multiplies storage the same way a bad metric label does.
- **Only touch retention last**, since it degrades every trace equally, including the ones actively worth keeping.

Revisit the sampling policy from step 3 first — a cost problem in tracing is almost always a sampling problem wearing a storage bill as a disguise.

**Done when:** a tracing cost increase is diagnosed by checking sampling rate and cardinality of attributes before touching retention.

## Report

State which services have propagation wired up (and which don't yet), the sampling strategy and rate for errored/slow versus routine traces, and whether trace IDs are correlated into logs.

Name the honest gap — usually one or two services or async boundaries where context propagation silently drops — rather than claiming end-to-end tracing coverage that hasn't actually been verified hop by hop.
