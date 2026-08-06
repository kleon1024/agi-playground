---
status: verified
level: applied
base: scratch
label: The margin vs the ceiling
verified: 2026-08-06
---

# The remaining gap belongs to the codec, not the sequence model

**Question:** [stage 02's generation model](../) beats frame-repeat by
37.2%. This chapter reads the recorded runs and asks where the remaining
gap to perfect reconstruction lives.

**Before this:** [stage 02's generation model](../) and its recorded runs.

## The numbers, read

The run ([record](runs/2026-08-06-margin-ceiling.md)) reads the recorded
JSONs:

| seed | LM completion | oracle (true tokens) | frame-repeat |
|---|---:|---:|---:|
| 0 | 0.0804 | 0.0779 | 0.1281 |
| 1 | 0.0865 | 0.0865 | 0.1281 |
| 2 | 0.0882 | 0.0882 | 0.1281 |

## Two readings

**The LM beats frame-repeat decisively on every seed.** The margin
(0.0430 mean) is 5.5x the seed spread (0.0078), and the LM completion
sits within 3.2% of the oracle — the best the codec could do even with
the true future tokens. The generation is not the bottleneck.

**The remaining gap is the codec's reconstruction fidelity.** Because the
LM lands near the oracle, most of the distance from frame-repeat to
perfect reconstruction is the tokenizer's own blur — the oracle itself is
at 0.0779-0.0882, not zero. The anatomy is: sequence model fixed, codec
blur dominates. That is why stage 04's longer sequences and stage 05's
multi-object both conclude "the tokenizer, not compute, is the binding
constraint."

## Evidence boundary

The recorded generation JSONs (three seeds, 150 eval clips, one recipe).
It reads those artifacts; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. What does the oracle number actually bound?**

<details>
<summary>Answer</summary>

The codec's ceiling. The oracle runs the true future tokens through the
decoder — no sequence prediction involved — so its MSE (0.0779-0.0882) is
what the codec alone can reconstruct. The LM matching it means the
sequence model has essentially nothing left to improve; the gap to zero
is the codec's reconstruction blur, not the generation's fault.

</details>

**2. Why does the margin-vs-spread comparison matter here?**

<details>
<summary>Answer</summary>

Because it is what makes the win a result instead of a seed-lucky number.
The margin (0.0430) is 5.5x the run-to-run spread (0.0078), so the
generation beats frame-repeat beyond what seed noise could produce. The
same rule the whole repository uses for a continuous metric is what
turns the three rows into a verdict.

</details>

## Next

Back to [stage 02](../), or to
[when the tokens are wrong but the frames still reconstruct](../when-wrong-tokens-still-reconstruct/)
which reads the same runs' token-vs-pixel story.
