# Diagnostic Commands Cookbook

A symptom-driven reference for the commands in the main skill. Each entry names the layer it
isolates, the exact invocation, and what separates a good result from a bad one — so you can match
a symptom to a command instead of running everything and hoping.

## Contents

- DNS layer
- Reachability and routing layer
- Port, TCP, and TLS layer
- Local socket and process layer
- Packet capture layer
- HTTP-level timing
- Which command for which symptom

## DNS layer

**`dig +short api.example.com`** — what the system resolver returns right now.
- Good: a single, expected IP (or CNAME chain ending in one).
- Bad: empty output (`NXDOMAIN` or resolver failure) or an IP that doesn't match any known
  record — either points at the zone or at a stale cache, not at the network.

**`dig +short api.example.com @8.8.8.8`** — same query against a public resolver, bypassing
whatever the client normally uses.
- Good: matches the system resolver's answer — rules out local cache or split-horizon DNS.
- Bad: differs from the system resolver — propagation lag or a resolver-specific override, not a
  broken record.

**`dig api.example.com NS`** then **`dig api.example.com @<authoritative-ns>`** — query the
authoritative server directly, skipping every cache in between.
- Good: returns the record you expect, immediately, with no ambiguity about propagation.
- Bad: `NXDOMAIN` here means the record genuinely doesn't exist — stop chasing caches and fix the
  zone.

**`nslookup api.example.com`** — same job as `dig +short`, less clean output; use it only when
`dig` isn't installed.

## Reachability and routing layer

**`ping -c 4 api.example.com`** — cheapest possible check that a host answers at L3 at all.
- Good: replies with consistent round-trip times.
- Bad: 100% loss with no error means either the host is down, or (more often) ICMP is filtered
  while TCP would work fine — don't stop here, confirm with a port-level check next.

**`traceroute api.example.com`** — shows every hop between you and the destination.
- Good: completes to the destination with reasonable per-hop latency.
- Bad: stops cold at the same hop across repeated runs — that hop, not the destination, owns the
  problem. Stopping at your own gateway means the issue is local before it's even left your network.

**`mtr -rw api.example.com`** — like traceroute but continuous, with loss percentage per hop over
time; use it for intermittent problems traceroute's single pass would miss.
- Good: 0% loss at every hop, including the last.
- Bad: loss appearing at one hop and persisting at every hop after it is that hop dropping
  packets; loss appearing only at the final hop and nowhere before it is usually the destination
  rate-limiting ICMP, not a real path problem — cross-check with TCP.

## Port, TCP, and TLS layer

**`nc -vz api.example.com 443`** — fastest way to answer "is anything listening on this port,"
with no TLS or HTTP involved.
- Good: `succeeded` — the three-way handshake completed.
- Bad: `Connection refused` means nothing is bound to that port, or a firewall actively rejected
  it; a hang with no response at all means something is silently dropping the packets — a `DROP`
  rule or a route that goes nowhere. Refused and silent-dropped are different failures and point
  at different owners.

**`curl -v https://api.example.com/health`** — the highest-value single command in this list; it
narrates connect, TLS handshake, and HTTP response as three distinct phases.
- Good: `* Connected to`, then TLS handshake lines, then a real HTTP status line — proves every
  layer up through the application responded.
- Bad: stalls after `* Trying <ip>...` — the port isn't reachable, back to the reachability layer.
  Fails during the `* TLS handshake` lines — cert or protocol problem, not connectivity. Connects
  and completes TLS but returns a 5xx — network is exonerated, hand off to the application.

**`openssl s_client -connect api.example.com:443 -servername api.example.com`** — use when
`curl -v`'s TLS summary isn't enough detail, e.g. to see the full certificate chain or negotiated
cipher.
- Good: `Verify return code: 0 (ok)` and a certificate chain that matches expectations.
- Bad: verify failure, an unexpected `subject=` (wrong cert served, often an SNI/vhost
  misconfiguration on a shared load balancer), or an expired `notAfter` date.

## Local socket and process layer

**`ss -tlnp`** — every TCP socket in `LISTEN` state, and the process that owns it.
- Good: the expected process is listed against the expected port and address (`0.0.0.0` or the
  right interface, not just `127.0.0.1` if remote clients need to reach it).
- Bad: nothing listening on the port at all (app isn't running or crashed), or it's bound to
  `127.0.0.1` when it needs to accept external connections.

**`ss -tanp | grep CLOSE_WAIT`** — sockets the remote side closed but the local app never did.
- Good: empty, or a small transient count.
- Bad: a large and growing count means the application is leaking connections — this looks like a
  network problem from the outside (things time out) but the fix is in the app, not the network.

**`ss -s`** — one-line summary of total sockets by state, useful as a fast triage before drilling
into specific states.
- Bad: TCP totals far above normal baseline, or a large `timewait` count on a host that shouldn't
  be churning connections that fast.

## Packet capture layer

**`tcpdump -ni <iface> port 443`** — ground truth, used only after the layers above all look
clean or the failure is intermittent enough that higher-level tools can't catch it mid-failure.
Filter before capturing, not after — an unfiltered capture on a busy host is unreadable.
- Good: a clean SYN, SYN-ACK, ACK, then normal data flow, then a clean FIN/ACK teardown.
- Bad: a SYN with no SYN-ACK ever arrives (confirms silent drop, not a slow server); a `RST`
  appearing mid-connection is definitive — something actively killed the connection, which points
  at a firewall, load balancer, or app-level reset, not routing.

## HTTP-level timing

**`curl -w "dns:%{time_namelookup} connect:%{time_connect} tls:%{time_appconnect} ttfb:%{time_starttransfer} total:%{time_total}\n" -o /dev/null -s https://api.example.com/health`**
— breaks a single request into named timing phases instead of one opaque total.
- Good: each phase is a small fraction of the total, and DNS/connect/TLS are near-zero on repeat
  requests (connection reuse, warm cache).
- Bad: a large gap between `connect` and `tls` isolates a slow or hanging TLS handshake; a large
  gap between `tls` and `ttfb` (time to first byte) is server-side processing time, not network —
  hand off to the application; a large `dns` value on its own points straight back at the DNS
  layer, not anything downstream of it.

## Which command for which symptom

| Symptom | Start here | Confirms/isolates |
|---|---|---|
| "Site doesn't resolve" or wrong IP | `dig +short`, `dig @8.8.8.8` | DNS record vs. cache/propagation |
| "Can't reach the host at all" | `ping`, `traceroute`, `mtr -rw` | Path exists, or the hop where it breaks |
| "Connection refused" | `nc -vz` | Nothing listening, or actively rejected |
| "Connection times out" (no refusal) | `nc -vz`, then `tcpdump` | Silent drop vs. genuine unreachability |
| "TLS/cert errors" | `curl -v`, `openssl s_client` | Handshake phase specifically, cert chain detail |
| "Works sometimes, not others" | `mtr -rw`, `tcpdump` | Intermittent loss or a mid-connection `RST` |
| "Service up but nothing connects" | `ss -tlnp` | Is it actually listening, on the right address |
| "Connections pile up over time" | `ss -tanp \| grep CLOSE_WAIT` | App-level leak, not network |
| "It's slow, not broken" | `curl -w` timing breakdown | Which phase — DNS, connect, TLS, or server — is slow |
