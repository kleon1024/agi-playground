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

## The fix and its trade

The fix is to set the cut objective from top-K recall at the cut — stage
63's distilled pre-rank — and measure the survival at every cut against
the final ranker's choices. The executed read prices the failure the fix
exists to remove: cutting a 1,000-item catalogue to 80 by clicks ejects 9
of the final top-20 (11 of 20 survive), so more than half of what the
final ranker would have chosen never reaches it.

The trade, named: the repair costs a teacher dependency at the cheap
stage — the pre-rank must be distilled and re-audited against the final
ranker whenever either changes, which is real ongoing work. The
alternative is the trap the number exposes: a click-based cut looks fine
on final NDCG because NDCG is computed on survivors, so the cascade can
discard the answer and still pass its own metric. Top-K recall at the cut
is the only read that measures the cascade's one irreparable decision,
and the trade is paying for that measurement on every cut, not once.

## Who owns the loop

- **The pre-rank model team** owns the cut objective and its re-training
  contract — the cut is chosen from survival against the final ranker,
  not from click AUC.
- **The serving team** owns the cut size as a latency-and-quality budget:
  a bigger cut buys survival at the price of more expensive-stage traffic.
- **The evaluation team** owns the top-K recall measurement at every cut
  — the number that says the cascade kept the answer before the final
  ranker ever runs.

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
