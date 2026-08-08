---
status: verified
level: applied
base: none
label: The tier that won
verified: 2026-08-06
---

# When every tier resolves everything, which tier won?

**Question:** [stage 03](../) asked whether the cheap model should replace
the expensive one, and its recorded run resolved all 18 tasks across all
three tiers — haiku, sonnet, opus at 6/6 each. When the resolve rate
separates nothing, the answer is economic: what did each tier actually
charge for the same job?

**Before this:** [stage 03's cost comparison](../) and its recorded results.

## The economics, laid out

The analysis ([run record](runs/2026-08-06-tier-cost.md)) reads the
recorded results:

| tier | resolved | mean cost | total cost | mean output tokens | mean turns |
|---|---:|---:|---:|---:|---:|
| haiku | 6/6 | \$0.1604 | \$0.96 | 7,513 | 10.5 |
| sonnet | 6/6 | \$0.5369 | \$3.22 | 4,680 | 9.8 |
| opus | 6/6 | \$0.8226 | \$4.94 | 4,368 | 11.2 |

## Three readings

**The cheap tier won on cost, decisively.** Haiku resolved the same 18/18 at
10.6% of the total spend — about a fifth of opus's mean price per task. When
the expensive tier buys nothing in resolve rate, the cost split is the
entire decision, and it is not close.

**It won by working harder, not smarter.** Haiku produced 7,513 output
tokens per task versus 4,368-4,680 for the other tiers and took 10.5 turns —
it iterated more to arrive at the same resolved patch. The cheap tier's
price advantage is real, and its mechanism is more labor at a lower rate,
which is exactly the trade a cost-per-resolved-task metric is designed to
surface.

**The tiers trade price against time differently.** Sonnet is middle-priced
(0.537) and fastest (71s wall-clock); opus is slowest per price. When the
product cares about latency rather than token spend, the ranking changes —
which is why the stage reports cost per resolved task beside resolve rate
and the mission reports both, rather than one number.

## The fix and its trade

The fix is the economic reading of a saturated resolve table: when every
tier resolves everything, cost per resolved task is the decision, and it
is decisive — haiku resolves the same 18/18 at 10.6% of total spend. The
trade is what the cheap tier's win is made of: haiku won by working
harder, not smarter — 7,513 output tokens and 10.5 turns per task versus
4,368-4,680 and 9.8-11.2 for the others — so the savings come from the
per-token rate, not from efficiency. And the ranking is latency-sensitive:
sonnet is middle-priced and fastest, so a product that cares about
wall-clock would not pick haiku. The metric pair (cost beside resolve)
is what keeps any single-axis answer from looking like the whole answer.

## Who owns the loop

- **The routing owner** owns the tier policy and its evidence: the
  cost-per-resolved metric is the number a maintainer pays, and the
  resolve saturation that makes it decisive is stated, not assumed.
- **The product owner** owns the latency axis: cost-optimal and
  latency-optimal are different policies, and the mission reports both
  so the choice is visible.
- **The model/cost owner** owns the rate caveat: haiku's advantage is
  the per-token price, which is a commercial fact about the day the
  tiers ran, not a property of the model.

## Evidence boundary

Eighteen tasks, one snapshot, three tiers resolved by the CLI on the
recorded date; the cost fields are the recorded `cost_usd`. It shows the
cost split when resolve is saturated on this task set; it does not claim the
cheap tier wins when the expensive tier's extra reasoning buys resolve on a
harder task distribution — that is the failure-taxonomy stage's separate
claim.

## Check your mental model

Answer each before opening it.

**1. Why is "haiku resolved 18/18" not itself the answer to which tier to
use?**

<details>
<summary>Answer</summary>

Because resolve rate is saturated — every tier resolves everything, so the
number separates nothing. The decision needs the second axis: cost. Haiku
at 10.6% of total spend resolves the same set, so on cost it wins; but the
full answer also needs the labor it spent (more tokens, more turns) and the
latency, which is why the metric is the pair, not the rate alone.

</details>

**2. Haiku produced 70% more output tokens than opus for the same result.
What does that say about where the cheap tier's savings come from?**

<details>
<summary>Answer</summary>

That the savings come from the per-token rate, not from efficiency. The
cheap tier spent more generation and more turns to reach the same patch —
it is cheap per unit of labor and used more units. The cost-per-resolved
metric captures both sides: the low rate wins on price, and the extra
iteration is the honest price it pays.

</details>

## Next

[Stage 04's failure taxonomy](../../04-how-it-fails/): where the harness's
zero-failure surface and the blind call's non-applying patches are counted,
completing the pair the cost question needs.
