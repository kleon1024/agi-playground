---
status: verified
level: applied
base: scratch
label: When the policy borrows luck
verified: 2026-08-07
---

# The log measures quality under the policy, not quality

**Question:** [stage 45's loop](../) entrenches what it shows. This
chapter asks how the log misreads the items it did show and answers: an
item served in a featured slot borrows the slot's luck, so the naive log
calls it better than it is — and the correction only works while the
propensities that produced the log are still the current ones.

**Before this:** [stage 45 — feedback loops](../) and its executed
exposure run, plus [stage 59 — exposure bias](../../../recommendation/59-exposure-bias/)
for the propensity-weighting family this detour's fix belongs to.

## The borrowed luck, executed

The run ([record](runs/2026-08-07-policy-borrows-luck-read.md)) serves
two items with the same true CTR (0.030) 200 times each, one in a
featured slot that doubles clicks, one in a low position that halves
them:

| item | position multiplier | clicks | naive ctr | IPS (true) | IPS (stale) |
|---|---:|---:|---:|---:|---:|
| A | 2.0 | 12 | 0.060 | 0.030 | 0.060 |
| B | 0.5 | 3 | 0.015 | 0.030 | 0.015 |

## The reading

The naive log says A converts at 0.060 and B at 0.015. Neither is true:
A borrowed the featured slot's luck, B paid for its low position.
Inverse propensity weighting divides each click by the probability the
policy gave that row, which returns 0.030 for both — but only when the
propensity is the one that produced the log. The stale column is the
feedback-loop twist: the serving policy changes, the stored propensities
describe a policy that no longer exists, and the correction reproduces
the bias it was meant to remove.

The consequence for the loop is direct: an item that ranks well because
it was shown well gathers more exposure and entrenches, exactly the
mechanism stage 45's main run measures. The log is the only place the
luck is recorded, so exploration must be logged with the policy version
that produced it — propensities are not a property of the item, they are
a property of the policy that served it.

## Evidence boundary

The executed read over two declared items (illustrative, deterministic).
It demonstrates the mechanism; real systems must estimate propensities
from the serving log per policy version and re-check them when the
policy changes, and they must accept that the correction degrades
gracefully only as fast as the propensity model is refreshed.

## Check your mental model

Answer each before opening it.

**1. Why does IPS recover 0.030 when the naive estimate says 0.060?**

<details>
<summary>Answer</summary>

Because each of A's 12 clicks came from a row the policy made twice as
likely to click, so each click is worth half a unit of true signal;
dividing by the propensity (2.0) gives 12 × 0.5 / 200 = 0.030. The
correction weights each logged row by how much the policy distorted its
chance of appearing and being clicked.

</details>

**2. Why does a stale propensity reproduce the bias?**

<details>
<summary>Answer</summary>

Because the weight is wrong for the rows that produced it. When the
featured slot stops boosting clicks, the stored propensity 2.0 no longer
describes the served rows, and dividing by 1.0 leaves the naive bias in
place. The correction is only as honest as the policy-version pairing of
the propensity log.

</details>

## Next

The loop misreads its own log; [stage 46 — retraining and
staleness](../../46-retraining-and-staleness/) asks how often the model
must be refreshed before the snapshot it holds stops describing the
world. The propensity noise that limits this correction is measured in
[stage 59's noisy-propensity detour](../../../recommendation/59-exposure-bias/when-the-propensity-is-noisy/).
