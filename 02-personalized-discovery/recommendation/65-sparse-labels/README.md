---
status: verified
level: applied
base: scratch
label: Sparse labels
verified: 2026-08-07
---

# The aggregate AUC is a dense-slice number

**Question:** the buy objective's labels are rare — 119 train positives in
the head slice, 74 for cold users, 5 for cold items. This stage asks what
the model can learn on a slice with five positives, and which fix layer
actually moves the number: sample and label construction, model
structure, or delay-aware training?

**Before this:** [stage 56 — entire-space funnel](../56-entire-space-funnel/)
for why a sparse target trained on the wrong population is biased,
[stage 57 — delayed feedback](../57-delayed-feedback/) for why the label
window censors purchases, [stage 61 — multi-task conflict](../61-multi-task-conflict/)
for the shared-trunk mechanism, and [stage 05 — the value
tree](../../shared/05-value-tree/) for why every probability must be
honest.

## The three fixes, executed

The run ([record](runs/2026-08-07-sparse-labels.md)) trains three variants
on the cold (non-head) rows — a buy-only model from scratch, a shared
trunk that also fits clicks, and a surrogate-trained model using
"engaged" as the buy proxy:

| variant | cold-slice buy AUC |
|---|---:|
| cold-only, from scratch | 0.678 |
| shared trunk (click+buy) | 0.780 |
| surrogate (engaged) | 0.696 |

## The mechanism, named

The density report ([record](runs/2026-08-07-sparse-labels-audit.md))
shows the problem: head 30 positives in 659 test rows (0.0455), cold-user
21 in 681 (0.0308), cold-item 2 in 260 (0.0077). The aggregate buy AUC of
0.769 is a head-and-cold-user number; the cold-item slice's 5-95%
interval spans chance ([0.500, 0.957]). Five train positives cannot shape
a ranker, and no modeling choice changes that — only the label supply
does. The fixes act on three layers: sample and label construction (a
longer window, a surrogate hierarchy, exposure data), model structure
(warm start and transfer, shared-trunk balancing), and delay-aware
training (window with fake-negative correction). Each buys signal at a
measured cost: the surrogate fills the empty slice but inflates every
predicted probability, and warm start only wins when the source task is
aligned.

## How you find it: the density report and interval read, executed

The case-finding audit ([record](runs/2026-08-07-sparse-labels-audit.md))
emits the per-slice label-density report, the delay distribution of
purchase labels, and per-slice buy AUC with bootstrap 5-95% intervals for
the shared model:

| slice | rows | positives | rate | AUC | 5-95% interval |
|---|---:|---:|---:|---:|---:|
| head | 659 | 30 | 0.0455 | 0.752 | 0.678-0.822 |
| cold-user | 681 | 21 | 0.0308 | 0.745 | 0.667-0.823 |
| cold-item | 260 | 2 | 0.0077 | 0.773 | 0.500-0.957 |

Delay distribution: median 0.39d, p95 0.64d, with 11% of purchases still
in flight at the 0.6d snapshot. The verdict is THE AGGREGATE AUC IS A
DENSE-SLICE NUMBER — report per slice with its interval, and gate the
cold-item slice on a different signal because its own labels cannot
decide anything yet. The delay axis is the known industry fact behind the
window: in display advertising, about 50% of conversions occur after 24
hours (Chapelle, Manavoglu and Rosales, "Modeling Delayed Feedback in
Display Advertising", KDD 2014, DOI 10.1145/2623330.2623634), so a short
label window is a structural source of sparsity, not a logging bug. The
surrogate and fake-negative fixes are the published routes: Ktena et al.
("Addressing Delayed Feedback for Continuous Training with Neural
Networks in CTR prediction", RecSys 2019) weight and calibrate the
fake-negative labels of a continuous-training system, and Yasui et al.
("A Feedback Shift Correction in Predicting Conversion Rates under
Delayed Feedback", WWW 2020, arXiv:2002.02068) correct the feedback shift
with an importance weight, which is the surrogate's cleaner cousin.

## Who owns the loop

Sparsity is a label-supply problem that spans three teams:

- **The sample and label team** owns the supply: the label window, the
  surrogate label hierarchy, and the exposure data that fills the empty
  slice. It owns the density report, and the surrogate-bleed detour is
  its failure mode.
- **The model team** owns the structure: the shared-trunk balance, the
  warm-start source selection, and the content embeddings that bridge the
  cold slice. It owns the transfer test, and the warm-start detour is its
  failure mode.
- **The evaluation team** owns the guardrail: per-slice density with
  intervals, never the aggregate alone. The interval verdict is its
  signal, and it holds the gate until the sparse slice's own numbers can
  decide something — or the product explicitly accepts the surrogate's
  probability cost.

When the ownership is implicit, the dashboard shows the aggregate buy
AUC, the model team tunes it, and nobody owns the cold-item slice — so a
model ships with five-positive confidence, and the cold-item rows are
averaged into a number that never had them.

## Why this belongs in the mission

The mission's funnel multiplies probabilities, and stage 05's value tree
feeds them into money decisions. A slice whose number was never real is
the same failure as stage 56's wrong population and stage 57's censored
window, one level down: the model is confident exactly where the labels
were absent. This stage is where sparsity stops being a data complaint
and becomes a per-slice evaluation contract.

## Evidence boundary

The executed synthetic read over 8,000 rows with declared per-slice label
rates and delay (illustrative, deterministic, single seed). It
demonstrates the density report, the interval behavior, and the three fix
layers; real systems must measure production label velocity per slice
(users, items, surfaces) and gate decisions on the slice's interval, not
on a surrogate of the aggregate.

## Check your mental model

Answer each before opening it.

**1. Why is the cold-item slice's interval the guardrail, and not its
AUC?**

<details>
<summary>Answer</summary>

Because with two positives, the AUC point estimate is a number drawn from
an interval that spans chance — the read cannot tell a coin flip from a
perfect ranker. The interval is the honest summary of the slice's
evidence; the point estimate is theater. The fix is therefore a data
decision (labels, surrogate, exposure) gated on the interval, not a model
decision gated on the AUC.

</details>

**2. What makes a warm-start source aligned?**

<details>
<summary>Answer</summary>

Not the task name — the signal distribution. Pre-training on clicks and
fine-tuning on cold rows loses to scratch (0.659 versus 0.740) because
the click trunk is activity-dominated. Pre-training on the dense head
slice's buy task wins (0.786) because it shares buy's drivers. The
transfer test is source-task alignment, measured per slice.

</details>

## Next

Three executed failure faces: the arithmetic of the interval — [with two
positives the AUC interval spans chance, and it only narrows as the label
supply grows](when-the-aggregate-auc-lies/) (width 1.000 at k=2 to 0.517
at k=30); the surrogate's price — [it fills the empty slice but inflates
the predicted purchase rate about 11x and loses on the labels that
matter](when-the-surrogate-label-bleeds/) (0.0395 predicted versus 0.0036
true); and the transfer test — [warm start is not automatic: the
misaligned click trunk loses to scratch, the aligned head-slice buy trunk
wins](when-warm-start-beats-from-scratch/) (0.659, 0.740, 0.786).
