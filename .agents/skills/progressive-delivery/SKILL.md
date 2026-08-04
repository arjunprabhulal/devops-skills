---
name: progressive-delivery
description: Automates canary and blue-green rollouts so promotion and rollback are driven by live metrics, not a timer or a human watching a dashboard, using controllers like Argo Rollouts or Flagger. Use this whenever the user wants automatic rollback on error-rate or latency regression, is defining an AnalysisTemplate or metric provider, asks about canary weight steps, or wants a rollout gated on real signals, not "wait ten minutes and ship." For the strategies automated use `deployment-strategies`; for the reconciler underneath use `argocd-operations`; for metrics queried use `metrics-and-monitoring`.
license: MIT
---

# Progressive Delivery

Progressive delivery takes strategies covered in `deployment-strategies` — canary, blue-green — and
makes the promotion decision automatic and metric-driven instead of manual or time-based. A canary
that "runs for ten minutes then goes to 100%" is not progressive delivery, it's a timer with extra
steps: if the ten minutes happened not to expose the regression, you ship it anyway. The controller
(Argo Rollouts, Flagger) exists to query real signals at each step and decide, without a human in
the loop, whether to advance, hold, or abort.

**A canary step that isn't gated on a query against production metrics is just a delay, not a
safety mechanism.**

## 1. Pick metrics that would actually catch a bad release

The default temptation is to gate on whatever's easiest to query — often just HTTP error rate. That
catches crashes, not the more common failure: a change that's technically 200-OK but slower, more
expensive per request, or silently returning wrong data to a subset of users. Combine at least an
error-rate metric with a latency percentile (p95 or p99, not average — averages hide tail
regressions), and add a business metric when one exists and is fast enough to compute (checkout
success rate, not daily revenue). See `slo-definition` for choosing thresholds that reflect what
users actually notice, and `metrics-and-monitoring` for where these queries come from.

**Done when:** the analysis would have failed on the last real incident this service had.

## 2. Define the AnalysisTemplate as the actual go/no-go contract

The AnalysisTemplate (Argo Rollouts) or MetricTemplate (Flagger) is where "success" gets a precise
definition — the query, the threshold, how many consecutive failures trigger a rollback, how many
samples are required before a judgment is even made. Treat changes to this file with the same review
rigor as the deployment manifest itself, because a threshold set too loose makes the automation
theater, and one set too tight makes every deploy flap on noise.

```yaml
metrics:
  - name: error-rate
    interval: 1m
    successCondition: result[0] <= 0.01
    failureLimit: 3
    provider:
      prometheus:
        query: sum(rate(http_requests_total{status=~"5..",app="{{args.app}}"}[1m]))
              / sum(rate(http_requests_total{app="{{args.app}}"}[1m]))
```

**Done when:** every promotion or rollback decision can be traced to a specific metric crossing a
specific threshold, not to elapsed time.

## 3. Step canary weights to bound the blast radius, not to look thorough

Each step (5% → 20% → 50% → 100%) should exist because it changes how many real users are exposed
to a still-unproven version, with a pause long enough for the analysis to gather enough samples to
be statistically meaningful — a step that pauses for 30 seconds on a metric with a 1-minute scrape
interval never actually evaluates anything. Low-traffic services need fewer, coarser steps (there
aren't enough requests to make 5% meaningful) while high-traffic services can afford more, smaller
ones. Match the step count to request volume, not to a template copied from another service.

**Done when:** the first canary step exposes few enough users that a full failure is a non-event,
and the pause at each step is longer than one full metric-collection interval.

## 4. Automate rollback and make it actually revert, not just pause

On analysis failure the controller should scale the canary to zero and route all traffic back to
stable without waiting for a human to notice a Slack alert — that's the entire point of doing this
automatically. Verify this by actually failing a canary in a non-prod environment and watching
traffic shift back, not by reading the config and assuming it works. Pair this with `alerting` so a
triggered rollback is loudly announced even though no one had to perform it, and with
`incident-response` for what happens next if the rollback itself doesn't fully resolve the problem.

**Done when:** a deliberately broken canary in a test environment rolls back automatically with zero
manual intervention, and someone is notified that it happened.

## 5. Don't let the canary and the reconciler fight each other

A Rollout resource under Argo CD is still declarative, but the controller mutates replica counts and
traffic weights as it steps through analysis — the exact kind of drift `argocd-operations` normally
flags. Exclude the fields the Rollouts/Flagger controller owns (via `ignoreDifferences` or the
resource's own CRD status conventions) so the GitOps reconciler doesn't fight the rollout by trying
to sync it back to the committed replica count mid-canary.

**Done when:** a canary can run to completion without Argo CD reporting OutOfSync on the fields the
rollout controller is actively managing.

## Report

State which metrics gate promotion, the canary step sequence, and confirm rollback has been tested
to actually revert traffic, not just theoretically configured to. Call out any metric gate that's
still just error-rate with no latency or business signal, or any environment where rollback hasn't
been exercised — that untested path is the real risk, not the one written in the AnalysisTemplate.
