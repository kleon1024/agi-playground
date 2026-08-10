---
status: verified
level: applied
base: scratch
label: When the recipe broke then fixed
verified: 2026-08-06
---

# The escape window is input-dependent

**Question:** [stage 03's real-speech run](../) retrained the codec on
LibriSpeech with the synthetic recipe. This chapter reads the recorded
sweep and asks why the recipe needed a change.

**Before this:** [stage 03's real-speech run](../) and its recorded sweep.

## The sweep, read

The run ([record](runs/2026-08-06-recipe-read.md)) reads the recorded
numbers:

| setting | outcome |
|---|---|
| lr=1e-3, 600 steps | collapses (silence tie) |
| lr=1e-3, 2000 steps | escapes by ~1400-1800, MSE 0.01306, 58/64 codes |
| lr=3e-3 | never escapes, MSE 0.02722, 3/64 codes |

Production seeds at 2000 steps: 0.01306 / 0.01369 / 0.01309, 51-63/64
codes.

## Two readings

**The same LR that escaped synthetic tones collapses on real speech at
600 steps.** The synthetic clips were simple enough that the recipe's
escape happened within the original budget; real LibriSpeech is harder,
and the codec is still in the silence local minimum at 600. Doubling the
step count to 2000 lets the escape happen (by ~1400-1800) — the fix is
time in the recipe, not a new mechanism.

**A higher LR never escapes — the opposite of the synthetic intuition.**
On synthetic tones, raising the LR helped escape; on real speech, lr=3e-3
keeps the codec at the silence tie with 3/64 codes. The escape window is
input-dependent, which is why the production run fixed the step count
rather than tuning the LR. The sweep is the evidence that "the recipe
that worked" was a property of the input, not the method.

## The fix and its trade

The fix is the controlled sweep at the fixed learning rate: at 600 steps
the recipe that escaped synthetic tones collapses on real speech (silence
tie, 1/64 codes), 2000 steps at the unchanged `lr=1e-3` escapes by ~step
1400-1800 (eval MSE 0.01306, 58/64 codes), and `lr=3e-3` never escapes
(0.02722, 3/64) — so the intervention is more time in the recipe, not a
new mechanism or a higher rate. The trade is that the escape window is
input-dependent: the recipe that worked was a property of the data-codec
pair, the higher-LR intuition that held on synthetic tones is ruled out on
real speech, and the production seeds (0.01306/0.01369/0.01309, 51-63/64
codes) carry that scoped meaning — they prove the step-count fix works on
this input, not that the recipe is universal.

## Who owns this loop

- **The recipe owner** owns the step-count fix and the sweep that proved
  it; the production run at 2000 steps is the measured consequence of the
  diagnostic, never the diagnostic itself.
- **The eval owner** owns the three-arm comparison (600, 2000, higher LR)
  and the production-seed protocol; the sweep is what makes "the fix is
  time, not rate" a measured claim.
- **The mission owner** owns the input-dependence boundary: the escape
  window is a property of the data-codec pair, so the recipe's transfer to
  harder input is tested (stage 04), never assumed.

## Evidence boundary

The recorded real-speech run (diagnostic sweep + three production seeds,
LibriSpeech dev-clean, CPU lane). It reads those artifacts; it does not
re-train.

## Check your mental model

Answer each before opening it.

**1. Why did the synthetic recipe not transfer unchanged?**

<details>
<summary>Answer</summary>

Because the escape from the silence local minimum depends on how hard the
input is. Synthetic tones are simple, so the decoder escapes within the
original 600-step budget; real speech has more structure, and the codec
is still trapped at 600. The recipe's "escape window" is a property of
the data-codec pair, which is why the step count had to grow.

</details>

**2. What does the lr=3e-3 failure rule out?**

<details>
<summary>Answer</summary>

The "higher LR always helps escape" hypothesis. On synthetic tones it
did; on real speech it never escapes (3/64 codes, silence tie). The
higher LR's larger early updates push the codec deeper into the local
minimum instead of out of it. The contrast is what makes the fix — more
steps at the original LR — the measured one, not the assumed one.

</details>

## Next

Back to [stage 03](../), or to
[the real network is where the realtime margin goes](../when-the-network-is-the-tail/)
which reads the same run's network half.
