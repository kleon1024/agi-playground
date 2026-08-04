---
status: verified
level: reference
verified: 2026-08-01
label: Networking
---

# Why does allreduce topology matter, if the sum comes out the same either way?

**Question:** two ranks can average their gradients by routing every message
through one coordinator, or by passing partial sums around a ring. Both
produce the identical number. Why does anyone bother with the second one?

**The artifact this chapter follows** is a real measured comparison: the same
gradient-sized array, allreduced by two different message-passing topologies,
over real inter-process communication on one machine.

**Before this:** [distributed training, without a cluster](../../platform/training/01-distributed/)
-- that chapter asserts all-reduce as a single opaque collective operation and
measures what it does to memory. This chapter opens the collective itself and
measures what it does to the network.

## The mechanism: two ways to sum P arrays

**Star (naive):** every rank sends its local array to one coordinator rank.
The coordinator sums all P arrays and sends the result back to each of the
other P-1 ranks. Simple, and it is what a first implementation looks like.

**Ring:** arrange the P ranks in a cycle. Split each rank's array into P
chunks. In P-1 steps of *reduce-scatter*, each rank forwards a running partial
sum to its neighbor, so that after P-1 steps every rank holds the fully
reduced value for exactly one chunk. Then P-1 steps of *all-gather* circulate
those finished chunks around the ring so every rank ends up with the complete
result. No rank is ever a bottleneck; every rank sends and receives the same
amount, every step.

[`core/network_sim.py`](core/network_sim.py) implements both, on real OS
processes (`multiprocessing.Process`) communicating over real IPC queues, and
asserts every result against a plain single-process sum before trusting a
timing number.

The ring's reduce-scatter and all-gather phases, one step at a time:

<!-- interactive: RingAllreduceFlow -->

## What the coordinator actually costs

```
world_size payload_MB     star_s     ring_s  star_bytes/rank  ring_bytes/rank  correct
         2        1.0     0.0101     0.0029          2097152          1048576     True
         4        1.0     0.0307     0.0176          3145728          1572864     True
         8        1.0     0.0121     0.0071          3670016          1835008     True
         2       32.0     0.3246     0.1285         67108864         33554432     True
         4       32.0     0.5292     0.3954        100663296         50331648     True
         8       32.0     1.0304     0.5080        117440512         58720256     True
```

Ring wins every one of the nine (world_size, payload_size) combinations
measured, and the margin grows with `world_size` — at 8 ranks and 32MB, ring
is roughly twice as fast. The reason is visible in the bytes-per-rank
columns: `ring_bytes/rank` climbs toward roughly `2 x payload_size` and then
**stops climbing** as `world_size` grows, while `star_bytes/rank` keeps
growing because the coordinator's traffic — proportional to `world_size` — is
folded into the per-rank average. The star topology does not distribute its
cost; it concentrates it on one rank and then reports the average as if it
had.

Full sweep and every measured number:
[`runs/2026-08-01-star-vs-ring.md`](runs/2026-08-01-star-vs-ring.md).

## The failure mode that produced this chapter's real content

Both topologies deadlocked on the first attempt, and neither failure was
theoretical — both reproduced immediately at a large enough payload size, and
neither was visible at the small array size used for a first correctness
check.

Every rank in a naive ring implementation calls `send()` and then `receive()`.
Once a chunk is larger than the OS's pipe buffer (a few hundred KB), `send()`
blocks until the neighbor drains it — but the neighbor is itself blocked in
its own `send()`, waiting on *its* neighbor. Every rank waits on the next one
around the cycle, forever. Real distributed frameworks avoid this with
non-blocking sends or dedicated communication threads; this chapter's fix is
the same idea in miniature — a background thread per rank handles the
outgoing queue so the main thread is always free to drain the incoming one.

The star topology's version of the same bug was subtler: the coordinator
wrote its own reduced result back into its own result queue, which nobody
ever reads. At small payloads this sits harmlessly in the OS pipe buffer
forever; at large payloads the buffer fills and the coordinator itself
deadlocks on a write nobody will ever read. Same root cause — writing into a
channel with no active reader on the far end — two different topologies, two
different-looking failures.

## What this cannot show you

**Real network fabric.** Every message here crosses the same machine's memory
bus over a loopback IPC channel. It has none of a datacenter's bandwidth
ceilings, NIC contention, switch topology, or multi-hop latency — the numbers
above measure process-scheduling and serialization overhead, not network
transport. A real multi-node ring-allreduce's advantage over a real star
comes from the same asymptotic argument this chapter demonstrates, but the
absolute numbers on real interconnect (NVLink, InfiniBand, Ethernet) are not
measurable on one machine and this chapter does not claim otherwise.

**GPU collectives.** Real training frameworks (NCCL, `gloo`) implement
allreduce with hardware-aware topology selection, not the two fixed
strategies shown here. [`platform/training/01-distributed/`](../../platform/training/01-distributed/)
is where the actual training-relevant collective (via PyTorch's `gloo`
backend) is measured; this chapter is the topology argument underneath it,
not a replacement for it.

## A brief history

Ring-allreduce's bandwidth-optimal argument predates deep learning: Patarasuk
and Yuan formalized it in 2009 ("Bandwidth Optimal All-reduce Algorithms for
Clusters of Workstations," *Journal of Parallel and Distributed Computing*),
proving a ring's per-rank bandwidth cost is independent of world size while a
naive star's is not — the same asymptotic gap this chapter's sweep
reproduces. It became a fixture of deep learning specifically after Baidu's
2017 engineering post (Andrew Gibiansky, "Bringing HPC Techniques to Deep
Learning") applied the same algorithm to multi-GPU gradient synchronization;
NCCL's ring implementation and PyTorch's `gloo` backend both still default to
it for many message sizes today.

## Exercises

1. Run the sweep at `world_size=16`. Does the ring/star gap keep widening, or
   does process-scheduling overhead start to dominate at some point?
2. The star bug (writing to an unread queue) was invisible below a certain
   payload size. Find that threshold on your machine and explain why it
   depends on the OS's pipe buffer size, not on the code's logic.
3. Implement a third topology: a binary tree (each rank sends to and receives
   from two neighbors instead of one). Where does it fall between star and
   ring, and why?

## Run it

```bash
cd infra/01-networking/core
python3 network_sim.py --world-sizes 2 4 8 --payload-mb 1.0 8.0 32.0
```

CPU only, ~35s wall-clock, \$0. Full trace:
[`runs/2026-08-01-star-vs-ring.md`](runs/2026-08-01-star-vs-ring.md).
