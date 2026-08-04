# PromQL patterns

PromQL only makes sense in light of the metric type it's querying — a counter, a gauge, and a histogram each demand a different query shape, and using the wrong one produces a number that looks plausible and is wrong. This reference covers the shapes that come up constantly: rates over counters, RED and USE queries, aggregation without blowing up cardinality, recording rules, and alert expressions.

## Contents

- The four metric types, and the query each implies
- `rate()` vs `irate()` — and why counters need one at all
- RED queries — Rate, Errors, Duration
- USE queries — Utilization, Saturation, Errors
- Aggregation with `sum by (...)`, and why the label list matters
- Recording rules for the expensive queries
- Alerting-rule expressions and `for:`

## The four metric types, and the query each implies

- **Counter** — monotonically increasing (requests, errors, bytes). Never query the raw value; always wrap it in `rate()` or `increase()`. The raw value is just "how many since the process started," which is meaningless on its own.
- **Gauge** — goes up and down (queue depth, memory, in-flight requests). Query it directly, or with `avg_over_time()` / `max_over_time()` to smooth noise. `rate()` on a gauge is a category error — there's no monotonic increase to rate.
- **Histogram** — a set of cumulative `_bucket` counters plus `_sum` and `_count`. Use `histogram_quantile()` over `rate()` of the buckets to get percentiles. Never average a histogram's `_sum` / `_count` and call it "the latency" without saying it's a mean — means hide the tail that histograms exist to expose.
- **Summary** — client-side quantiles plus `_sum` and `_count`. Cheaper to compute than a histogram's quantile math, but its quantiles can't be aggregated across instances (you can't average two p99s into a meaningful p99). Prefer histograms for anything you'll aggregate `sum by (...)`; reach for a summary only when you need a quantile the client controls and will never need to merge across series.

## `rate()` vs `irate()` — and why counters need one at all

A counter resets to zero on every process restart, so its raw value is a sawtooth, not a trend. `rate()` and `irate()` both correct for resets automatically (Prometheus detects a decrease and treats it as a reset), but they answer different questions:

```promql
# Average per-second rate over the last 5 minutes — smooth, good for alerting and dashboards
rate(http_requests_total[5m])

# Instantaneous rate from the last two samples in the window — spiky, good for fast-moving graphs
irate(http_requests_total[5m])
```

- **`rate()` for anything that feeds an alert or a slow-moving dashboard.** It averages over the whole window, so a single noisy scrape doesn't fire a page.
- **`irate()` only for high-resolution graphs of fast-changing counters**, where you want to see a spike, not smooth it away. Never use `irate()` in an alert expression — it's sensitive to exactly the noise you want an alert to ignore.
- **The window in `rate(...[5m])` should span at least 4 scrape intervals.** A 5m window against a 15s scrape interval has 20 samples to work with; a window close to the scrape interval produces gaps and `NaN`.

## RED queries — Rate, Errors, Duration

RED is for anything request-driven. All three read off the same instrumentation: a request counter, an error counter (or the request counter split by status class), and a latency histogram.

```promql
# Rate — requests per second, by service
sum by (job) (rate(http_requests_total[5m]))

# Errors — ratio of two counters, not a raw error count
sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
  /
sum by (job) (rate(http_requests_total[5m]))

# Duration (p99) — histogram_quantile over rate() of the _bucket series
histogram_quantile(0.99,
  sum by (le, job) (rate(http_request_duration_seconds_bucket[5m]))
)
```

- **Error rate is always a ratio of two counters**, never a bare `rate()` of an error counter alone — 5 errors/sec means nothing without knowing it's out of 10,000 requests/sec.
- **`histogram_quantile()` needs `le` preserved through the aggregation.** Drop `le` from the `sum by (...)` and every bucket collapses into one, and the quantile math produces garbage instead of an error.
- **Query the `_bucket` series, not `_sum` / `_count`.** Those two only give you a mean; the quantile lives entirely in the buckets.

## USE queries — Utilization, Saturation, Errors

USE is for finite resources: connection pools, disks, thread pools, downstream dependencies. Where RED starts from a counter, USE mixes gauges (current state) and counters (things that overflow).

```promql
# Utilization — fraction of a pool in use right now (gauge / gauge)
db_connections_in_use / db_connections_max

# Saturation — queue depth, a gauge read directly, no rate() involved
db_connection_wait_queue_depth

# Errors — connection failures, a counter, rated like any other error
rate(db_connection_errors_total[5m])
```

- **Utilization is a snapshot ratio**, not a rate — it's "how full is it right now," which is exactly what a gauge is for.
- **Saturation is the queue building up behind a resource** — a wait-queue depth, pending-task count, or throttling metric. A resource at 100% utilization with zero saturation is fine; the same utilization with a growing queue is the actual problem.
- **Don't rate a gauge to get "how fast is utilization changing."** If that trend matters, graph the gauge directly over a longer window instead.

## Aggregation with `sum by (...)`, and why the label list matters

`sum by (...)` (and `avg by`, `max by`, etc.) collapses a metric down to only the labels you list — every other label is discarded, which is usually what you want on a dashboard showing "per service" rather than "per pod per service per instance."

```promql
# Good — one series per job, regardless of how many pods back it
sum by (job) (rate(http_requests_total[5m]))

# Bad — one series per job per pod per instance; this is the cardinality
# explosion showing up at query time even if the underlying metric is fine
sum by (job, pod, instance) (rate(http_requests_total[5m]))
```

- **List only the labels the query needs to answer its question.** Aggregating away `pod` and `instance` isn't losing information you need for a service-level dashboard — it's the whole point of aggregation.
- **A query that returns thousands of series is a cardinality problem even if no individual metric is high-cardinality on its own** — combining several medium-cardinality labels multiplies, it doesn't add. `sum by` is where that multiplication becomes visible and where it should be cut down.
- **`without (...)` is the inverse of `by (...)`** — use it when you want to keep most labels and drop a specific noisy one (like `instance`), rather than re-listing everything else.

## Recording rules for the expensive queries

Anything computed on every dashboard load and every alert evaluation — a multi-minute `rate()` over a high-cardinality histogram, or a query joining several metrics — belongs in a recording rule instead of being typed inline everywhere it's needed.

```yaml
groups:
  - name: http_red
    rules:
      - record: job:http_requests:rate5m
        expr: sum by (job) (rate(http_requests_total[5m]))
      - record: job:http_request_errors:rate5m
        expr: sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
      - record: job:http_request_duration:p99_5m
        expr: |
          histogram_quantile(0.99,
            sum by (le, job) (rate(http_request_duration_seconds_bucket[5m]))
          )
```

- **Name recording rules `level:metric:operations`** (the convention Prometheus docs use) so it's obvious from the name alone what's been pre-aggregated and over what window.
- **Point both the dashboard and the alert at the recorded series**, not at the raw expression twice — that's what guarantees they never disagree about what fired.

## Alerting-rule expressions and `for:`

An alert expression should read a recording rule, use a ratio or threshold that's meaningful at a glance, and carry a `for:` duration long enough to reject noise but short enough to still page in time.

```yaml
- alert: HighErrorRate
  expr: job:http_request_errors:rate5m / job:http_requests:rate5m > 0.05
  for: 10m
  labels:
    severity: page
  annotations:
    summary: "{{ $labels.job }} error rate above 5% for 10m"

- alert: HighP99Latency
  expr: job:http_request_duration:p99_5m > 1
  for: 5m
```

- **`for:` requires the condition to hold continuously across every evaluation in that window**, not just at one instant — a single noisy scrape over threshold doesn't page, only a sustained one does.
- **Pick `for:` relative to the recording rule's own window**, not arbitrarily — a `for: 1m` on top of a `rate5m` recording rule barely adds any noise rejection, since the underlying series is already smoothed over 5 minutes.
- **A `for:` that's too long delays a real page**; one that's too short pages on transient blips. Both failure modes are visible in the alert's own history — check how often it flaps before trusting the duration.
