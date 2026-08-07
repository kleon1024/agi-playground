---
status: verified
level: applied
base: scratch
label: Cascade consistency
verified: 2026-08-07
---

# The cut that ejects what the final ranker would have chosen

**Question:** the mission's funnel cuts the candidate set before the
expensive ranker. This stage asks what the cheap stage should optimize,
and answers: clicks — because a click-optimized pre-rank quietly discards
the transaction-heavy items the final ranker would have surfaced, and the
expensive ranker can only re-rank survivors.

**Before this:** [stage 02 — recall](../../shared/02-recall/) for the
candidate set, and [stage 03 — pre-rank](../../shared/03-pre-rank/) for the
stage whose objective this chapter changes.

## The two pre-ranks, executed

The run ([record](runs/2026-08-07-cascade-consistency.md)) cuts 1,500 items
to 100 with a click-optimized and a distilled pre-rank, then reads the
final top-20:

| pre-rank | top-20 recall | final NDCG |
|---|---:|---:|
| CTR-only | 0.35 | 0.967 |
| distilled from final score | 1.00 | 1.000 |

## The mechanism, named

Clicking is not the same as valuing. A pre-rank that optimizes clicks keeps
the clicky items and drops the transaction-heavy ones; the final ranker
then ranks what survived, so its NDCG measures a truncated problem and
looks fine while the top of its true ranking is gone. Distilling the final
score into the pre-rank — as a soft label instead of a click label — keeps
the top of the final ranking inside the cut. Top-K recall at the cut is
the metric that matters across a cascade, because no downstream model can
re-rank an item the cut already removed.

## Why this belongs in the mission

Every stage after recall assumes the candidate set is complete enough.
The cascade's consistency is decided at the cut, not at the final ranker,
and the cost of getting it wrong is paid in the final NDCG's blind spot.

## Evidence boundary

The executed synthetic read over a 1,500-item catalogue (illustrative,
deterministic). It demonstrates the cut effect; real systems must measure
top-K recall at each cut against the final ranker's choices and audit the
distillation target's own calibration.

## Check your mental model

Answer each before opening it.

**1. Why does the CTR-only pre-rank lose the final top-20?**

<details>
<summary>Answer</summary>

Because it optimizes a different objective. Transaction-heavy items are
rarely clicked often, so a click-optimized cut ejects them before the
final ranker sees them — the cut is a hard filter no downstream model can
undo.

</details>

**2. Why is top-K recall at the cut the cascade's metric?**

<details>
<summary>Answer</summary>

Because it measures the one thing downstream cannot repair: whether the
items the final ranker values survived the cut. Final NDCG alone is
computed on survivors, so it rewards a cascade that quietly discarded the
answer.

</details>

## Next

The distillation's own failure: [a noisy teacher passes its noise to the
pre-rank](when-the-distillation-blurs/), and the arithmetic of the cut:
[only 11 of the final top-20 survive a click-based cut of
80](when-top-k-is-not-preserved/).
