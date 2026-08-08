---
status: verified
level: applied
base: scratch
label: The model's first win
verified: 2026-08-06
---

# The mid-range endpoint gives the model its first clean win

**Question:** [stage 04's third endpoint](../) ran the comparison on NR-ER,
the midpoint of the imbalance spectrum. This chapter reads the recorded
seeds and asks what the result adds to the mission.

**Before this:** [stage 04's third endpoint](../) and its recorded seeds.

## The win, read

The run ([record](runs/2026-08-06-model-win.md)) reads the recorded
seeds:

| arm | mean ROC-AUC | spread |
|---|---:|---:|
| descriptor | 0.6413 | 0.0011 |
| model | 0.6679 | 0.0227 |
| margin | +0.0265 | vs larger spread 0.0227 |

## Two readings

**The model wins beyond its own spread — the first model win in the
mission.** The margin (+0.0265) clears the larger spread (0.0227), so
NR-ER is a real model win, not a no-result. The three-endpoint pattern now
has both a descriptor win (SR-MMP), a no-result (NR-PPAR-gamma), and a
model win (NR-ER): the winner is not decided by scarcity alone.

**The mid-range point is what separates the two questions.** At the
midpoint of the imbalance spectrum, the model's spread (0.0227) sits
between the extremes' (0.0159, 0.0620), and its win says the trained
model can beat the descriptor when it has enough positives. Scarcity
decides where a winner can be seen; the third point is what shows that
who wins depends on enough data.

## The fix and its trade

The fix is adding the mid-range endpoint to the comparison: with only
SR-MMP and NR-PPAR-gamma, the mission could not separate "scarcity decides
where a winner can be seen" from "who wins." NR-ER (12.8% positive, 628
train positives) resolves the model's first clean win — margin +0.0265
clears the larger spread 0.0227 — which is the third point that breaks the
confound. The trade is that the win is endpoint-specific: the same
architecture loses on SR-MMP, so the chapter cannot claim the model
"got better," only that this endpoint has enough positives for its signal
to beat its noise.

## Who owns this loop

- **The mission owner** owns the endpoint-selection decision — the
  midpoint was chosen deliberately, not sampled — and the three-point
  pattern it produces.
- **The eval owner** owns the seed protocol and the win-beyond-spread bar
  that decides whether +0.0265 is a result or a no-result.
- **The report owner** owns the honest framing: a first win that is
  explicitly not a general one, with the endpoint conditions stated beside
  the number.

## Evidence boundary

The recorded third-endpoint seeds (three per arm, one scaffold split, one
architecture). It reads those artifacts; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why does the model win here when it lost on SR-MMP?**

<details>
<summary>Answer</summary>

Because the endpoints differ in more than balance. SR-MMP and NR-ER have
different scaffolds, different label semantics, and different split
shifts — the model's win on NR-ER is endpoint-specific, not a
contradiction of the SR-MMP loss. The mission's pattern is not "one
representation always wins"; it is that the winner depends on enough data
and the endpoint's own structure.

</details>

**2. What does the mid-range position add that the extremes could not?**

<details>
<summary>Answer</summary>

It completes the range. With only the two extremes, "variance grows as
positives shrink" had one interior point missing, and a skeptic could call
it an accident of the endpoints chosen. NR-ER's spread (0.0227) lands
between the extremes' on its mid-range positive count — the difference
between a directional pattern and a coincidence at n=2.

</details>

## Next

Back to [stage 04](../), or to
[the third point that fills the range](../when-the-mid-range-point-lands/)
which reads the same stage's pattern side.
