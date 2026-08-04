---
name: metrics-and-monitoring
description: Covers instrumenting and collecting numeric time-series data — the Prometheus data model, choosing between counters, gauges, and histograms, controlling cardinality before it controls your bill, applying RED and USE systematically, and writing recording rules. Use this whenever the user is adding metrics to code, choosing a metric type, debugging a cardinality explosion or a slow metrics query, or deciding between pull and push collection. For turning metrics into paging rules use `alerting`, for visualizing them use `dashboards`, and for the broader signal strategy use `observability`.
license: MIT
---

# Metrics and Monitoring

A metric is a compressed, aggregatable summary of something that happened many times — it deliberately throws away per-event detail to stay cheap at scale. That trade only works if you pick the right shape (counter, gauge, histogram) and keep the label set small; get either wrong and you've built either a metric that can't answer the question or a metrics backend that falls over under its own cardinality.

Prometheus's pull-based model made this trade-off explicit for a generation of tooling: a metric is a name plus a set of key-value labels, sampled on a schedule, and every design decision below follows from taking that model seriously rather than fighting it.

**A metric earns its cost by staying cheap to query at 3am, six months from now, with a year of history behind it.**

For PromQL patterns — rate, histogram quantiles, RED/USE queries, and recording rules — read `references/promql.md`.

## 1. Pick the metric type the query needs, not the one that's easiest to emit

The three core types answer different questions and are not interchangeable after the fact:

- **Counter** — a value that only goes up (requests served, errors, bytes sent). Never set it directly; use `rate()` over a window to get a meaningful number. Good for "how much happened."
- **Gauge** — a value that goes up and down (queue depth, in-flight requests, memory used). Good for "what is the state right now."
- **Histogram** (or summary) — a distribution bucketed by value, almost always used for latency. Good for "what's the p99," which an average can never tell you because it hides the tail.

Emitting latency as a gauge of the last request's duration, or errors as a gauge instead of a counter, are the two most common type mistakes — both make the eventual query impossible without redeploying the instrumentation.

- **A gauge of "last request duration"** throws away everything but the most recent sample; a histogram keeps the distribution.
- **A gauge of error count** can't be turned into a rate cleanly the way a counter can with `rate()`.
- **Fixing a wrong metric type after the fact** means a redeploy and a gap in history — worth getting right the first time.

**Done when:** every metric's type matches how it will actually be queried, not just how it's naturally computed in code.

## 2. Treat every label as a cardinality decision

Cardinality is the number of unique label-value combinations a metric can produce, and it is the single biggest cost and reliability lever in a metrics system — each combination is a separate time series the backend must store and index. A label like `status_code` is cheap (a handful of values); a label like `user_id`, `request_path` with unbounded path params, or `pod_ip` is not, and can turn one metric into millions of series.

- **Ask what set of values a label can take in production**, not in the test you just ran locally.
- **Never put an identifier — user, request, session, IP — in a metric label**; that detail belongs in a log or trace attribute instead.
- **Review new metrics for cardinality before they ship**, the same way you'd review a schema migration — it's much cheaper to catch here than after the backend is already struggling.

**Done when:** no metric has an unbounded or high-cardinality label, and you can state the worst-case series count for each metric you own.

## 3. Apply RED and USE without re-deriving them each time

For every request-driven service, expose Rate, Errors, and Duration, broken down by the dimensions that matter for debugging (endpoint, status class) and no further. For every finite resource — connection pool, disk, thread pool, downstream dependency — expose Utilization, Saturation, and Errors. These two checklists cover the overwhelming majority of "why is it slow / why is it failing" investigations, and applying them mechanically to every new service is far more reliable than inventing bespoke metrics under incident pressure.

- **Rate** as a counter of requests, divided by time in a query, not sampled as a gauge.
- **Errors** as a counter partitioned by status class, so error rate is a ratio of two counters, not a raw count.
- **Duration** as a histogram, so percentiles are queryable later without having pre-decided which one mattered.

**Done when:** a new service ships with RED and USE metrics before it ships with a dashboard.

## 4. Pre-aggregate the expensive queries as recording rules

A dashboard or alert that recomputes a heavy aggregation (a `rate()` over a high-cardinality histogram, joined across services) on every load is slow and, worse, inconsistent between the alert and the dashboard that shows why it fired. Recording rules pre-compute that expression on a schedule and save it as a new time series, so the alert and the dashboard both read the same cheap, pre-baked number:

```yaml
- record: job:http_requests:rate5m
  expr: sum by (job) (rate(http_requests_total[5m]))
- alert: HighErrorRate
  expr: job:http_requests_errors:rate5m / job:http_requests:rate5m > 0.05
  for: 10m
```

The alert here reads the same pre-computed series the dashboard reads, so there's never a discrepancy between what fired and what's shown as the reason.

**Done when:** every alert expression reads a recording rule rather than computing a multi-minute aggregation inline.

## 5. Choose pull vs push by who knows the service is alive

Pull-based collection (the scraper asks the service for its current metrics) is the default for anything long-running: it makes "is this target even reachable" itself a signal, and it puts the collector in control of load. Push-based collection (the service sends metrics to a gateway) is for things that don't live long enough to be scraped — batch jobs, cron jobs, serverless functions — where there's no stable target to poll before the process exits.

- **Pull for anything long-running**, since scrape failure is itself a usable signal that something's wrong.
- **Push for anything short-lived**, since it will finish and exit before a scraper would ever reach it.
- **Picking pull for a short-lived job** just means silently missing its last few seconds of metrics; see `scheduled-jobs` for job-shaped workloads specifically.

**Done when:** every workload's collection method matches its lifecycle, not just the team's default.

## 6. Separate "monitoring is broken" from "the service is broken"

A metrics pipeline that silently drops data during the exact outage you needed it for is worse than no metrics — it gives false confidence. Monitor the monitoring: scrape success/failure, ingestion lag, and rule evaluation failures are metrics too.

- **Scrape success and target up/down** — a target that's stopped reporting looks identical to "everything's fine" unless you're watching for it directly.
- **Rule evaluation failures and ingestion lag** — a delayed pipeline delays every downstream alert with it.
- **Route this meta-monitoring through its own low-noise path**, so a storage backend problem doesn't masquerade as "everything's fine, no alerts fired."

**Done when:** a failure in the metrics pipeline itself pages someone, distinctly from a service-level alert.

## Report

State which services have RED/USE metrics live, the current worst-case cardinality contributors, which alerts run on recording rules versus raw queries, and the collection model (pull/push) per workload class. Name the honest gap — usually a handful of unbounded labels already in production, a service that still lacks basic Duration instrumentation, or a recording-rule migration that's only partly done — rather than reporting metrics coverage as complete when it's only true for the services you looked at most recently.
