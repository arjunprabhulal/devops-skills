---
name: compliance-as-code
description: Turns compliance controls into executable, version-controlled checks with automated evidence collection, so audits become a query instead of a fire drill. Use this whenever the user is preparing for SOC 2, ISO 27001, or PCI audits, mapping controls to infrastructure, detecting drift from a compliance baseline, manually screenshotting settings for an auditor, or proving a control is enforced rather than just documented. For enforcing rules at deploy time use `policy-as-code`; for who has access to audited systems use `iam-access-management`.
license: MIT
---

# Compliance as Code

The traditional audit is a controlled panic: weeks of screenshotting console settings, chasing
down who approved what, and hoping nothing changed between the evidence snapshot and the actual
audit date. That process proves compliance at one instant in time and says nothing about the
other 364 days of the year — which is exactly when the control usually drifts.

Compliance as code expresses each control as a check that runs continuously against real
infrastructure, producing evidence as a byproduct of normal operation instead of a special one-
time effort. The audit stops being an event you prepare for and becomes a report you already
have.

**If proving a control holds requires a human to go look, the control isn't actually enforced —
it's hoped for.**

## 1. Map each control to a concrete, checkable assertion

"Encrypt data at rest" is a policy statement, not a control you can automate. "Every RDS
instance has `storage_encrypted = true`" is a control. Break every framework requirement (SOC
2, ISO 27001, PCI-DSS, HIPAA) down to assertions that map onto real resource attributes, IAM
configuration, or pipeline gates. Many frameworks overlap heavily — build the control library
once and map multiple frameworks onto it rather than duplicating checks per framework.

**Done when:** every control in scope has at least one automated check that queries live
infrastructure state.

## 2. Encode controls as code, run them continuously

Tools like OPA/Rego, Chef InSpec, or cloud-native config rules let you express "this is what
compliant looks like" as a versioned artifact that runs on a schedule or on every change, not
just before an audit. Version control gives you the same review and history for a compliance
rule that you'd expect for application code — a control change should go through a pull
request, not a spreadsheet edit.

```rego
# compliant: every storage bucket must deny public read
deny[msg] {
  input.resource_type == "storage_bucket"
  input.public_access == true
  msg := "bucket must not allow public access"
}
```

**Done when:** compliance checks run on a schedule independent of any upcoming audit date.

## 3. Generate evidence automatically, not manually

An auditor wants proof a control held over a period, not a screenshot from the morning of the
audit. Pipe check results, timestamps, and remediation history into a store the audit process
reads directly, so "show me evidence for control X for the last quarter" is a query, not a
scavenger hunt through Slack and email threads.

- **Timestamp everything**: a control that's compliant today is worthless evidence for a claim
  about last quarter unless you can show continuous history.
- **Store evidence immutably**, so it can't be edited after the fact to look better than it
  was.

**Done when:** producing a quarter's evidence for any control takes a query, not a manual
evidence-gathering effort.

## 4. Detect and alert on drift from baseline

A control that passed at deploy time can silently fail six months later — someone opens a
security group "temporarily," a bucket policy gets loosened for a one-off debugging session and
never gets reverted. Continuous checks catch this the same day it happens rather than at the
next audit cycle, when the cause is long forgotten and the exposure window was months, not
hours.

**Done when:** a manual change that violates a control triggers an alert before the next audit,
not during it.

## 5. Treat every finding as a ticket with an owner, not a checkbox

A failed control needs a remediation path as concrete as a vulnerability finding: who owns it,
what fixes it, and by when. Controls that fail silently into a dashboard nobody reads provide
no more assurance than not checking at all — the goal is closed-loop remediation, not just
visibility.

**Done when:** every failing control has an assigned owner and a remediation deadline, tracked
the same way as any other production issue.

## Report

State which frameworks are in scope, what fraction of controls are automated versus still
manually attested, and how evidence is generated and stored. Name the control category still
verified by hand — that manual gap is where drift will hide undetected, and calling it out is
more credible than claiming full automation.
