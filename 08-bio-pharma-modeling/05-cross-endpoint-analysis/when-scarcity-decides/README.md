---
status: verified
level: applied
base: none
label: When scarcity decides
verified: 2026-08-06
---

# What does scarcity decide, and what does it not?

**Question:** [stage 05](../) checked two directions across the mission's
three endpoints: does model variance grow as positives shrink, and does the
win/loss gap follow the same line? This chapter reads the recorded analysis
and separates the part the scarcity hypothesis explains from the part it
does not.

**Before this:** [stage 05's cross-endpoint analysis](../) and its recorded
directions.

## The grid, read

The run ([record](runs/2026-08-06-scarcity-grid.md)) lays out the recorded
numbers:

| endpoint | train positives | model spread | gap | verdict |
|---|---:|---:|---:|---|
| SR-MMP | 689 | 0.016 | -0.083 | descriptor wins |
| NR-PPAR-gamma | 118 | 0.062 | +0.004 | inconclusive |
| NR-ER | 628 | 0.023 | +0.027 | model wins |

variance vs positive count: **monotonic decreasing**. Gap vs positive
count: **not monotonic**.

## Two readings

**Scarcity decides where a winner can be seen, not who wins.** The model's
variance grows monotonically as positives shrink — PPAR's 118 positives
carry a 0.062 spread (4x SR-MMP's), and that variance is exactly what
swallows its 0.004 gap into "inconclusive." Scarcity explains the no-verdict
row. It does not explain the winners: SR-MMP and NR-ER both resolve beyond
spread, one each way, with positive counts that bracket PPAR's. The gap
direction is explicitly not monotonic, so the hypothesis is about noise, not
about which representation wins.

**The monotonicity check is n=3 and directional.** The recorded note says
so itself: no correlation coefficient is computed or implied. The finding
is a legible pattern (scarcest -> noisiest -> no verdict), not a fitted
claim — which is the honest ceiling of a three-endpoint comparison, and why
the mission's acceptance treats it as a pattern to investigate, not a law.

## The fix and its trade

The fix is delimiting the scarcity hypothesis instead of letting it absorb
the whole result: scarcity explains the no-verdict row (PPAR's 118
positives carry a 0.062 spread that swallows its 0.004 gap), and it does
not explain the winners (SR-MMP and NR-ER resolve one each way, with
counts that bracket PPAR's). The trade is that the delimitation leaves the
winner question open — the chapter answers "where a winner can be seen"
and explicitly does not answer "who wins and why," which needs endpoints
beyond this panel. The fix buys a precise hypothesis at the cost of an
unfinished one.

## Who owns this loop

- **The analysis owner** owns the grid and the two-direction read,
  including the "not monotonic" verdict on the gap.
- **The dataset owner** owns the positive counts and the scaffold-split
  records the grid reads; the scarcity numbers are measured, not assumed.
- **The report owner** owns the scoped conclusion: the hypothesis is about
  noise, not about which representation wins, and that boundary stays in
  the mission's conclusions.

## Evidence boundary

The recorded cross-endpoint JSON, three endpoints, three seeds each. It
reads the directions and their scope (n=3, direction only); it does not
compute a correlation, does not add endpoints, and does not claim the
scarcity pattern is causal.

## Check your mental model

Answer each before opening it.

**1. Why is the inconclusive verdict on the scarcest endpoint, not the
weakest one?**

<details>
<summary>Answer</summary>

Because the verdict depends on variance, not on the model's mean. PPAR's
model spread (0.062) is large enough that its 0.004 gap over the baseline
is inside the noise, so no winner can be claimed. The scarcity hypothesis
explains this: fewer positives mean noisier AUC estimates, so the scarcest
endpoint is where a winner becomes invisible — regardless of which arm is
actually better.

</details>

**2. The gap direction is not monotonic. What does that leave the scarcity
hypothesis explaining?**

<details>
<summary>Answer</summary>

It leaves it explaining variance and verdict visibility only, not the
winner. The gaps do not order with positive count (SR-MMP and NR-ER resolve
opposite ways at similar counts), so scarcity predicts where a verdict is
possible, not which representation is right. That is the honest scope of a
three-point directional check, and it is why the mission frames it as a
pattern to investigate rather than a fitted law.

</details>

## Next

Back to [stage 05's cross-endpoint analysis](../),
or to [the mission report](../../02-report/) where the full chain's
acceptance verdict is held.
