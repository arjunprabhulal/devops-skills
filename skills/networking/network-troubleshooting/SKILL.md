---
name: network-troubleshooting
description: Covers diagnosing connectivity failures methodically, layer by layer, with the right tool per symptom — dig/nslookup for DNS, curl/openssl for TLS and HTTP, traceroute/mtr for routing, tcpdump for packet capture, and ss/netstat for local socket state. Use this whenever the user reports a connection timing out, refused, or intermittently failing, cannot tell whether DNS, routing, a firewall, or the application is at fault, or needs to prove exactly where a request is failing. For fixing DNS records once diagnosed use `dns-management`, and for policy fixes once isolated use `network-security`.
license: MIT
---

# Network Troubleshooting

"It's not connecting" describes a symptom, not a cause, and the cause could be any of six or seven
layers between the client and the application. The single biggest time-waster in network
troubleshooting is guessing at the application layer first because it's the most familiar, when
the fault is actually two layers down in DNS or routing. Working through the stack in order —
resolution, then reachability, then the port, then the protocol, then the application — turns a
guessing session into a bounded diagnosis.

**Isolate the layer before you fix anything; a fix aimed at the wrong layer just adds noise to the
next person's investigation.**

For a symptom-driven command cookbook (dig, curl, traceroute, ss, tcpdump), read
`references/diagnostic-commands.md`.

## 1. Confirm DNS resolves to what you expect before touching anything else

If the name doesn't resolve, or resolves to the wrong address, nothing past this point matters.
`dig` gives more control and cleaner output than `nslookup` for this — use it against both the
system resolver and the authoritative server directly to separate a propagation issue from a wrong
record.

```bash
dig +short api.example.com                # what the system resolver returns
dig +short api.example.com @8.8.8.8       # bypass local cache, check a public resolver
dig api.example.com NS                    # who is authoritative
```

- **A mismatch between the two queries above** means propagation lag or a stale local cache, not a
  wrong record — see `dns-management` for TTL behavior.
- **`NXDOMAIN` from the authoritative server itself** means the record genuinely doesn't exist;
  stop looking downstream and fix the zone.

**Done when:** the resolved address is confirmed correct from both the client's resolver and the
authoritative source, or the mismatch is understood and explained.

## 2. Confirm reachability and the path before assuming a firewall

Once the address is right, check whether packets can get there at all, and where they stop if not.
`traceroute` (or `mtr` for a continuously updating view with loss percentages) shows each hop; a
consistent stop at the same hop across repeated runs points at that hop specifically, not at the
destination.

```bash
traceroute api.example.com
mtr -rw api.example.com          # report mode, shows per-hop loss over time
```

- **Traceroute stopping at your own gateway or a known internal hop** points at local routing or a
  firewall rule, not the remote service.
- **Total loss with no partial path** on a route that normally works is often a firewall silently
  dropping rather than a real routing failure — an explicit `REJECT` sends something back, a silent
  `DROP` looks identical to packet loss.

**Done when:** the path either completes to the destination, or the exact hop where it stops is
identified and attributable to a specific network or policy.

## 3. Confirm the port and TLS handshake before blaming the application

A host being reachable doesn't mean the specific port is open or that TLS is negotiating correctly.
`curl` with verbose output separates connection, TLS handshake, and HTTP response into distinct
phases, which tells you exactly which one failed instead of just "it didn't work."

```bash
curl -v https://api.example.com/health
openssl s_client -connect api.example.com:443 -servername api.example.com
```

- **Connection refused** means nothing is listening on that port, or a firewall actively rejected
  it — different from a timeout, which means nothing is responding at all.
- **TLS handshake failure specifically** (cert mismatch, expired cert, unsupported protocol
  version) shows clearly in `curl -v` output before any HTTP response is even attempted.
- **A response at all, even an error status,** proves the network path and TLS are both fine and
  the problem has moved to the application.

**Done when:** you can state definitively which phase — connect, TLS, or HTTP response — the
request is actually failing at.

## 4. Check local socket and process state before assuming the problem is remote

Half the time a "network" issue is local: a process not actually listening on the expected port, a
socket stuck in `CLOSE_WAIT` because the application never closed it, or a local firewall rule.
`ss` (the modern replacement for `netstat`) shows exactly what's bound and in what state.

```bash
ss -tlnp                 # what's actually listening, and which process owns it
ss -tanp | grep CLOSE_WAIT   # sockets the app opened but never closed
```

**Done when:** the expected process is confirmed listening on the expected port with no
unexpected accumulation of stuck connection states.

## 5. Capture packets when everything above looks fine and it still fails

`tcpdump` is the last resort because it produces the most data to sift through, but it's the only
tool that shows ground truth when every higher-level tool reports success and the failure is
intermittent or timing-dependent — a retransmission storm, a reset from an intermediate device, or
an asymmetric route.

```bash
tcpdump -i any host api.example.com -w capture.pcap
tcpdump -i any port 443 and host api.example.com   # narrow before capturing broadly
```

- **Filter tightly before capturing**, not after — an unfiltered capture on a busy host is
  unreadable and can itself affect timing.
- **A `RST` from the far side** appearing in the capture is definitive: something actively closed
  the connection, which redirects the investigation toward a firewall, load balancer, or
  application-level reset rather than a routing problem.

**Done when:** the capture shows the specific packet-level event causing the failure, or
definitively rules out the network layer and hands the investigation to `root-cause-analysis` at
the application level.

## Report

State which layer the failure was isolated to (DNS, routing, port/TLS, local socket, or
application), the exact command output that proved it, and what fixed it or who owns the fix.
Name the honest gap — usually an intermittent symptom that was never reproduced during the capture
window — rather than declaring the issue resolved when it was only reproduced and diagnosed once.
