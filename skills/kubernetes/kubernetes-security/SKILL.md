---
name: kubernetes-security
description: Hardens the cluster and its workloads — RBAC least-privilege, Pod Security Standards, admission control with OPA/Kyverno, securityContext, secrets at rest, image provenance, and disabling default service-account automount. Use this whenever the user asks about RBAC roles, hardening pod security, writing an admission policy, or reducing what a compromised pod can do. For network isolation use `kubernetes-networking` and `multi-tenancy`; for image contents use `image-scanning`; for secret backends use `secrets-management`.
license: MIT
---

# Kubernetes Security

Kubernetes ships permissive by default: any pod gets a service-account token mountable for API
access, RBAC starts wide open until you constrain it, and nothing stops a container from running as
root unless you tell it not to. Security here is subtractive work — removing default permissions the
platform hands out for convenience, not adding a product on top.

Assume every pod will eventually be compromised and ask what that gets the attacker. **The right
default is the least the workload needs to function, enforced at admission, not caught in review.**

## 1. Scope RBAC to the verb and resource, not the namespace

The most common RBAC mistake is binding `ClusterRole: edit` or `cluster-admin` because a narrower
role was fiddly to write. A Role/ClusterRole should list exact verbs (`get`, `list`, `watch`,
`create`) against exact resources — "can read Pods in this namespace" is a different, much smaller
grant than "edit everything."

- **Prefer Role+RoleBinding over ClusterRole+ClusterRoleBinding** unless the permission genuinely
  spans namespaces — cluster-scoped grants are the ones that turn one compromised namespace into a
  cluster-wide incident.
- **Audit with `kubectl auth can-i --list --as=<sa>`** rather than reading YAML and hoping — it's
  the ground truth the API server actually enforces.
- **Service accounts, not user credentials**, should hold workload permissions; humans get scoped
  roles through your identity provider, see `iam-access-management`.

**Done when:** `kubectl auth can-i --list` for the workload's service account shows nothing beyond
what it demonstrably calls.

## 2. Turn off the automount you didn't ask for

Every pod gets a service-account token mounted by default, whether or not it ever calls the
Kubernetes API. That token is exactly what an attacker inside a compromised container reaches for
first — disabling automount removes a capability most workloads never needed.

```yaml
spec:
  automountServiceAccountToken: false   # set at pod or ServiceAccount level
```

Only workloads that genuinely call the API (controllers, operators — see `operators-and-crds`)
should have a token, and it should be bound to a ServiceAccount scoped by rule 1, not `default`.

**Done when:** `automountServiceAccountToken: false` is set for every workload that doesn't call the
Kubernetes API.

## 3. Enforce Pod Security Standards at admission, not by convention

A securityContext written correctly once and never checked again drifts the moment someone copies
an old manifest. Pod Security Admission (the built-in `restricted`/`baseline`/`privileged` labels)
or an admission controller like Kyverno/OPA Gatekeeper turns "we ask people not to run as root" into
"the API server rejects it."

- **`restricted` profile** requires non-root, no privilege escalation, a disallowed hostPath/hostPID,
  and a defined seccomp profile — treat it as the namespace-wide floor, not an aspiration.
- **Custom policy beyond PSS** (require specific labels, block `:latest` tags, require resource
  limits) is what OPA/Kyverno add — write policies as code and test them like code; broader
  organizational policy patterns live in `policy-as-code`.
- **Warn-then-enforce rollout**: label a namespace `audit`/`warn` first, watch violations in logs,
  then flip to `enforce` — flipping straight to enforce breaks things you didn't know existed.

**Done when:** every namespace has an enforced Pod Security Standard label, and no exceptions exist
without an explicit, documented reason.

## 4. Don't let secrets at rest mean secrets in cleartext

A Kubernetes `Secret` is base64, not encrypted, by default — anyone with `get` on it or etcd access
reads it in plaintext. Encryption at rest (`EncryptionConfiguration` on the API server, or a KMS
provider) and keeping actual secret material out of Git are separate problems that both need
solving.

- **Enable encryption at rest** for the Secrets resource specifically — it is not on by default on
  most self-managed clusters.
- **RBAC on `secrets` resources** should be as tight as anything in rule 1 — read access to Secrets
  is equivalent to read access to whatever they protect.
- **For rotation, external stores, and injection patterns** (Vault, cloud KMS, External Secrets
  Operator), that's the deeper subject of `secrets-management` — this skill only covers the
  in-cluster storage posture.

**Done when:** encryption at rest is confirmed enabled and no application secret exists as a
plaintext file in version control.

## 5. Verify what you run, not just what you scanned

Scanning an image for CVEs (`image-scanning`) tells you what's inside it; provenance tells you the
image you're running is the one you built, not something swapped in the registry or a compromised
CI step. Without signature verification at admission, a scanned-clean image and a tampered one are
indistinguishable to the cluster.

- **Require signed images** (cosign/sigstore or your registry's equivalent) and enforce verification
  via admission policy — an unsigned or wrongly-signed image should be rejected, not logged.
- **Pin by digest, not tag**, for anything security-sensitive — tags are mutable pointers.
- **Supply-chain provenance beyond the cluster boundary** — SBOMs, build attestation — is
  `supply-chain-security`; this rule is only about what the admission controller checks before
  scheduling.

**Done when:** the admission controller rejects an unsigned or unverified image in a test run.

## Report

State the RBAC scope granted to each workload identity, whether automount is disabled by default,
which Pod Security Standard is enforced per namespace, the secrets-at-rest encryption status, and
whether image signature verification is active. Call out any namespace still in audit/warn mode
instead of enforce, or any workload still holding broader RBAC than it uses — naming the gap beats
implying the cluster is fully locked down.
