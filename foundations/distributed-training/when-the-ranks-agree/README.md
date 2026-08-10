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

## The fix and its trade

The four numbers in the table are two fixes, and each trade is stated in
the same row that proves the fix works. The first fix is the assertion
protocol: the 0.000119 pre-reduction delta is the evidence that the ranks
genuinely saw different batches (if it were zero, DDP would be a no-op with
added communication), and the asserted 0.0 post-reduction divergence is the
evidence that the collective merged them — a silent desync, where one rank's
gradient is skipped, produces plausible loss curves and no complaint, which
is exactly why the run asserts agreement instead of hoping for it. The trade
is that the assertion only proves lockstep on this toy: the chapter's own
boundary concedes that communication cost is invisible on one machine, so
the protocol answers "did the ranks agree" and not "what did agreeing cost."

The second fix is ZeRO-1's sharding, and its trade is memory for
communication: per-rank optimizer state drops from 2.62 MB to 1.05 MB
(2.5x, not the 4x a world size of four suggests, because 5 tensors
round-robined across 4 ranks cannot divide evenly — production shards by
element count for exactly this reason) while each rank must broadcast the
parameters it updated after every optimizer step. The recorded zero
divergence under sharding is the point: memory was saved without changing
the mathematics of the update, and the price is traffic the toy cannot
measure (ZeRO: Rajbhandari, Rasley, Ruwase, and He, "ZeRO: Memory
Optimizations Toward Training Trillion Parameter Models," SC, 2020).

## Who owns the loop

- **The training engineer** owns the assertion protocol: printing the
  pre-reduce delta beside the post-reduce divergence is the diagnostic that
  answers "are the ranks actually different, and did the merge actually
  work," and a run that prints only the final loss has dropped both pieces
  of evidence.
- **The framework team** owns the sharding arithmetic: the ownership rule
  (round-robin tensor count here, element count in production) decides the
  memory split, and the broadcast after each optimizer step is the
  communication cost this chapter's boundary hands to the cluster chapter.
- **The platform team** owns the unmeasured half: what the collective
  actually costs on real interconnect is the networking and topology
  chapters' job, and the 2.5x-vs-4x gap is the warning that memory savings
  follow the ownership rule, not the world size.

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
