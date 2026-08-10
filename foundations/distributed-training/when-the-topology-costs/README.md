---
status: verified
level: applied
base: scratch
label: When the topology costs
verified: 2026-08-06
---

# The coordination tax that grows with the graph

**Question:** [the cluster chapter](../) timed all-reduce over 200
iterations at world sizes 2, 4, 8 with a fixed 4 MB tensor. This chapter
reads the recorded run and asks why the per-call time grows when the data
never changes.

**Before this:** [the cluster chapter](../) and its recorded topology
timings.

## The timings, read

The run ([record](runs/2026-08-06-topology-read.md)) reads the recorded
per-call means:

| world size | 4 MB all-reduce | growth vs world 2 |
|---:|---:|---:|
| 2 | 1.82 ms/call | 1.0x |
| 4 | 3.60 ms/call | 1.98x |
| 8 | 8.31 ms/call | 4.57x |

## Two readings

**The tensor never changes, so the growth is coordination, not data.** The
payload is 4 MB in every cell; what grows is the number of ranks that have
to synchronize and the number of hops the reduction crosses. Doubling the
world size nearly doubles the per-call time (x1.98 at world 4) and more
than doubles it again at world 8 (x4.57) — the cost scales with the
coordination graph, not with the gradient.

**This is why the cluster's wiring decides the parallelism strategy.** If
all-reduce time grows with rank count even at a fixed tensor, then a
topology that shortens the reduction path is worth more than a topology
that moves data faster. The chapter's own claim — the wiring decides which
parallelism strategy is worth running — is the measured consequence of
these three numbers.

## The fix and its trade

The fix is reading the coordination tax for what it is, so the wiring
decision is made on the right curve. The recorded growth — x1.98 at world 4,
x4.57 at world 8 — with a fixed 4 MB payload is the evidence that the cost
scales with the coordination graph, not with the gradient, which means a
faster NIC cannot cure it: the tax is per-rank-pair rendezvous, not bytes.
What the curve buys is a quantitative rule for choosing among parallelism
strategies — data parallelism pays the tax once per step and tolerates a
slow link; tensor parallelism pays it many times per step and therefore
belongs on the shortest, fastest path (Shoeybi et al., "Megatron-LM," 2019;
the ring all-reduce being bandwidth-optimal comes from Thakur, Rabenseifner,
and Gropp, "Optimization of Collective Communication Operations in MPICH,"
2005).

The trade is that the tax is only worth paying while the alternative is
worse. The chapter's answer to "what makes it worth paying" is explicit:
data parallelism pays the tax to split the batch, ZeRO-style sharding pays
it to split the memory, and the decision is which tax is cheaper for a given
model and data size. The recorded curve makes that comparison a number
instead of a preference — but it is a local-machine number, and the
evidence boundary is honest that real multi-node NICs, where latency and
link topology change the curve, would re-fit the x1.98 and x4.57 themselves.

## Who owns the loop

- **The platform team** owns the topology and the rank count: the decision
  to grow world size is a decision to buy coordination tax, and the curve
  at fixed tensor size is the chart that prices it.
- **The training engineer** owns the strategy choice: which parallelism
  pays the tax how many times per step, and where each strategy is placed,
  follows from this same curve.
- **The benchmarking owner** owns the boundary: the recorded growth is
  coordination overhead, and handing it to a bandwidth-hungry argument is
  the conflation this chapter's label exists to prevent.

## Evidence boundary

The recorded local-machine timings (world sizes 2/4/8, 4 MB tensor, 200
timed iterations after 20 warmup, gloo CPU backend, no GPU). It reads that
artifact; it does not re-run the collectives and does not extend the cost
to real multi-node NICs, where latency and link topology change the curve.

## Check your mental model

Answer each before opening it.

**1. Why does all-reduce get slower when the tensor size is fixed?**

<details>
<summary>Answer</summary>

Because the collective is a coordination operation, not just a data
transfer. Each additional rank adds synchronization points and hops the
reduction has to cross; even with nothing extra to move, the protocol does
more work. The recorded growth (x1.98, x4.57) is that coordination tax,
which is why it cannot be fixed by a faster NIC.

</details>

**2. What would make the coordination tax worth paying?**

<details>
<summary>Answer</summary>

It is worth paying whenever the alternative — one rank holding the whole
model — is worse. Data parallelism pays the tax to split the batch;
ZeRO-style sharding pays it to split the memory. The cluster chapter's
decision is about which tax is cheaper for a given model and data size,
and the timing curve is what makes that comparison a number instead of a
preference.

</details>

## Next

Back to [the cluster chapter](../), or to
[the ring-vs-star detour](../../networking/when-the-ring-beats-the-star/)
which measures the same all-reduce's byte-cost under two topologies.
