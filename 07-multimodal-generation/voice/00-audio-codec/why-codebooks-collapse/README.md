---
status: verified
level: applied
base: scratch
label: Why codebooks collapse
verified: 2026-08-06
---

# Why does a VQ codebook collapse — and can you watch it happen?

**Question:** [stage 00](../) turns a waveform into a discrete token sequence
through a vector-quantized codebook, and its recorded run mentions a
collapse that a fix had to escape. This chapter measures the collapse
itself — codebook usage at 25-step intervals on a fresh seed — so the
mechanism is a trajectory, not a footnote.

**Before this:** [stage 00's codec](../) and its recorded run.

## The mechanism, in one sentence

The quantizer maps every encoder output to its nearest codebook vector via
argmin, and the gradient flows back through that nearest vector (the
straight-through trick). A code that is never the nearest vector receives no
gradient and stays dead forever, until the optimizer moves the live codes
enough that some encoder output crosses a boundary into it. Collapse is the
regime where the whole batch maps to one or two codes; recovery is the slow,
seed-dependent process of the codebook partitioning again.

## The measured trajectory

The run trains the stage's own codec for 600 steps on a fresh seed with
usage logged every 25 steps ([run record](runs/2026-08-06-codebook-collapse.md)):

| step | unique codes / 64 | entropy ratio |
|---:|---:|---:|
| 0 | 1 | 0.000 |
| 100 | 2 | 0.033 |
| 200 | 2 | 0.033 |
| 300 | 13 | 0.187 |
| 400 | 14 | 0.520 |
| 500 | 12 | 0.409 |
| 600 | 15 | 0.475 |

Three readings, and each contradicts an intuition:

**The whole batch starts on one code.** At step 0, all 2,048 tokens in the
batch map to a single codebook entry; 63 of 64 codes are dead, and dead
codes have no gradient path to escape. Collapse is not a late-training
failure; it is the initialization regime.

**Recovery is slow and non-monotonic.** The codebook is still at 2 codes
after 200 steps, partitions at 300, peaks at 400 (entropy 0.52), then *loses*
codes at 500 before ending at 15/64. Codes die and revive; the trajectory is
not a monotone climb.

**It is seed-dependent.** The recorded seed-0 run ended healthy at 34/64;
this seed-7 run ends at 15/64, from identical code. That is the exact
seed-dependence mission 07's later stages investigate, and it is why a
single healthy run is not evidence the codebook is safe.

<!-- interactive: CodebookUsageTimeline -->

## Why the line cared enough to fix it

The lineage this stage builds on made collapse a first-class problem:
**VQ-VAE** (van den Oord et al., 2017) introduced the discrete codebook and
its collapse; **SoundStream** (Zeghidour et al., 2021) made codebooks
residual (RVQ), so a collapsed level silently removes a whole bitrate tier;
**EnCodec** (Defossez et al., 2022) and **DAC** (Kumar et al., 2023) added
commitment and adversarial terms plus EMA-style fixes, and VQ-VAE-2's EMA
update is the direct ancestor of the reset/EMA 2x2 the mission measures in
[stage 05](../../05-codebook-reset/). The full line is in
[the realtime-voice lineage](../../lineage.md).

## The fix and its trade

The fix is measuring the collapse as a trajectory instead of a footnote:
logging codebook usage every 25 steps turns "collapse" into a legible,
measured process (1 code at step 0, 2 at 200, 13 at 300, peaking at 14
with entropy 0.520 at 400, then losing codes at 500 before ending at
15/64) and exposes its three properties: the whole batch starts on one
code, recovery is slow and non-monotonic, and it is seed-dependent (seed 0
ends healthy at 34/64, seed 7 at 15/64 from identical code). The trade is
that one seed and one configuration cannot certify the codebook — the
trajectory view is what makes a single healthy run insufficient evidence,
and the chapter does not measure how RVQ or EMA would change the shape
(stage 05's 2x2 exists for that).

## Who owns this loop

- **The codec owner** owns the usage telemetry contract: per-step
  bincounts and entropy are recorded in the run, not reconstructed after
  the fact.
- **The eval owner** owns the per-seed protocol that exposes
  seed-dependence; one healthy seed is reported as one data point, never
  as a certificate.
- **The mission owner** owns the downstream handoff: the seed-dependence
  measured here is the exact phenomenon stage 04 records at the frontier
  and stage 05/06's reset/EMA grid is built to fix.

## Evidence boundary

One seed, one codec config, 600 steps, on the stage's synthetic clips. It
demonstrates the collapse regime and its non-monotonic, seed-dependent
recovery on this configuration; it does not measure how RVQ or EMA changes
the trajectory — that is stage 05's 2x2. The widget's numbers are this run's
actual bincounts, not a schematic.

## Check your mental model

Answer each before opening it.

**1. Why do dead codes stay dead, and what finally revives them?**

<details>
<summary>Answer</summary>

Because the straight-through gradient flows only through the nearest
codebook vector. A code that is never nearest receives no update, so it
cannot become more attractive on its own. It revives only when the optimizer
moves the live codes' geometry enough that some encoder output crosses the
boundary into it — which is why recovery is slow, happens late, and depends
on the seed.

</details>

**2. The entropy ratio goes 0.52 at step 400 and 0.475 at 600. What does the
dip mean?**

<details>
<summary>Answer</summary>

That the codebook can lose codes after gaining them: at 500 the run has 12
unique codes, two fewer than at 400. Partitioning is not a one-way process,
so a single checkpoint's usage number cannot certify the codebook healthy —
which is exactly why the mission's later stages measure the fix across seeds
and across the reset/EMA grid.

</details>

## Next

[Stage 05 — codebook reset](../../05-codebook-reset/): the standard dead-code
reset and the EMA fix, measured in a 2x2 to find which half actually does the
work.
