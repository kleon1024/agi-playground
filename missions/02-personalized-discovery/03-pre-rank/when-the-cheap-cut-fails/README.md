---
status: verified
level: applied
base: none
label: When the cheap cut fails
verified: 2026-08-06
---

# When does the cheap cut fail?

**Question:** [stage 03](../) cuts the candidate set from ~1,000 to ~100
with a model a hundredth of the fine-ranker's cost. The cut has a price —
surface rate, the fraction of the true top items that survives. This
chapter measures that price across keep sizes, and the scorer that is
structurally blind to the long tail.

**Before this:** [stage 03's pre-rank](../), including its recorded
long-tail surface run.

## The sweep, measured

The run ([record](runs/2026-08-06-surface-sweep.md)) scores the stage's
synthetic catalogue with three scorers at four keep sizes:

| keep | cheap proxy surface | popularity surface | popularity long-tail |
|---:|---:|---:|---:|
| 50 | 0.55 | 0.35 | 0.00 |
| 100 | 0.85 | 0.50 | 0.00 |
| 200 | 1.00 | 0.55 | 0.00 |
| 300 | 1.00 | 0.55 | 0.00 |

## Two readings

**The cheap cut's price is the keep size.** The proxy surfaces all of the
true top-20 at keep 200 on this catalogue, and only 55% at keep 50 — and of
the long-tail true-top items, 11% at keep 50 versus 100% at 200. The cut's
cost is a curve, not a number: tight cuts save compute and lose surface,
and the fine-rank ceiling (1.000 everywhere) is the price of running the
expensive model on everything.

**Popularity-only is structurally long-tail-blind.** Its overall surface
plateaus at 0.55 and its long-tail surface is 0.000 at every keep size —
popularity can never recover an item with no history, no matter how large
the cut. That is why pre-rank must be a real proxy (content or embedding),
not a popularity sort: the long-tail surface rate is the part of the
catalogue the cheap scorer exists to keep, and the popularity scorer loses
it by construction.

## Evidence boundary

One synthetic catalogue, one seed, three scorers, four keep sizes. It shows
the surface-rate curves and the popularity scorer's permanent long-tail
blindness on this design; it does not claim the exact keep-size threshold
transfers to real catalogues.

## Check your mental model

Answer each before opening it.

**1. Why does popularity-only's surface plateau while the proxy's keeps
climbing?**

<details>
<summary>Answer</summary>

Because popularity is a fixed ranking: it always surfaces the same popular
items, and the true top-20 that overlap with popularity are a fixed share
(about 55%) no matter how many candidates you keep. The proxy ranks by a
content signal, so a larger keep genuinely rescues more true-top items. The
plateau is the signature of a scorer with nothing to learn from a bigger
cut.

</details>

**2. The long-tail surface rate is 0.000 for popularity at every keep. What
does that say about the items the pre-rank must protect?**

<details>
<summary>Answer</summary>

That the long-tail true-top items are unreachable by popularity by
construction — they have no history to be popular. The pre-rank's job is to
keep them through the cut, and only a real proxy (content, embedding) can
do that; a popularity sort would silently drop every cold-but-good item
before the fine-ranker ever saw it, which is exactly the stage's claim
measured.

</details>

## Next

Back to [stage 03's pre-rank](../), or forward to
[stage 04's fine-rank](../../04-fine-rank/) where the cut's survivors get
the expensive multi-objective model.
