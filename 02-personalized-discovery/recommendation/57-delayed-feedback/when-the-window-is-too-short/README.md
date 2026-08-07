---
status: verified
level: applied
base: scratch
label: When the window is too short
verified: 2026-08-07
---

# The window that trades labels for rows

**Question:** [stage 57](../) fixes the young-snapshot case. This chapter
asks how the label window itself should be chosen, and answers: it is a
hyperparameter, because a short window buys rows at the price of false
negatives and a long window buys clean labels at the price of volume.

**Before this:** [stage 57 — delayed feedback](../).

## The window sweep, executed

The run ([record](runs/2026-08-07-window-too-short.md)) sweeps the label
window over the same synthetic stream:

| window (days) | train rows | false negatives | conv AUC |
|---|---:|---:|---:|
| 1 | 4,754 | 728 | 0.462 |
| 3 | 4,498 | 421 | 0.695 |
| 7 | 4,001 | 122 | 0.705 |
| 14 | 3,112 | 11 | 0.690 |
| 30 | 1,217 | 0 | 0.702 |

## The reading

The one-day window has the most training rows and the most false negatives —
every converter past day one is labeled negative — and it halves the AUC. The
30-day window has clean labels and a quarter of the rows, and the gain
plateaus. AUC peaks in the middle, where label quality and volume balance.
That is why the window is tuned like a hyperparameter and logged with the
model, not picked by convention: the right choice depends on the conversion
latency distribution of the specific funnel.

## Evidence boundary

The executed sweep over a synthetic conversion-delay distribution
(illustrative, deterministic). It demonstrates the trade; real systems must
measure the actual conversion-delay distribution per funnel and re-check the
window when the product changes it.

## Check your mental model

Answer each before opening it.

**1. Why does the short window halve the AUC despite having the most rows?**

<details>
<summary>Answer</summary>

Because its extra rows are mostly false negatives: every converter past day
one is labeled negative, so the model fits a world in which conversions
barely happen. Rows that lie are worse than no rows.

</details>

**2. Why does AUC plateau instead of keep rising with the window?**

<details>
<summary>Answer</summary>

Because beyond the conversion latency mass, extending the window adds no
new correct labels — it only delays the training set and drops rows whose
conversions were already counted. The plateau is where marginal label
quality meets marginal volume.

</details>

## Next

Back to [stage 57](../). The freshness face of the same trade: [a fresh
snapshot is mostly in-flight rows](../when-freshness-fights-correctness/).
