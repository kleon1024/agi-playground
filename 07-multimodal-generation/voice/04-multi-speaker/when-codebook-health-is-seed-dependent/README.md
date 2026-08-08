---
status: verified
level: applied
base: scratch
label: When codebook health is seed-dependent
verified: 2026-08-06
---

# No collapse — and a seed-dependent codebook

**Question:** [stage 04's multi-speaker run](../) retrained the codec on 10
speakers. This chapter reads the recorded JSONs and asks what "no
collapse" actually looked like.

**Before this:** [stage 04's multi-speaker run](../) and its recorded
JSONs.

## The health, read

The run ([record](runs/2026-08-06-health-read.md)) reads the recorded
seeds:

| seed | codes used | entropy ratio | eval MSE |
|---|---:|---:|---:|
| 0 | 18/64 | 0.405 | 0.02712 |
| 1 | 63/64 | 0.760 | 0.01698 |
| 2 | 32/64 | 0.644 | 0.02122 |

## Two readings

**No seed fully collapsed, and that is the first half of the result.** The
eval MSEs all beat the silence baseline (4.3%, 38.2%, 22.7% margins) and
every codebook has more than one active code — the 1-2-code collapse of
stage 00's pilot is gone. The recipe that escaped on stage 03's narrow
baseline did not fail outright at 10.

**Codebook health became seed-dependent, and that is the second half.**
The same architecture, step count, LR, and seeds produce 18, 63, and 32
of 64 codes. Seed 1's codebook is nearly full (63/64, entropy 0.760);
seed 0's is a quarter used (18/64, entropy 0.405). The fix that was
reliable on stage 03's narrow baseline is now a coin flip per seed — the generalization
gap stage 04 exists to record, and the exact problem stage 05's reset
targets.

## The fix and its trade

The fix is the three-seed protocol that turns reliability into a measured
property: the same architecture, step count, LR, and recipe produce 18, 63,
and 32 of 64 codes (entropy 0.405/0.760/0.644, eval MSE
0.02712/0.01698/0.02122), so "no collapse" is reported as the first half of
the result and seed-dependence as the second. The trade is that the read is
uncomfortable on purpose: no seed fully collapsed and every seed beats the
silence baseline, yet the capacity claim is unreliable — a seed using 18 of
64 entries is silently leaving 46 unused, and a production codec cannot
accept that variance. The fix buys a reliability verdict at the cost of
denying the "it works" reading that any single healthy seed would support.

## Who owns this loop

- **The eval owner** owns the seed protocol; a single healthy run is
  reported as one data point, never as evidence the codebook is safe.
- **The codec owner** owns the capacity claim the utilization figures make:
  the 64 entries are the representational budget, and seed-dependence in
  usage is a reliability defect, not a quality curiosity.
- **The mission owner** owns the handoff the seed-dependence justifies:
  the frontier gap is the reason stage 05 tests a mechanism (dead-code
  reset) rather than a bigger hyperparameter sweep.

## Evidence boundary

The recorded multi-speaker JSONs (three seeds, balanced 10-speaker
LibriSpeech mix, one recipe). It reads those artifacts; it does not
re-train.

## Check your mental model

Answer each before opening it.

**1. Why is seed-dependent codebook health a problem if no seed
collapsed?**

<details>
<summary>Answer</summary>

Because utilization is a capacity claim. The codebook's 64 entries are
the model's representational budget; a seed that uses 18 of them is
silently leaving 46 unused, and a different seed uses 63. The same
training run can produce very different capacity utilization depending on
its random seed — which is a reliability property, not a quality one, and
it is what a production codec cannot accept.

</details>

**2. What does the 10-speaker setting change about the fix?**

<details>
<summary>Answer</summary>

It tests generalization. The stage-03 recipe escaped collapse reliably on
its narrow baseline;
at 10 speakers the same recipe is seed-dependent. The fix that worked at
small scale did not transfer cleanly to larger scale — which is exactly
the "does the fix generalize" question stage 04 names, and the reason
stage 05 tries a mechanism (dead-code reset) rather than a bigger
hyperparameter sweep.

</details>

## Next

Back to [stage 04](../), or to
[the fix that did not generalize](../when-the-fix-did-not-generalize/)
which reads the same run's verdict side.
