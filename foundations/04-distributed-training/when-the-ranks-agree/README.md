---
status: verified
level: foundation
base: scratch
label: When the ranks agree
verified: 2026-08-06
---

# The all-reduce that makes ranks agree

**Question:** [the distributed chapter](../) runs real DDP and ZeRO-1
collectives on four CPU processes. This chapter reads the recorded run and
asks what the three numbers it printed actually establish.

**Before this:** [the distributed chapter](../) and its recorded CPU
simulation.

## The mechanism, read

The run ([record](runs/2026-08-06-rank-agreement.md)) reads the recorded
simulation:

| number | value | what it means |
|---|---:|---|
| pre-all-reduce gradient delta | 0.000119 | ranks genuinely differ before the reduction |
| post-all-reduce divergence | asserted 0.0 | the all-reduce makes them identical |
| optimizer state / parameters | 2.00x | Adam keeps two moments per parameter |
| ZeRO-1 per-rank optimizer state | 1.05 MB (from 2.62) | sharded /4 without changing the math |

## Two readings

**The delta is the whole point of DDP.** If the pre-reduction delta were
zero, the ranks would be seeing identical data and the exercise would be a
no-op. The 0.000119 is the proof that each rank computed from its own batch
— and the asserted zero divergence after the all-reduce is the proof that
the collective actually merged them. The mechanism is both halves: different
gradients in, identical gradients out, and every rank applies the same
update to the same weights.

**The 2x optimizer ratio is why ZeRO exists.** Weights are not what fills
the card — Adam's two moment estimates are. Sharding them (ZeRO-1) drops
each rank's share from 2.62 MB to 1.05 MB, a 2.5x reduction, while the
asserted zero divergence holds: memory was saved without changing the
mathematics of the update. That is the trade the rest of the distributed
stack builds on.

## Evidence boundary

The recorded four-rank CPU simulation (gloo backend, one toy model, DDP and
ZeRO-1 modes). It reads that record; it does not re-run the collectives and
does not measure communication cost, which the chapter itself states is
invisible on one machine.

## Check your mental model

Answer each before opening it.

**1. Why must the pre-reduction gradients differ for DDP to mean anything?**

<details>
<summary>Answer</summary>

Because data parallelism's entire premise is that each rank trains on a
different batch. If the gradients were already identical, the ranks would
be computing the same thing redundantly and the all-reduce would add
communication with nothing to merge. The delta is the evidence that the
premise holds; the zero post-reduction divergence is the evidence that the
merge worked.

</details>

**2. Why does ZeRO-1 give 2.5x, not the 4x a world size of four suggests?**

<details>
<summary>Answer</summary>

Because this toy has 5 parameter tensors distributed round-robin across 4
ranks — ownership cannot divide evenly, so some ranks hold 2 tensors and
others 1. Production implementations shard by element count precisely
because tensor count divides badly; the uneven split in the recorded run is
the same phenomenon at toy scale, and seeing it is more instructive than
rounding it away.

</details>

## Next

Back to [the distributed chapter](../), or to
[why allreduce topology matters](../networking/) where the
communication cost this simulation cannot show is measured.
