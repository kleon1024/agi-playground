---
status: verified
level: applied
base: scratch
label: When top-K is not preserved
verified: 2026-08-07
---

# The cut that eats the answer

**Question:** [stage 63](../) shows a distilled pre-rank keeping the final
top-20. This chapter quantifies the failure a click-based cut produces:
more than half of the final top-20 is ejected before the final ranker
ever sees it.

**Before this:** [stage 63 — cascade consistency](../).

## The cut, executed

The run ([record](runs/2026-08-07-topk-not-preserved.md)) cuts a 1,000-item
catalogue to 80 by clicks and reads the final top-20:

| measure | value |
|---|---:|
| catalogue | 1,000 |
| pre-rank cut | 80 |
| final top-20 surviving the cut | 11 of 20 |

## The reading

Clicking is not the same as valuing, and a click-optimized pre-rank can
eject most of the items the final ranker would have chosen before it ever
sees them. This is the metric to watch across the cascade — top-K recall
at the cut — because no downstream model can re-rank an item the cut
already removed. Stage 63's distilled pre-rank is the repair; this number
is the cost of not repairing.

## Evidence boundary

The executed read over a synthetic catalogue (illustrative, deterministic).
It demonstrates the survival arithmetic; real systems must measure top-K
recall at every cut against the final ranker's choices and set the cut
objective from that metric.

## Check your mental model

Answer each before opening it.

**1. Why does a click-based cut lose the transaction-heavy items?**

<details>
<summary>Answer</summary>

Because clicks are a different objective than value. Items with high
conditional value but low click rate are ranked out by a click-optimized
cut, and the final ranker never gets the chance to surface them.

</details>

**2. Why is top-K recall at the cut the right metric?**

<details>
<summary>Answer</summary>

Because it measures the cascade's one irreparable decision. Final NDCG is
computed on survivors, so it cannot see the items the cut removed; only
recall at the cut can.

</details>

## Next

Back to [stage 63](../). The distillation's own failure: [a noisy teacher
passes its noise to the pre-rank](../when-the-distillation-blurs/).
