---
name: network-security
description: Protects traffic and boundaries through segmentation, default-deny rules, egress control, and TLS everywhere, minimizing what's actually reachable on the network. Use this whenever the user is configuring security groups or firewalls, designing network segmentation, asking why a service can reach something it shouldn't, setting up egress filtering, or enabling TLS between internal services. For identity-based access that replaces network location as the trust boundary use `zero-trust`; for Kubernetes-specific network policy and mesh use `kubernetes-networking`.
license: MIT
---

# Network Security

The default state of most cloud networks is far too permissive: a security group that allows
all outbound traffic, a VPC where every subnet can reach every other subnet, a database
reachable from anywhere inside the perimeter because nobody restricted it after launch. That
permissiveness isn't a deliberate decision, it's just what happens when nobody actively
restricts it — and every unrestricted path is one more route an attacker can use after a single
compromised workload.

Reduce what's reachable before worrying about detecting what happens on the paths that remain.
A network where nothing unnecessary can talk to anything else contains a breach by
construction, without needing to detect it first.

**The traffic you never allowed is traffic you never have to defend.**

## 1. Segment the network around blast radius, not org chart

Flat networks let a single compromised service reach everything else on the network, turning
one bad container into a full breach. Segment by trust boundary and sensitivity — public-facing
tier, application tier, data tier — so lateral movement from a compromised workload hits a wall
quickly instead of a clear path to the database.

- **Separate by environment first**: prod, staging, and dev should not share network
  reachability, ever.
- **Separate by data sensitivity next**: the segment holding customer PII gets tighter rules
  than the segment serving static assets.

**Done when:** a compromised workload in one segment cannot reach resources in another segment
without an explicit rule allowing it.

## 2. Default-deny, then add exactly what's needed

An allow-all baseline with occasional deny rules requires you to anticipate every bad path in
advance, which nobody does completely. Default-deny inverts the burden: nothing talks to
anything until a rule explicitly permits it, so the failure mode of a forgotten rule is
"service can't reach what it needs" — loud and immediately visible — instead of "unintended
path stays open silently for years."

```hcl
# security group: deny is implicit, only add what's actually needed
ingress {
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = ["10.0.1.0/24"]  # app tier only, not 0.0.0.0/0
}
```

**Done when:** removing every explicit rule leaves zero traffic flowing, not some implicit
allowance.

## 3. Control egress as deliberately as ingress

Teams lock down what can come in and leave outbound traffic wide open, which is exactly
backwards from an attacker's perspective — after a compromise, the next move is calling out to
exfiltrate data or pull a second-stage payload, and unrestricted egress makes both trivial.
Egress allowlists (by destination, not just port) turn "reach any external host on port 443"
into a much smaller, auditable set of actual dependencies.

**Done when:** a workload attempting to reach an unlisted external destination is blocked and
logged.

## 4. Encrypt traffic on the wire, including internally

"It's inside our network, so it's trusted" was never as true as it sounded, and it gets less
true every year as networks span multiple clouds, regions, and third-party peering. TLS between
internal services costs little with modern tooling (service mesh sidecars, mTLS libraries) and
removes an entire class of on-path interception risk, whether the interception comes from a
misconfigured route, a compromised host, or a malicious insider on the same segment.

**Done when:** capturing traffic on the internal network yields no plaintext application data.

## 5. Minimize the reachable surface continuously, not just at launch

Rules that were correct at launch drift as services are added, decommissioned, or reconfigured
— an old rule for a service that was retired last year is still an open door with nothing
behind it that matters, and a new one that's wider than intended. Periodically audit actual
traffic flows against configured rules and remove what's unused; a rule nobody remembers the
reason for is a rule that's probably too wide.

**Done when:** every active firewall or security group rule maps to a currently running,
currently justified traffic flow.

## Report

State the segmentation boundaries in place, whether the default posture is allow or deny, and
whether egress is currently filtered or open. Name any segment, rule, or path still wider than
it needs to be — an unreviewed wide-open rule is the most likely way in, and calling it out is
more useful than describing the network as locked down.
