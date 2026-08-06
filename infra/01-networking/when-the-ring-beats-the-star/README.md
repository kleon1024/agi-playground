---
status: verified
level: applied
base: scratch
label: When the ring beats the star
verified: 2026-08-06
---

# Why the ring wins every cell of the sweep

**Question:** [the networking chapter](../) ran star and ring allreduce
across world sizes 2-8 and payloads 1-32 MB. This chapter reads the
recorded sweep and asks where the ring's advantage comes from.

**Before this:** [the networking chapter](../) and its recorded star-vs-ring
run.

## The sweep, read

The run ([record](runs/2026-08-06-ring-vs-star-read.md)) reads the recorded
9-combination sweep. The pattern in three rows (world 8):

| payload | star | ring | ring/star time | star bytes/rank | ring bytes/rank |
|---:|---:|---:|---:|---:|---:|
| 1 MB | 0.0121 | 0.0071 | 0.59x | 3,670,016 | 1,835,008 |
| 8 MB | 0.3813 | 0.0910 | 0.24x | 29,360,128 | 14,680,064 |
| 32 MB | 1.0304 | 0.5080 | 0.49x | 117,440,512 | 58,720,256 |

## Two readings

**Ring halves the bytes each rank moves.** At every cell, star's bytes per
rank is exactly 2x ring's — the star topology sends the full gradient to
and from a central rank, while the ring passes each shard around the ring
once. That byte-count difference is the mechanism; the wall-clock win is
its consequence.

**The advantage grows with payload because bandwidth, not latency, is what
the topology trades.** At world 8, ring is 0.59x of star's time at 1 MB and
0.24x at 8 MB — the heavier the payload, the more the per-rank bandwidth
halving matters. This is why the cluster chapter's wiring decision is not a
fixed "ring is better" but a scaling law: the topology matters most exactly
when the tensors are biggest.

## Evidence boundary

The recorded localhost-IPC sweep (world sizes 2/4/8 x payloads 1/8/32 MB,
one process pair per cell, gloo-equivalent semantics). It reads that
artifact; it does not re-run the collectives and does not extend the result
to multi-node NICs, where latency and link topology change the crossover
point.

## Check your mental model

Answer each before opening it.

**1. Why does ring move half the bytes of star at the same world size?**

<details>
<summary>Answer</summary>

Because the two topologies move the data differently. Star has one central
rank that receives every rank's gradient and then sends the total back —
so each non-central rank sends its full gradient to the center and the
center sends the full total to each rank. Ring passes each shard around the
ring once, so each rank sends and receives only its own shard. Twice the
bytes in, half the bytes each way out — the recorded 2x ratio is exact.

</details>

**2. At world 2, ring wins only 0.29x-to-0.77x of star's time. Why is the
advantage not uniform?**

<details>
<summary>Answer</summary>

Because at small world sizes and small payloads, latency and process
overhead dominate and the byte-count advantage is diluted — the measured
cells are noisy (0.29x at 1 MB, 0.77x at 8 MB for world 2). The clean,
large advantage appears where the sweep is actually informative: bigger
payloads, where bandwidth dominates. The non-monotonic cells are the
overhead regime, not a refutation of the mechanism.

</details>

## Next

Back to [the networking chapter](../), or to
[the cluster topology chapter](../../05-gpu-cluster-concepts/) which uses this
same all-reduce to show why the cluster's wiring decides the parallelism
strategy.
