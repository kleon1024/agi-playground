---
status: verified
level: applied
base: scratch
label: When the baseline refuses to lose
verified: 2026-08-06
---

# The baseline that refused to lose: a decisive gap, read honestly

**Question:** [mission 09's report](../) returned `NOT MET` — the descriptor
baseline beats the trained SMILES model on SR-MMP. The difference between a
decisive loss and a near-tie matters for what the mission can claim, and
this chapter reads the verdict structure from the recorded numbers.

**Before this:** [mission 09's outcome report](../) and
[the baseline-holds chapter](../../01-descriptor-baseline-and-model/when-the-baseline-holds/).

## The verdict, read

The run ([record](runs/2026-08-06-baseline-report.md)) tabulates the recorded
report's means and spreads:

| arm | mean ROC-AUC | seed spread |
|---|---:|---:|
| descriptor baseline | 0.8142 | ±0.0010 |
| trained model | 0.7312 | ±0.0159 |
| gap (descriptor - model) | +0.0830 | vs larger spread 0.0159 |

## Two readings

**The gap is 5x the larger spread: a decisive loss, not a near-tie.** The
descriptor baseline wins by 0.0830 while the noisier arm — the trained
model — varies by only 0.0159 seed to seed. The win clears the mission's own
"a gap smaller than run-to-run spread is no result" bar by a wide margin,
so this is not a coin flip dressed up as a finding. "The baseline refused to
lose" means the loss is structural at this scale, not something a different
random seed would erase.

**The scaffold-checked split makes the win a real generalization, not a
leak.** The held-out structures were not in training (stage 00 measured
scaffold overlap at 0.0), so the baseline's edge survives the one test that
would have invalidated it. The honest reading is that a ten-number
physicochemical summary of a molecule generalizes better than this
from-scratch character model at this data size — the opposite of the
headline most training pipelines would want, and exactly the answer
`mission.yaml` was written to allow.

## The fix and its trade

The fix is the spread-relative verdict rule the mission declared before
running: a gap smaller than run-to-run spread is no result, and a gap
larger is decisive. The trade is that decisiveness is a property of this
comparison at this data size — the descriptor baseline wins by 0.0830
against a 0.0159 spread (5x), so the loss is structural here, but the same
rule would call a narrower margin a no-result even when a real effect
exists. The rule buys an honest headline (the baseline refused to lose) at
the cost of conservatism: it cannot distinguish "no effect" from "effect
too small for this run to see."

## Who owns this loop

- **The report owner** owns the gap-vs-spread bar and the verdict
  structure: NOT MET is read from the recorded means and spreads, never
  from the trained model's nominal presence.
- **The dataset owner** owns the measured 0.0 scaffold overlap that turns
  the baseline's win into a generalization claim instead of a leak.
- **The mission owner** owns the `does_not_prove` boundary that stops this
  chapter from extending one endpoint's verdict to aging biology or drug
  efficacy.

## Evidence boundary

The recorded outcome report (2026-08-01), one endpoint, one scaffold split,
one descriptor set, one architecture. It tabulates the recorded verdict and
does not re-train. Nothing here extends to other endpoints — that is stage
03/04's job — and nothing here is evidence about aging biology or drug
efficacy, per `mission.yaml`'s `does_not_prove`.

## Check your mental model

Answer each before opening it.

**1. The trained model is the "smart" arm. Why does the chapter call its
loss structural rather than bad luck?**

<details>
<summary>Answer</summary>

Because the loss exceeds the model's own run-to-run spread by 5x. A near-tie
would sit inside that spread and be reported as no result; this gap is
beyond it, and the baseline is nearly deterministic (±0.0010). The seed
spread is the estimate of what a different random draw could change, and the
gap dwarfs it — the definition of a repeatable result, here a repeatable
loss.

</details>

**2. Why does the scaffold split belong in the reading of a loss?**

<details>
<summary>Answer</summary>

Because the most common way a "simple baseline beats a neural model"
headline turns out to be fake is leakage: the held-out structures were
already in training, so the baseline wins by memorization. The scaffold
split closes that door (overlap 0.0), which is what makes the loss
meaningful — the baseline genuinely generalizes better on structures the
model has never seen.

</details>

## Next

Back to [mission 09's report](../), or forward to
[the second endpoint](../../03-second-endpoint/) which tests whether this
verdict generalizes beyond SR-MMP.
