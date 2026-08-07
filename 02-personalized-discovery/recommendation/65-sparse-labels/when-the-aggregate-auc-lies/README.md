---
status: verified
level: applied
base: scratch
label: When the aggregate AUC lies
verified: 2026-08-07
---

# With two positives the interval spans chance, and only label supply narrows it

**Question:** [stage 65's audit](../) reports a cold-item slice whose 5-95%
interval spans chance. This chapter turns that into arithmetic: how many
positives does a slice need before its AUC interval stops spanning chance?

**Before this:** [stage 65 — the aggregate AUC is a dense-slice
number](../), where the per-slice interval became the guardrail. This
detour is the interval's arithmetic, read at increasing label counts.

## The interval, executed

The run ([record](runs/2026-08-07-aggregate-lies-read.md)) subsamples the
dense head slice at increasing positive counts and reads the bootstrap
10-90% interval at each size:

| positives | 10-90% interval | width |
|---|---:|---:|
| 2 | 0.000 .. 1.000 | 1.000 |
| 5 | 0.250 .. 1.000 | 0.750 |
| 10 | 0.222 .. 1.000 | 0.778 |
| 20 | 0.316 .. 1.000 | 0.684 |
| 30 | 0.414 .. 0.931 | 0.517 |

## The reading

With two positives the interval is [0.000, 1.000] — the read cannot tell
a coin flip from a perfect ranker. The interval only starts to narrow
around 20-30 positives (width 0.684 to 0.517), and nothing a model team
does changes that: no architecture, loss, or gating choice adds
information that the labels do not contain. The aggregate AUC is not
lying — it is measured where the labels are. The defect is reporting it
alone; the fix is a data decision (longer window, surrogate labels,
exposure data) gated on the slice's interval, never the point estimate.

## Evidence boundary

The executed synthetic read over the dense head slice subsampled to
declared positive counts (illustrative, deterministic, single seed,
120 bootstrap draws per size). It demonstrates the interval shape; real
systems must read the interval at the production slice's actual label
velocity and choose the label-supply fix from it.

## Check your mental model

Answer each before opening it.

**1. Why does the interval width stop shrinking around 20-30
positives?**

<details>
<summary>Answer</summary>

Because AUC's variance falls with the positive count, and the marginal
narrowing shrinks as the count grows. The executed read shows width 1.000
at 2 positives dropping to 0.684 at 20 and 0.517 at 30 — the curve is
steep at the bottom and flattens. The interval is a label-supply fact,
which is why the fix is a data decision.

</details>

**2. Is the aggregate AUC wrong?**

<details>
<summary>Answer</summary>

No — it is exactly the AUC of the rows that have labels, dominated by the
dense slices. It is not wrong, it is uninformative about the sparse slice.
The defect is treating it as the summary for slices it does not measure.

</details>

## Next

Back to [stage 65](../), where the density report makes the same point
per slice — now with the arithmetic that explains the guardrail.
