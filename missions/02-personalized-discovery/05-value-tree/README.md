---
status: verified
level: applied
verified: 2026-07-30
---

# How do you trade user value against revenue on purpose?

**Goal:** turn each item's vector of calibrated predictions — click,
completion, satisfaction, dwell — into the single number a slate is actually
ordered by, and make the rule for that collapse explicit enough to defend.

Most tutorials stop at "predict the right things" and wave at "then combine
them somehow." Most production arguments inside a real discovery team start
exactly where that wave ends. How you collapse a prediction vector into a
scalar is not a modeling detail — it is the platform's product strategy,
written down as arithmetic, and this stage is where that fact stops being an
abstraction.

**Before this:** [stage 04's four calibrated predictions](../04-fine-rank/)
per item — this stage only works because those numbers are honest
probabilities, not merely well-ranked scores.

## 1. A ranking needs one number, and the choice of number is a decision

Fine-rank hands this stage `{click: 0.7, completion: 0.4, satisfaction:
0.2, dwell: 0.55}` for one item and a different vector for the next. Neither
vector is naturally "bigger" than the other — it depends what you weight.
A platform that cares mostly about immediate engagement and one that cares
mostly about long-term satisfaction will rank the same two items in opposite
order from the same predictions, with no model retrained and no bug
introduced. That is the entire content of this stage: the combination rule
*is* the objective, not a detail downstream of it.

## 2. Weights, made legible by moving one

`core/value_tree.py`'s `combine_additive` computes a normalized weighted sum;
`sweep_weight` holds every other weight fixed and moves exactly one trade —
satisfaction against click — from one end to the other, recording the
resulting order at each step. Run it and watch the top of the slate change
as the weight moves. Nothing about the predictions changed between rows;
only the answer to "what is this platform for, right now" did. That is a
different kind of demonstration than a static formula, because a formula on
a page invites nodding along, while a slate visibly reordering under your own
hand does not.

## 3. Additive and multiplicative encode different beliefs

$$
\text{additive} = \sum_i w_i \, p_i \qquad
\text{multiplicative} = \prod_i p_i^{\,w_i}
$$

**Worked, on two items and two equally weighted objectives.** Item A predicts
0.9 on the first objective and 0.1 on the second; item B predicts 0.5 on both.
Additive scores them $0.5(0.9)+0.5(0.1) = 0.50$ and $0.5(0.5)+0.5(0.5) = 0.50$
— a dead tie. Multiplicative scores them $0.9^{0.5} \times 0.1^{0.5} = 0.30$
and $0.5^{0.5} \times 0.5^{0.5} = 0.50$ — item B wins by two thirds. Same
predictions, same weights, opposite ranking. The rule, not the model, decided
which item a user sees.

Choose a weighted sum and you have chosen to treat objectives as
substitutes: a very high score on one can compensate a very low score on
another, so a highly clickable item with mediocre everything-else can still
win a slot. Choose a weighted product instead and you have chosen to treat
objectives as requirements — any factor near zero, raised to a positive
weight, drags the whole product toward zero, so an item weak on even one
weighted dimension is punished far harder than the equivalent sum would
punish it. Run the same weight sweep under both combination rules
(`demo_calibration_precondition`'s sibling comparison in `run_demo`) and
watch the difference show up directly: at the same satisfaction weight, the
multiplicative order moves toward balanced items measurably sooner than the
additive order does. Neither rule is "more correct." Additive says a
platform will tolerate a bad outcome on one axis in exchange for a great one
elsewhere; multiplicative says it will not — a policy choice a weight cannot
express on its own.

## 4. Calibration is a precondition, not a nicety

Set a weight of 2 on click and you are claiming "click matters twice as much
as whatever carries weight 1." That claim is only true if the click number
is an honest probability. Run `demo_calibration_precondition`: it reruns the
identical weights after inflating click's predictions by a fixed factor,
with no change to product strategy at all, and watch the ranking move
anyway — for a reason that has nothing to do with what the platform is
trying to optimize and everything to do with a miscalibrated input
pretending to be a probability. Skip stage 04's calibration work and every
weight set here makes a promise the arithmetic cannot keep.

## 5. Every ad displaces an organic result — so price the displacement

Remember that an ad does not add a slot to the page — it takes one that an
organic item would otherwise have held. Call `auction_insert` and it prices
that trade explicitly: convert the ad's expected revenue (bid times
predicted click probability) into the same utility units as the organic
value-tree score, using a declared trade rate — utility credited per dollar
of expected revenue — and compare it against the weakest organic score
inside the slate. Clear that bar and the ad enters, displacing whichever
organic item it beat; miss it and the slate stays fully organic. Read the
displaced item's own score and you have exactly what the ad cost the user in
that slot, stated as the same number everything else in this stage is
measured in, not a separate accounting kept off to the side.

Move the weight below and watch the slate reorder, then watch the ad's fate
change as the trade rate moves — the same one-variable-at-a-time discipline
as the weight sweep above, now applied to the question that usually gets
argued about in a room instead of computed.

<!-- interactive: ValueTree -->

## What the numbers actually look like, on a real run

Section 3 above claims the multiplicative rule "moves toward balanced items
measurably sooner" than the additive rule. Run a finer sweep — `steps=200`
instead of the demo's `steps=4` — on the same 12-item, seed-42 slate, and
that claim gets a number: the multiplicative top pick flips at satisfaction
weight **0.165**; the additive top pick doesn't flip until **0.410**. Less
than half the weight buys the same reordering under the stricter rule.

The default demo (`python core/value_tree.py`) confirms the rest: the
calibration break reorders 8 of 12 items with the weights held fixed — click
inflated 1.6x, nothing about product strategy touched — and the ad auction
enters only at `trade_rate=0.8`, displacing `item_6` at organic value 0.499.
`prod/scipy_trade_rate.py --target-ad-load 0.15` solves a trade rate of
0.6039 across 200 independent synthetic slates and hits 15.00% exactly.

Full output: [`runs/2026-07-30-weight-sweep-and-auction.md`](runs/2026-07-30-weight-sweep-and-auction.md).
Every input above is synthetic — `make_items`'s four archetypes, not a fit to
any observed population — so this confirms the mechanics, not a real
platform's actual weights.

## Reproducing

```bash
# weight sweep (additive and multiplicative), calibration precondition demo,
# and the ad auction at a few trade rates
python core/value_tree.py

# a larger synthetic slate
python core/value_tree.py --n-items 30

# the production lane: solve for the trade rate that hits a target ad load
# across many slates, instead of picking one by hand
python prod/scipy_trade_rate.py --target-ad-load 0.15
```

## Exercises

1. **Find the crossover weight.** Sweep the satisfaction weight finely enough
   (raise `steps` in `sweep_weight`) to find the exact point where the top
   item changes under additive combination, and compare it to the crossover
   point under multiplicative combination. The gap between the two crossover
   points is a measurement of how much more conservative the multiplicative
   rule is toward lopsided items.
2. **Design a third combination rule.** A weighted minimum
   (`min(p_i / w_i)`-style) is stricter than the product — a single very weak
   dimension caps the whole score regardless of the others. Implement it and
   compare which items it eliminates that the product does not.
3. **Break calibration harder.** Instead of a flat multiplicative inflation,
   miscalibrate only the top third of click predictions. Confirm the ranking
   damage concentrates where the miscalibration does, not uniformly across
   the slate.
4. **Solve for a trade rate under a shifted bid distribution.** Raise
   `--ad-bid` in `prod/scipy_trade_rate.py` and re-solve for the same target
   ad load. The solved trade rate should fall — the platform needs to credit
   less utility per dollar once bids are already higher.

## Next

This stage produced one score per item. Stage 06 — mixing, not yet built —
is where those scores become an actual page: the value of a slate is not the
sum of its items, and the ad auction above gets folded into a real
permutation search rather than a single insert-or-not decision. See the
stage table in the [mission README](../README.md) for where that fits in the
funnel.
