---
status: verified
level: applied
base: scratch
label: The three MET items
verified: 2026-08-06
---

# A failing verdict can still be a disciplined one

**Question:** [mission 09's report](../) returned NOT MET. This chapter
reads the recorded report and asks what the verdict still established.

**Before this:** [mission 09's report](../) and its recorded outcome.

## The items, read

The run ([record](runs/2026-08-06-three-met.md)) reads the recorded
report:

| item | result |
|---|---|
| trained model beats descriptor baseline | NOT MET (gap 0.0830, spread 0.0159) |
| scaffold overlap measured | 0.0 |
| every stage has a runs entry | held |
| does_not_prove boundary stated | held |

## Two readings

**The headline is a clear loss, not a near-tie.** The descriptor baseline
(0.8142) beats the trained model (0.7312) by 0.0830, roughly 5x the
larger seed spread. The report calls it plainly: the model is clearly
worse on SR-MMP, and the honest answer is that the descriptor baseline is
the better model to ship.

**Three of four acceptance items hold, and that is part of the verdict.**
The scaffold overlap is measured (0.0), every stage has a real runs entry,
and the does_not_prove boundary is stated in both places. A NOT MET on
the headline does not mean the mission was sloppy — it means the
discipline held while the result was negative, which is exactly what the
declared contract is for.

## Evidence boundary

The recorded outcome report (stage 00/01 numbers read mechanically). It
reads that artifact; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why is the loss reported as "clearly worse" rather than "no
result"?**

<details>
<summary>Answer</summary>

Because the mission's rule is "a gap smaller than run-to-run spread is no
result" — and the gap (0.0830) is far larger than the larger spread
(0.0159). A no-result is a margin inside the noise; this is a margin
outside it, so the honest label is a clear loss, not an inconclusive one.
The rule is what distinguishes the two readings.

</details>

**2. What does the scaffold-overlap item add to the negative verdict?**

<details>
<summary>Answer</summary>

It rules out the most common way such a headline is fake: leakage. If the
held-out structures were in training, the descriptor's win could be
memorization. The measured 0.0 overlap closes that door, so the NOT MET
is a real generalization finding — the baseline genuinely beats the
model on structures it has never seen.

</details>

## Next

Back to [mission 09's report](../), or to
[the baseline that refused to lose](../when-the-baseline-refuses-to-lose/)
which reads the same report's gap structure.
