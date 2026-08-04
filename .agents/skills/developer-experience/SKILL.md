---
name: developer-experience
description: Cuts the friction between having an idea and seeing it running — fast local feedback loops, painless environment setup, and DORA-plus metrics that reveal where time actually goes. Use this whenever the user complains local dev is slow or fragile, asks how to measure developer productivity, wants to reduce time-to-first-commit for new hires, or is deciding what toil to automate next. For the platform hosting these workflows use `internal-developer-platform`; for templates removing setup friction use `golden-paths`; for automating identified toil use `toil-reduction`.
license: MIT
---

# Developer Experience

Developer experience is not a survey score, it's the sum of every wait a developer sits through
between writing code and knowing whether it works: environment setup, build time, test time, CI
queue time, deploy time. Each wait is small enough to ignore individually and large enough,
multiplied by every developer and every day, to be the biggest lever a platform team has.

Optimize the loop a developer runs most often, not the one that's most interesting to fix. **The
fastest team is the one with the shortest gap between a change and knowing if it worked.**

## 1. Instrument the loop before you optimize it

Teams guess at their bottleneck and fix the wrong one — usually the part they personally find
annoying rather than the part costing the most aggregate time. Measure time-to-first-commit for a
new hire, local build time, CI wall-clock time, and deploy lead time before touching anything.
DORA's four keys (lead time, deploy frequency, change failure rate, MTTR) are a floor, not a
ceiling — add local-loop metrics DORA doesn't capture, since most developer time is spent before
code ever reaches CI.

| Loop stage | What to measure | Who feels it first |
|---|---|---|
| Local dev | time from clone to running app | new hires |
| Build/test | wall-clock per run | everyone, every commit |
| CI | queue time + pipeline duration | anyone waiting on a PR |
| Deploy | lead time, change failure rate | on-call |

**Done when:** you have a baseline number, not an impression, for each stage above.

## 2. Make local dev boringly reliable

If setting up a working local environment takes more than an hour or requires tribal knowledge in
a Slack thread, developers will avoid touching unfamiliar parts of the codebase rather than fight
the setup — and that avoidance compounds into worse code review and slower onboarding. Standardize
on one documented path (devcontainer, Nix, a single setup script) and treat any manual step as a
bug in the setup, not a fact of life.

- **One command to a running app**: `make dev` or equivalent, no tribal-knowledge steps.
- **Parity with production config**, not a simplified stand-in that hides integration bugs until
  deploy.
- **Fast inner loop**: hot reload or incremental compilation so a one-line change doesn't trigger
  a full rebuild.

**Done when:** a new hire has a running local environment on day one without asking a teammate for
help.

## 3. Cut toil before you automate it

Automating a broken process just makes the breakage run faster and more often. Before scripting a
manual step away, ask whether it should exist at all — many approvals, handoffs, and manual
checklist items survive purely because nobody re-examined them after the reason for them expired.
See `toil-reduction` for the fuller framework on identifying and eliminating repetitive manual
work; the discipline here is doing that audit before writing automation, not after.

**Done when:** every piece of toil you automated has a named reason it needs to exist at all, not
just a script that hides it.

## 4. Treat CI queue time as a first-class metric

Developers experience CI as one number: how long until I know if I broke something. A fast test
suite behind a ten-minute runner queue is still a ten-minute wait from the developer's chair. Track
queue time separately from execution time — they have different fixes (more runners vs. faster
tests) and conflating them hides which one is actually the bottleneck. See `ci-pipelines` for
pipeline structure itself; this is about the wait as experienced, not the pipeline's internals.

**Done when:** queue time and execution time are tracked as separate numbers on the same
dashboard.

## 5. Ask developers, then verify with data

Surveys catch friction that metrics miss — a step that's fast but confusing, or documentation that's
technically present but never found. Metrics catch friction that surveys miss — the fifteen-minute
build everyone has quietly adapted to and stopped mentioning. Run both, and trust the pattern where
they agree more than either alone.

- **Run a short DevEx survey quarterly**, not once — friction shifts as the platform changes.
- **Cross-check complaints against metrics** before prioritizing a fix — a loud complaint about a
  rare event can crowd out a quiet, constant one.

**Done when:** the top three reported pain points each have a corresponding metric that moved after
the fix shipped.

## Report

State the current baseline for each loop stage, the single biggest bottleneck by developer-hours
lost per week, and what shipped to address it. Name which pain points are still reported but
unmeasured, or measured but unaddressed — that gap is next quarter's real priority, and naming it
beats declaring DevEx solved.
