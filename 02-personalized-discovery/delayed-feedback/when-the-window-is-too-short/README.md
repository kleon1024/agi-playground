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

## The fix and its trade

The fix is to treat the label window as a hyperparameter and log it with
the model, because it is a volume-versus-correctness knob with a measured
sweet spot. The sweep on the same stream shows the whole curve: a 1-day
window keeps 4,754 rows and 728 false negatives and halves the AUC to
0.462; the 7-day window lands at 0.705; the 30-day window has clean labels
but a quarter of the rows (1,217) and no better AUC (0.702). AUC peaks in
the middle because that is where label quality meets volume.

The trade, named: every window choice pays one direction and earns the
other. A short window buys the freshest, largest training set at the price
of rows that lie about conversions that have not happened yet; a long
window buys clean labels at the price of volume and staleness. The plateau
beyond the conversion-latency mass means the window is not "longer is
better" — it is a per-funnel decision that has to be re-made when the
product changes the conversion latency distribution.

## Who owns the loop

- **The label pipeline team** owns the window decision and the measured
  conversion-delay distribution it is chosen against. The window is a
  label-pipeline contract, not a model-team default.
- **The model team** owns logging the window with the model and its
  runs record, so a later AUC change is attributable to the label
  contract and not to the model.
- **The evaluation team** owns the window sweep and the re-check: when
  the funnel changes, the sweep is re-run and the plateau re-located
  before anyone tunes the model on the old optimum.

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
