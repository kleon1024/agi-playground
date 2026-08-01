---
status: verified
level: applied
verified: 2026-08-01
label: GPU cluster concepts
---

# Why the cluster's wiring decides the parallelism strategy

**Question:** [`platform/training/01-distributed/`](../../platform/training/01-distributed/)
proves data parallelism's mechanism on one CPU and deliberately reports no
throughput numbers, because gloo's loopback has none of the bandwidth
contention that makes real interconnect a design decision. So what part of
"topology matters" *can* honestly be measured without a cluster — and what
part genuinely cannot?

**The artifact this chapter follows** is one number, measured three times: the
mean wall-clock cost of a single `all_reduce` call over a fixed-size tensor,
at world size 2, 4, and 8, isolated from any model forward or backward pass.

**Before this:** [distributed training, without a cluster](../../platform/training/01-distributed/) —
you need the correctness mechanism (all-reduce averages gradients, every rank
ends up identical) before its *cost* means anything.

## Three real interconnects, one cost model

A real GPU cluster has at least three distinct communication paths, and they
differ in bandwidth by orders of magnitude:

- **NVLink** — direct GPU-to-GPU links within one node. Highest bandwidth,
  lowest latency.
- **PCIe** — GPU to host, and host to host within a node if NVLink is absent
  or partial. An order of magnitude slower than NVLink.
- **Cross-node network (Ethernet or InfiniBand)** — between machines. Lower
  bandwidth and materially higher latency than either path within a node.

The standard collective algorithm for all-reduce — a ring, where each of `N`
ranks passes a `1/N` slice of the data to its neighbor for `N-1` steps, then
passes the reduced slices around again to broadcast the result — moves a
total of roughly `2(N-1)/N` times the tensor size, in and out, per rank. On a
single fast interconnect, that data volume is what a bandwidth-bound cost
model predicts: time grows with data moved, not with step count, once the
per-step chunks are large enough to saturate the link.

## Why that determines the parallelism strategy, not just the speed

The three parallelism strategies this repository's missions and platform
chapters use do not all pay this cost the same number of times per step:

- **Data parallelism** (this repo's `run_ddp`) all-reduces the gradient
  **once per optimizer step** — one collective, however large the model.
- **Tensor parallelism** all-reduces (or reduce-scatters) activations or
  gradients **inside every affected layer**, every forward and backward pass
  — many collectives per step, each smaller, but far more frequent.
- **Pipeline parallelism** sends **point-to-point activations** between
  adjacent stages, not a collective at all — its cost is dominated by latency
  and "bubble" idle time, not aggregate bandwidth.

A collective paid once per step tolerates a slower link; a collective paid
dozens of times per step does not. This is the concrete reason production
systems place tensor parallelism only across the fastest link available
(NVLink, inside one node) and reserve data or pipeline parallelism for the
slower cross-node link — not convention, a direct consequence of how many
times each strategy pays the cost above per step.

## What is actually measured here

`core/topology_timing.py` reuses this repository's own `setup()` and `log()`
from `platform/training/01-distributed/core/distributed.py` directly (no
duplication), and isolates one collective: it warms up, barriers, then times
200 repeated `all_reduce` calls over a fixed 4MB tensor and reports the mean
per-call wall-clock, at world size 2, 4, and 8, all on this machine's CPU via
gloo.

```
world_size= 2  tensor=4.0MB  mean all_reduce wall-clock = 1.8181 ms/call  (over 200 iters)
world_size= 4  tensor=4.0MB  mean all_reduce wall-clock = 3.5970 ms/call  (over 200 iters)
world_size= 8  tensor=4.0MB  mean all_reduce wall-clock = 8.3138 ms/call  (over 200 iters)
```

Doubling world size roughly doubled the measured wall-clock at every step —
2 to 4 ranks: 1.98x; 4 to 8 ranks: 2.31x. Full trace in
[`runs/2026-08-01-topology-timing.md`](runs/2026-08-01-topology-timing.md).

## What this number is, and what it is not

This is **not** a bandwidth measurement. All eight ranks are processes on one
CPU talking over loopback, which has orders of magnitude more bandwidth than
any real interconnect this chapter names, and the tensor here (4MB) never
comes close to saturating it. If this were bandwidth-bound, wall-clock would
depend on data volume, not rank count, and would barely move between world
sizes for a fixed tensor size.

What scaled instead is **coordination overhead**: every rank must rendezvous
with every other rank inside one `all_reduce` call, and gloo's default
algorithm for a tensor this size on CPU issues that rendezvous with a
per-rank-pair cost, not a constant one — so more ranks means more coordination
steps, and the measured near-linear growth (roughly 2x wall-clock per 2x
world size) reflects that step count, not link speed.

This is a real, useful analogy to one specific regime in real clusters: **small
messages are latency-bound, not bandwidth-bound.** NCCL itself switches
between a latency-optimized algorithm and a bandwidth-optimized ring
depending on message size, for exactly the reason this measurement surfaces —
below some size, the number of coordination round-trips dominates total cost
more than the bytes moved do. What this measurement cannot show, and does not
claim to, is the bandwidth-bound regime itself: the actual GB/s difference
between NVLink, PCIe, and cross-node Ethernet, and the point at which a
larger collective becomes bandwidth-bound rather than latency-bound. That
crossover point, and everything past it, needs a real multi-GPU, multi-node
cluster — the Modal lane, not this one.

## Exercises

1. **Grow the tensor.** Re-run at `--tensor-mb 64` and `--tensor-mb 256`. If
   the coordination-overhead explanation above is right, the *relative* cost
   of extra ranks should shrink as the tensor grows, because a fixed
   per-rank-pair rendezvous cost becomes a smaller fraction of a larger total.
2. **Compare to `run_ddp`'s per-step cost.** `distributed.py`'s DDP loop calls
   `all_reduce` once per parameter, not once per step — estimate how the
   measurements above would compound across a real model's parameter count,
   and why gradient bucketing (grouping many parameters into fewer, larger
   `all_reduce` calls) is standard practice once you see that arithmetic.
3. **Read this repository's `run_task.py`-style guardrail elsewhere**: this
   chapter deliberately reports coordination overhead as coordination
   overhead and refuses to call it a bandwidth result — check any of your own
   distributed benchmarks for the same conflation before trusting a claimed
   speedup.

## What this does not establish

Nothing about real GPU interconnect bandwidth, real cross-node network
latency, or the actual crossover point between latency-bound and
bandwidth-bound collective cost on real hardware — none of that is producible
on a CPU. Nothing about how NCCL's specific algorithm selection works
internally; this chapter names the phenomenon (algorithm choice depends on
message size) without reproducing NCCL's own decision logic. And nothing
about tensor- or pipeline-parallel wall-clock specifically — `run_ddp`'s
data-parallel collective is the only one timed here; a tensor-parallel
per-layer collective would need a real multi-layer sharded forward pass to
measure honestly, which is future work, not assumed here.

**Related:** [`local-4090.md`](../local-4090.md) and [`modal.md`](../modal.md)
document this repository's own two real compute lanes — neither currently
has the multi-node, multi-GPU topology this chapter's bandwidth-bound
question would need to close.
