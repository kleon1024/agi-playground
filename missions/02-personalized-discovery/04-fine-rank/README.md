---
status: verified
level: applied
label: Fine-rank
verified: 2026-07-30
---

# Which objective are you actually ranking by?

**Goal:** predict click, completion, satisfaction, and dwell for the roughly
hundred candidates pre-rank kept — as calibrated probabilities, because the
next stage will do arithmetic on them, and arithmetic on numbers that are not
what they claim to be produces nonsense with a confident decimal point.

Pre-rank's job was to not lose the right items. Fine-rank's job is to score
them well enough that stage 05 can turn several scores into one. That
second requirement is why this stage predicts a vector instead of a single
number, and why getting each entry of that vector calibrated matters as much
as getting its ranking right.

**Before this:** [stage 03's cut](../03-pre-rank/) from about a thousand
candidates to about a hundred — small enough for this stage's heavier model
to afford, and already checked for the systematic misses a cheap proxy could
have hidden.

## 1. Why no single label is the objective

Optimize click alone and you get a system that rewards a misleading
thumbnail — it is cheap to log and abundant, but it is also the objective
most likely to reward that. Check completion instead and you learn whether
the content delivered on what the click promised. Look at satisfaction —
usually the rarest label, often collected from a post-session prompt — and
you get the closest proxy to "the user is glad this happened"; dwell time
sits somewhere between a real quality signal and an artifact of how long a
format takes to consume. None of them alone is what a discovery system is
actually trying to maximize; each is a different, imperfect view onto it —
the argument for predicting all four rather than picking the one that is
easiest to optimize.

## 2. A shared trunk, and the interference it invites

Sharing a trunk across related tasks and reading off task-specific heads is
not this stage's own idea — it is the architecture Caruana names and
analyzes in *"Multitask Learning"* (Machine Learning, 1997), including the
same mechanism this stage measures: gradients from an unrelated task's loss
can help or hurt a shared representation depending on how the tasks and their
losses are related and scaled.

`core/fine_rank.py` builds one small network: a shared trunk that turns raw
features into a hidden representation, and one linear head per task reading
off that same representation. Sharing is attractive because a feature useful
for predicting a click is usually also informative about completion — reuse
is free accuracy, and it is the only way the rarest label (satisfaction,
observed on a fraction of impressions) gets to benefit from the trunk that
the abundant click label spent most of its gradient shaping.

That sharing is not free by default. Every task's gradient flows back
through the same trunk weights, and whichever task's loss has the larger
magnitude pushes those weights around more, regardless of whether that task
is the one you most wanted the representation to serve. This is negative
transfer, and the usual place it hides is exactly where two properties
compound: a task with abundant, large-scale labels drowning out a task with
sparse, small-scale ones.

## 3. Where the interference actually comes from: sparsity and scale

`core/fine_rank.py` gives each task a different observation rate — click on
every impression, completion less often, satisfaction on a small fraction —
mirroring how these labels are actually collected in a live system. It also
gives dwell time a genuinely different scale: a bounded probability for the
other three tasks, raw seconds (up to a few hundred) for dwell. Train with
every task's loss summed unweighted, on dwell's raw scale, and the trunk sees
gradients from a single dwell example that can dwarf what an entire binary
task contributes — the network quietly specializes toward predicting dwell
well and everything else worse, not because dwell matters more, but because
its units happen to be bigger.

The fix demonstrated here is not an elaborate one: normalize dwell's target
onto roughly the same scale as the bounded tasks and give it a comparable
loss weight before summing. `train()`'s `balanced` flag switches between the
naive and the normalized version, holding everything else — architecture,
data, epochs, learning rate — fixed, so the comparison isolates exactly one
variable. Run it and compare each task's validation metric between the two
modes: a pairwise ranking accuracy for the three binary tasks, a correlation
for dwell. The sparsest task is usually the one with the most to gain from
fixing the scale mismatch, because it has the least of its own signal to
fall back on when the trunk is being pulled somewhere else.

## 4. Calibration: what "0.3" is supposed to mean

Check only ranking quality within one task and a model can get every
pairwise comparison right — rank the better item above the worse one, every
time — while its output numbers are systematically off, because a monotonic
transform of a score preserves its ranking. That failure stays invisible
until stage 05 combines *different* tasks' numbers arithmetically, because
`0.5 * p_click + 0.5 * p_satisfaction` is only a meaningful blend if both
numbers are honest probabilities on the same scale — a "0.3" from a
systematically overconfident head is not the same quantity as a "0.3" from a
well-calibrated one, even though they print identically.

`expected_calibration_error` in `core/fine_rank.py` measures this directly:
bucket predictions by confidence, and compare each bucket's average predicted
probability against its actual observed positive rate. A well-calibrated
model's buckets line up; a miscalibrated one does not, regardless of how
good its ranking looks. `fit_platt_scaling` is the fix demonstrated here — a
two-parameter logistic curve fit on held-out data, mapping the raw score onto
a corrected probability. Run the demo and compare ECE before and after: the
fix does not touch ranking at all, because a monotonic recalibration cannot
change pairwise order — it only makes the number honest enough for stage 05
to add it to something else.

## What a real run actually shows

```
                     naive    balanced
hidden=8, epochs=25
  satisfaction       0.651       0.706
  dwell              0.658       0.803
hidden=16, epochs=60
  satisfaction       0.644       0.664
  dwell             -0.080       0.809
```

The wider trunk makes naive weighting *worse*, not better: more capacity and
more training gives dwell's raw-seconds gradient more room to dominate the
shared trunk, and its naive correlation goes negative. Balancing recovers
0.803-0.809 regardless of trunk size — the fix, not the architecture, is
what stabilizes this. Calibration: Platt scaling drops the click head's ECE
from 0.0722 to 0.0552 (default trunk); the `prod/` isotonic-regression lane
fits the same held-out set to ECE 0.0000, which is overfitting to that set,
not a better calibration in general. Full output:
[`runs/2026-07-30-negative-transfer-and-calibration.md`](runs/2026-07-30-negative-transfer-and-calibration.md).

<!-- interactive: MultiTaskBalancing -->

## Reproducing

```bash
# naive vs. balanced multi-task training, plus calibration before/after
python core/fine_rank.py

# a wider trunk, trained longer
python core/fine_rank.py --hidden 16 --epochs 60

# the production lane: PyTorch/Adam training, isotonic regression calibration
PYTHONPATH=core python prod/torch_fine_rank.py
```

## Exercises

1. **Make the interference worse on purpose.** Remove the `0.3` loss weight
   on dwell in balanced mode (set it to `1.0`) while keeping the target
   normalized. Confirm the binary tasks degrade relative to the fully
   balanced run — normalization and weighting are two separate levers, and
   this isolates the second one.
2. **Find calibration's blind spot.** Fit Platt scaling, then check ECE
   separately for the top and bottom half of the predicted-probability range.
   A two-parameter logistic curve cannot fix every shape of miscalibration —
   confirm that for yourself rather than trusting the aggregate ECE number.
3. **Give satisfaction more data.** Raise its `OBSERVE_RATE` and compare its
   validation metric across naive and balanced modes at the new sparsity.
   The gap between the two modes should narrow — negative transfer is most
   damaging exactly where a task has the least of its own signal to recover
   with.
4. **Swap the calibration split for the validation split.** Fit Platt scaling
   on the same data used to measure ECE and compare the "improvement" against
   the honest, held-out version. The dishonest version will look better and
   prove nothing about the model.

## Next

[Stage 05 — the value tree](../05-value-tree/): this stage's four calibrated
numbers per item become the one scalar an item is actually ranked by — and
the arithmetic of that collapse is where product strategy stops being a
slide and starts being a formula.
