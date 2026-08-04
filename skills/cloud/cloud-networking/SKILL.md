---
name: cloud-networking
description: Covers the virtual network layer of a cloud deployment — VPCs, subnets, route tables, peering and transit, private endpoints, egress control, and hybrid or on-prem connectivity. Use this whenever the user is designing a VPC/VNet layout, planning subnet CIDR ranges, connecting two networks or a cloud to a data center, locking down egress, or debugging traffic that can't cross a network boundary. For DNS and load balancing use `dns-management`/`load-balancing`; for perimeter posture use `network-security`.
license: MIT
---

# Cloud Networking

A cloud network is software pretending to be wires, and that means every routing decision is
explicit and reviewable in a way a physical network never was. The cost of that explicitness is
that nothing connects by default — every path between two resources exists because someone
configured it, which is a feature once you stop fighting it.

Treat the network layout as a security boundary first and a connectivity convenience second.
**Every path that traffic can take should be one someone deliberately allowed, not one that
happened to work.**

## 1. Plan CIDR ranges before you provision anything

Subnet ranges are painful to change after resources are placed in them, and overlapping ranges
are what block a future VPC peering or transit connection. Pick address space with room for
growth and with an eye toward every network you might ever need to connect to — including a
data center's existing ranges and other cloud accounts' VPCs.

| Decision | Get it wrong and… |
|---|---|
| CIDR too small | you run out of IPs and must re-subnet under pressure |
| CIDR overlaps peer network | peering or transit connection becomes impossible without renumbering |
| No reserved space for future subnets | new tiers (data, private endpoints) have nowhere to go |

**Done when:** the CIDR plan has documented headroom and has been checked against every network
it may ever need to peer or connect with.

## 2. Separate public and private subnets by function, not convenience

Anything that doesn't need a public IP shouldn't have a route to the internet gateway. Public
subnets hold load balancers and bastion/NAT infrastructure; private subnets hold everything else,
reaching the internet only through a NAT gateway if they need outbound access at all. This is the
single biggest reduction in attack surface available at the network layer, and it costs nothing
but discipline in the route table.

**Done when:** no compute or data resource holding sensitive data has a route to an internet
gateway.

## 3. Use private endpoints instead of the public internet for managed services

Most clouds offer a private-endpoint or private-link mechanism so traffic to a managed database,
object store, or API reaches it without leaving the provider's network. This avoids exposing the
service's public endpoint to the internet and avoids NAT egress cost for high-volume traffic. It
is a small setup cost for a permanent reduction in both risk and, often, bill size.

**Done when:** traffic to managed services from private subnets never traverses the public
internet.

## 4. Choose peering vs transit deliberately as the network count grows

Direct VPC peering does not transit — network A peered to B and B peered to C does not let A
reach C. That's fine for two or three networks; it becomes an unmanageable mesh past that. A
transit gateway (or provider equivalent) centralizes routing at the cost of a new component to
secure and a potential single point of failure. Pick peering for a small, stable set of networks
and transit once you're adding networks regularly.

**Done when:** the peering/transit choice is revisited once the network count exceeds a handful.

## 5. Control egress as deliberately as ingress

Inbound rules get the security attention; outbound often doesn't, and that's exactly the path
data takes when something goes wrong — exfiltration, a compromised dependency phoning home. Default
to deny-by-default egress with explicit allow rules for the destinations a workload actually
needs, especially for anything handling sensitive data.

**Done when:** egress from sensitive workloads is allow-listed, not open-by-default.

## 6. Design hybrid connectivity for the failure case, not just the happy path

A VPN or dedicated interconnect to on-prem is a single link until you add a second one — plan for
that link failing during the connection's design, not after the first outage. Route on-prem
traffic through redundant paths where the dependency is critical, and make sure DNS resolution
works correctly across the hybrid boundary in both directions.

**Done when:** the hybrid connection has a documented failure mode and, for critical dependencies,
a redundant path.

## Report

State the CIDR plan and its headroom, which subnets are public vs private and why, whether
managed-service traffic uses private endpoints, and the egress policy for sensitive workloads.
Name any network path that exists for historical reasons and isn't reviewed — an unreviewed path
is the one most likely to be the incident.
