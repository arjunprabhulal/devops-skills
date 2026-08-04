# The USE Method

USE stands for Utilization, Saturation, Errors. It is a checklist, not a diagnosis: for every
resource in the request path, ask whether it is busy, queueing, or failing. The point is not to
find *a* number that looks bad, it is to walk every resource in a fixed order so you cannot skip
the one you are unfamiliar with in favor of the one you already suspect.

- **Utilization** — the percentage of time the resource was busy doing work. High utilization
  means the resource has little slack left, but it does not by itself mean anything is wrong.
- **Saturation** — the amount of work the resource has queued that it cannot service right now.
  This is the number that predicts pain: utilization can sit at 90% forever with no queue and be
  fine, but a queue that is growing means requests are waiting longer every second that passes.
- **Errors** — the count of error events for the resource: retries, drops, corrupt packets,
  rejected allocations, throttling events. Errors are often silent to the application and only
  visible in resource-level counters, so they get missed if you stop at utilization.

Utilization tells you how busy something is. Saturation tells you whether that business is
already costing requests time. Errors tell you whether the resource is failing outright. All
three are cheap to read from the OS on any Linux box; none of them requires instrumenting the
application.

## Contents

- CPU
- Memory
- Disk / IO
- Network
- Per-process attribution
- Working the method

## CPU

- **Utilization**: percent of time not idle. `vmstat 1` (the `id` column, inverted) or
  `mpstat -P ALL 1` for a per-core breakdown — an aggregate 60% can hide one core pinned at 100%.
- **Saturation**: run-queue length — processes runnable but not currently on a CPU.
  `vmstat 1` reports this as the `r` column; a value consistently above the core count means
  work is waiting for CPU time it isn't getting. `sar -q 1` gives the same number with history.
- **Errors**: not classic errors, but throttling — cgroup CPU quota throttling or hypervisor
  steal time, both of which look like slowness with no local cause. Check
  `cat /sys/fs/cgroup/cpu.stat` (look for `nr_throttled` / `throttled_time`) for containers, and
  the `st` column in `vmstat 1` for steal time on a VM.
- **Command to start with**: `mpstat -P ALL 1 5` — shows per-core utilization and steal time in
  one pass.

## Memory

- **Utilization**: percent of memory in use. `free -m` — read `used` alongside `available`, not
  `free`; the kernel using RAM for cache is not the same as memory pressure.
- **Saturation**: this is the metric that actually matters for memory, and utilization alone is
  close to useless because caches inflate "used" without costing anything. Watch swap activity
  (`si`/`so` columns in `vmstat 1`) and page fault rate — nonzero swap-in/swap-out under load
  means the system is paging live data, not just caching. `sar -B 1` reports major fault rate
  (`majflt/s`), which is the more direct signal of pages being pulled back from disk.
- **Errors**: OOM kills. Check `dmesg -T | grep -i "oom-kill"` or `journalctl -k | grep -i oom-kill`
  — a process disappearing under load with no application-level error is almost always this.
- **Command to start with**: `free -m` for the headline number, `vmstat 1` for whether swap is
  actually moving.

## Disk / IO

- **Utilization**: percent of time the device was busy servicing requests. `iostat -x 1` — the
  `%util` column. Note that on an SSD or a RAID array with parallelism, 100% `%util` does not
  mean the device is out of capacity the way it would on a single spinning disk.
- **Saturation**: queue depth and average wait time, which is what actually predicts request
  latency. `iostat -x 1` gives `avgqu-sz` (queue size) and `await` (average wait, in ms,
  including queueing — compare it to `svctm`/`r_await`/`w_await` to see how much of the wait is
  queueing versus service time). A rising `await` with flat `svctm` means requests are queueing,
  not that the device got slower.
- **Errors**: device-level errors and retries. `dmesg -T | grep -iE "error|i/o error"` for
  hardware/driver-level failures; for filesystem-level issues check `journalctl` for the relevant
  fs module. A disk with a growing retry count will show fine utilization and terrible latency.
- **Command to start with**: `iostat -x 1 5` — this single command carries utilization,
  saturation, and enough of the timing breakdown to spot queueing.

## Network

- **Utilization**: throughput against link capacity. `sar -n DEV 1` for interface-level bytes/s,
  compared against the known link speed (`ethtool <iface>` if the number isn't already known).
- **Saturation**: retransmits and the socket backlog, since a network link rarely "fills up" the
  way a disk does — instead it drops or delays. `ss -s` for a summary, `ss -ti` for per-connection
  retransmit counts (`retrans`), and `netstat -s` (or `nstat`) for aggregate TCP retransmit and
  segment-loss counters. A rising retransmit rate under the same load is saturation, even if the
  interface itself shows low utilization.
- **Errors**: interface errors and drops. `ip -s link show <iface>` — the `errors` and `dropped`
  columns on both RX and TX. Nonzero and climbing means packets are being lost at the NIC or
  driver level, not just delayed.
- **Command to start with**: `ss -s` for a fast read on retransmits and connection state, then
  `sar -n DEV 1` for the throughput context.

## Per-process attribution

The resource-level commands above tell you *that* a resource is saturated; they don't tell you
which process is causing it. Once a resource is implicated, `pidstat 1` (with `-u` for CPU,
`-d` for disk, `-r` for memory) attributes that resource's usage to individual PIDs on the same
1-second cadence, so the process-level number lines up with the system-level one you just read.

## Working the method

Go down the list in order — CPU, memory, disk/IO, network, plus any resource specific to the
stack in front of you (connection pools, message queue depth, load balancer queue) — and read
utilization, saturation, and errors for each before drawing a conclusion. The resource that shows
saturation or errors is the bottleneck; the others are ruled out, not ignored.

Two failure modes to watch for while doing this:

- **Stopping at the first resource with nonzero utilization.** Every resource has nonzero
  utilization all the time. The question is whether it is queueing or erroring, not whether it is
  busy.
- **Treating a plausible-looking number as confirmation.** A CPU at 85% looks like an obvious
  answer, but if the run queue is flat and there are no throttling events, it is not the
  bottleneck — check saturation before committing to a story.

Take the USE reading before making any change, so it doubles as the baseline. After the change,
take the same reading again on the same resource. The bottleneck's utilization or saturation
metric moving in the expected direction is what confirms the change worked; a latency number that
improved for unrelated reasons (less traffic, a warmer cache) will not show up here, which is
exactly why this reading matters alongside, not instead of, the baseline metric from the top of
the tuning process.
