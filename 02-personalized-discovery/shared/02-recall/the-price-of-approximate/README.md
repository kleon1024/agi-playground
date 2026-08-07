---
status: verified
level: applied
base: scratch
label: The price of approximate
verified: 2026-08-06
---

# Recall bought back at a measured latency cost

**Question:** [stage 02's recall](../) uses approximate ANN search to save
latency. This chapter reads the recorded exact-vs-approximate comparison
and asks what the approximate index actually costs.

**Before this:** [stage 02's recall](../) and its recorded FAISS run.

## The trade, read

The run ([record](runs/2026-08-06-approx-price.md)) reads the recorded
numbers:

| setting | recall@25 vs exact | latency |
|---|---:|---:|
| exact (IndexFlatIP) | — | 1.133 -> 0.911 ms |
| approximate, default | 0.913 | 0.576 ms |
| approximate, ef-search 64 | 0.984 | 0.714 ms |

## Two readings

**Approximate search is a recall-for-latency bargain, and the settings are
the dial.** Raising ef-search from its default to 64 bought recall (0.913
-> 0.984) at a real latency cost (0.576 -> 0.714 ms) — the trade is not
"approximate is free," it is "you can buy recall back, and here is the
measured price."

**The gap to exact never fully closes.** Even at ef-search 64, approximate
recall is 0.984, not 1.0 — 1.6% of the exact index's retrievals are lost,
and the latency advantage narrows but does not disappear. That residual is
the honest boundary: an approximate index trades a bounded recall loss for
latency, and the recall loss is a property of the index, not a bug.

## Evidence boundary

The recorded FAISS comparison (5,000 synthetic items, 32-dim vectors, 160
queries, two settings). It reads that artifact; it does not re-run the
index and the numbers characterize a synthetic catalogue, not production
data.

## Check your mental model

Answer each before opening it.

**1. Why is the exact index slower at the second setting (1.133 -> 0.911)?**

<details>
<summary>Answer</summary>

Because exact search is a brute-force scan whose cost depends on the data
and the query, and the two rows were separate runs. The stable comparison
is approximate-vs-exact within each row; the exact time drifting between
rows is machine noise, not a property of the index. The recall numbers are
the meaningful signal — 0.913 and 0.984 against the exact index's own
results.

</details>

**2. When would the residual 1.6% recall loss matter?**

<details>
<summary>Answer</summary>

Whenever the lost item is the one a user wanted — and since recall feeds
everything downstream, a missed candidate cannot be recovered by a better
ranker. The 0.984 is the price of the latency saving, and the decision is
whether that recall loss is acceptable for the request budget. The
ef-search dial is how the operator chooses the point on that curve.

</details>

## Next

Back to [stage 02](../), or to
[the queue you disable is the target you lose](../when-you-lose-a-queue/)
which reads the same stage's coverage-by-queue story.
