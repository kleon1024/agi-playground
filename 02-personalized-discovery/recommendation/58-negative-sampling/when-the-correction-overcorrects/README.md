---
status: verified
level: applied
base: scratch
label: When the correction overcorrects
verified: 2026-08-07
---

# The formula is only as good as the ratio it is fed

**Question:** [stage 58](../) corrects the downsampled base rate. This
chapter asks what happens when the sampling ratio is misreported, and
answers: the correction inherits the error, which is why the ratio is
logged and the correction is checked against the observed base rate.

**Before this:** [stage 58 — negative sampling](../).

## The misestimated ratio, executed

The run ([record](runs/2026-08-07-correction-overcorrects.md)) applies the
correction with the right ratio and with a ratio off by half a decimal:

| assumed ratio | corrected p | bias vs true |
|---|---:|---:|
| exact ratio | 0.003 | -0.002 |
| ratio too low | 0.002 | -0.003 |
| ratio too high | 0.005 | 0.000 |

## The reading

If operations believes the sample ran at 1:10 and it actually ran at 1:20,
the corrected probabilities land half a decimal too high — the ratio error
passes straight through the formula. Calibrating against the observed base
rate after correction is the check that catches a wrong ratio, which is why
sampling ratios are logged at sampling time, not assumed at training time.
The correction is a formula; the formula's input is an operational fact.

## The fix and its trade

The fix is two operational habits, not a model change: log the sampling
ratio at the moment it is applied, and after correction compare the
resulting probabilities to the observed base rate on a validation slice.
The executed read shows why the check exists — with the exact ratio the
corrected p is 0.003 (true 0.005); with an assumed 1:10 against a real
1:20 the corrected p lands half a decimal off, and the formula has no way
to know it is wrong.

The trade is that the fix converts a silent model error into an explicit
operational alert, at the price of owning the alert. The base-rate
comparison needs a defined tolerance and a slice definition, and it will
fire on calibration noise if the tolerance is set too tight — so the
threshold is a real decision, not a default. The alternative — trust the
formula because the ratio "must be right" — is the failure mode itself:
the correction cannot detect its own input error, and nothing downstream
will.

## Who owns the loop

- **The sample and operations team** owns the ratio log: the real
  sampling rate is recorded at sampling time, which is the only place it
  is knowable.
- **The model team** owns applying the correction and the per-slice
  comparison to the observed base rate — the alert fires on a mismatch
  between corrected probabilities and the measured rate.
- **The evaluation team** owns the tolerance and the slice definition for
  the alert, and the re-check when the sampling strategy changes (a new
  ratio is a new contract, not a new number).

## Evidence boundary

The executed read over declared ratio errors (illustrative,
deterministic). It demonstrates the sensitivity; real systems must compare
the corrected probabilities to the observed base rate per slice and alert
when they diverge.

## Check your mental model

Answer each before opening it.

**1. Why does the correction not fix a wrong ratio?**

<details>
<summary>Answer</summary>

Because it divides by the assumed ratio. If the assumption is wrong, the
correction scales every probability by the wrong factor — it cannot detect
its own input error.

</details>

**2. What is the cheapest check that catches it?**

<details>
<summary>Answer</summary>

Compare the corrected probabilities to the observed base rate on a
validation slice. If they disagree by more than the calibration noise, the
ratio was mislogged; the fix is operational (record the real sampling rate),
not another model tweak.

</details>

## Next

Back to [stage 58](../). Why downsampling exists at all: [at 1:1000 the
negatives own 99% of the gradient](../when-the-negative-rate-is-extreme/).
