---
status: verified
level: applied
base: scratch
label: When the mid-range point lands
verified: 2026-08-06
---

# The third point that fills the range

**Question:** [stage 04](../) added a third endpoint (NR-ER, 12.8% positive)
midway on the imbalance spectrum between SR-MMP and NR-PPAR-gamma. This
chapter reads the recorded seeds and shows what the mid-range point does to
the three-point pattern.

**Before this:** [stage 04's third-endpoint run](../).

## The verdict, read

The run ([record](runs/2026-08-06-midrange-read.md)) reads the recorded
seeds:

| arm | mean ROC-AUC | seed spread |
|---|---:|---:|
| descriptor baseline | 0.6413 | 0.0011 |
| trained model | 0.6679 | 0.0227 |
| gap (model - descriptor) | +0.0265 | vs larger spread 0.0227 |

## Two readings

**The mid-range endpoint resolves — the model wins beyond its own spread.**
The gap (0.0265) clears the larger spread (0.0227), so NR-ER is a real
model win, not a no-result. The three-point pattern now has both a
descriptor win (SR-MMP), a no-result (NR-PPAR-gamma), and a model win
(NR-ER) — and the winner is not decided by scarcity alone.

**The variance pattern holds, and that is the part scarcity explains.**
NR-ER's model spread (0.0227) sits between SR-MMP's (0.0159) and
NR-PPAR-gamma's (0.0620), matching its mid-range positive count — variance
grows as positives shrink, monotonically across all three. What scarcity
does not explain is which arm wins: the descriptor baseline wins where the
model's noise is small and the model wins where it has enough positives to
beat its noise. The two directions are different claims, and the third
point is what separates them.

## The fix and its trade

The fix is the third data point as a discriminator: NR-ER's model spread
(0.0227) sits between the extremes (0.0159, 0.0620) and its margin
(+0.0265) clears that spread, which is what separates the two claims — the
variance direction is monotonic (scarcity -> noise), the gap direction is
not (who wins depends on endpoint structure). The trade is that the
discrimination is n=3 and directional: the chapter states the ceiling
itself, and no monotonicity claim here is a fitted or general one. The
third point buys the separation of the two questions at the cost of a
pattern that still cannot be extrapolated.

## Who owns this loop

- **The stage 04 owner** owns the mid-range endpoint run and its six
  committed seed JSONs.
- **The analysis owner** owns the two-direction read: variance
  monotonicity and gap non-monotonicity, each scoped to n=3.
- **The mission owner** owns the acceptance wording that treats the
  three-point pattern as "investigate further" rather than a law.

## Evidence boundary

The six committed seed JSONs (one endpoint, three seeds per arm, one
architecture, one scaffold split); it reads those artifacts and does not
re-train. The cross-endpoint monotonicity is n=3 and directional, as the
mission's own stage 05 states; nothing here extends beyond this panel.

## Check your mental model

Answer each before opening it.

**1. The model wins on NR-ER. Why does that not contradict the SR-MMP
descriptor win?**

<details>
<summary>Answer</summary>

Because the winner is endpoint-specific — the two endpoints differ in
positive count, scaffold split, and what each label measures. The mission's
three-endpoint pattern is not "one representation always wins"; it is that
scarcity decides whether a winner can be seen at all, while which arm wins
depends on enough data. Both findings coexist because they answer different
questions.

</details>

**2. What does the mid-range position add that the two extremes could
not?**

<details>
<summary>Answer</summary>

It completes the range. With only the two extremes, "variance grows as
positives shrink" had one interior point missing — a skeptic could argue
the relationship was an accident of the two endpoints. NR-ER's spread
(0.0227) lands between the extremes' (0.0159, 0.0620) on its mid-range
positive count, which is the difference between a directional pattern and a
coincidence at n=2.

</details>

## Next

Back to [stage 04](../), or to
[stage 05's cross-endpoint analysis](../../05-cross-endpoint-analysis/)
which reads the full three-endpoint pattern and its honest limits.
