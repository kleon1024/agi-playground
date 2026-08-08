---
status: verified
level: applied
base: scratch
label: When the distillation blurs
verified: 2026-08-07
---

# The teacher's mistakes, copied

**Question:** [stage 63](../) distills the final ranker's score into the
pre-rank. This chapter asks what happens when the teacher's score is
noisy, and answers: distillation copies the teacher, mistakes included.

**Before this:** [stage 63 — cascade consistency](../).

## The noisy teacher, executed

The run ([record](runs/2026-08-07-distillation-blurs.md)) distills a clean
and a noisy teacher into the same pre-rank:

| teacher | distilled rank corr |
|---|---:|
| clean | 0.998 |
| noisy | 0.989 |

## The reading

Distillation copies the teacher, mistakes included. A final ranker whose
scores are themselves noisy — uncalibrated, freshly retrained, or
evaluated on a small slice — passes that noise to the pre-rank, and the
cascade's cheap stage inherits a defect the expensive stage should have
had alone. The fix is to distill a stable, calibrated teacher score, or to
gate which slices are trusted enough to teach.

## The fix and its trade

The fix is to distill a stable, calibrated teacher — averaged over time or
over slices — or to gate which slices are trusted enough to teach. The
executed read prices the noise transfer: a clean teacher gives a
distilled rank correlation of 0.998, a noisy one 0.989, and the difference
is not cosmetic, because the student is trained to reproduce the teacher
and ends up carrying the expensive stage's errors inside the cheap one.

The trade, named: the fix buys a cleaner student at the price of the
teacher's freshness and coverage. Averaging the teacher over time delays
the signal the student sees; gating slices shrinks the teaching set and
adds a rule that has to be maintained. And the acceptance metric has to
be the cascade's top-K recall at the cut — not the student's correlation
to the teacher, which measures agreement with a noisy target and can look
fine while the cut still loses the answer. The cheap alternative,
distilling whatever the final ranker emits today, passes its noise down
for free.

## Who owns the loop

- **The final-ranker team** owns the teacher's stability and calibration
  — the student inherits whatever this team ships as its score.
- **The pre-rank model team** owns the distillation and the gating rule:
  which slices teach is a training-time decision with a maintenance cost.
- **The evaluation team** owns the distilled pre-rank's top-K recall at
  the cut — the read that says the distillation preserved the answer, not
  just the correlation.

## Evidence boundary

The executed read over clean vs noisy teacher scores (illustrative,
deterministic). It demonstrates the noise transfer; real systems must
stabilize and calibrate the teacher and measure the distilled pre-rank's
top-K recall, not just its correlation to the teacher.

## Check your mental model

Answer each before opening it.

**1. Why does teacher noise survive distillation?**

<details>
<summary>Answer</summary>

Because the student is trained to reproduce the teacher's output. Noise in
the teacher's scores becomes part of the target the student fits, so the
cheap stage ends up carrying the expensive stage's errors.

</details>

**2. What is the practical fix?**

<details>
<summary>Answer</summary>

Distill a stable, calibrated teacher — averaged over time or slices — and
measure the cascade's top-K recall at the cut, which is the metric the
distillation exists to preserve.

</details>

## Next

Back to [stage 63](../). Why the cut matters at all: [only 11 of the final
top-20 survive a click-based cut](../when-top-k-is-not-preserved/).
