---
status: draft
level: applied
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

A weighted sum treats objectives as substitutes: a very high score on one
can compensate a very low score on another, so a highly clickable item with
mediocre everything-else can still win a slot. A weighted product treats
objectives as requirements — because any factor near zero, raised to a
positive weight, drags the whole product toward zero, an item weak on even
one weighted dimension is punished far harder than the equivalent sum would
punish it. `demo_calibration_precondition`'s sibling comparison in
`run_demo` — the weight sweep run under both combination rules — shows this
directly: at the same satisfaction weight, the multiplicative order moves
toward balanced items measurably sooner than the additive order does. Neither
rule is "more correct." Additive says a platform will tolerate a bad outcome
on one axis in exchange for a great one elsewhere; multiplicative says it
will not. That is a policy choice a weight cannot express on its own.

## 4. Calibration is a precondition, not a nicety

A weight of 2 on click is supposed to mean "click matters twice as much as
whatever carries weight 1." That claim is only true if the click number is
an honest probability. `demo_calibration_precondition` reruns the identical
weights after inflating click's predictions by a fixed factor, with no
change to product strategy at all, and the ranking still moves — for a
reason that has nothing to do with what the platform is trying to optimize
and everything to do with a miscalibrated input pretending to be a
probability. Stage 04's calibration work is not a nice-to-have that happens
to make the numbers look tidier; skipping it means every weight set here is
making a promise the arithmetic cannot keep.

## 5. Every ad displaces an organic result — so price the displacement

An ad does not add a slot to the page; it takes one that an organic item
would otherwise have held. `auction_insert` prices that trade explicitly:
convert the ad's expected revenue (bid times predicted click probability)
into the same utility units as the organic value-tree score, using a
declared trade rate — utility credited per dollar of expected revenue — and
compare it against the weakest organic score inside the slate. Clear that
bar and the ad enters, displacing whichever organic item it beat; miss it
and the slate stays fully organic. The displaced item's own score is exactly
what the ad cost the user in that slot, stated as the same number everything
else in this stage is measured in, not a separate accounting kept off to the
side.

Move the weight below and watch the slate reorder, then watch the ad's fate
change as the trade rate moves — the same one-variable-at-a-time discipline
as the weight sweep above, now applied to the question that usually gets
argued about in a room instead of computed.

<!-- interactive: ValueTree -->

## Reproducing

No run has happened yet; the commands below exercise the arithmetic on a
synthetic slate, not a report of a completed run.

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
