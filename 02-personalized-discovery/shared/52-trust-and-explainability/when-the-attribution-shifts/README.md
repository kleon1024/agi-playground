---
status: verified
level: applied
base: scratch
label: When the attribution shifts
verified: 2026-08-07
---

# The headline changes with the baseline

**Question:** [stage 52's explanation](../) broke one score into
contributions. This chapter asks whether that breakdown is a stable
fact, and answers: it is not — an attribution is a statement about the
item against a counterfactual, and the same item, the same model, and
the same score produce a different largest contribution depending on
which baseline the explanation tool subtracts.

**Before this:** [stage 52 — trust and explainability](../) for the
contribution table being explained, and [stage 07 — rule
engine](../../07-rule-engine/) for the auditable-decision discipline
this continues.

## The flip, executed

The run ([record](runs/2026-08-07-attribution-shifts-read.md)) computes
the same item's contributions against two baselines:

| feature | zero baseline | mean baseline |
|---|---:|---:|
| price | −0.0240 | −0.0016 |
| category affinity | +0.0080 | −0.0120 |
| similar users bought | +0.0198 | +0.0011 |
| you viewed this category | +0.0140 | +0.0053 |
| headline | similar users bought | you viewed this category |

## The reading

Against the zero baseline the largest contribution is "similar users
bought" — unverifiable. Against the population-mean baseline the largest
contribution is "you viewed this category" — verifiable. Neither number
is wrong; both are correct statements of the same linear score against
different counterfactuals. Attribution methods that define a reference
distribution (Shapley-value-based approaches; Lundberg & Lee, "A Unified
Approach to Interpreting Model Predictions", NeurIPS 2017) make the
baseline explicit precisely because the answer changes with it.

The production consequence is that the explanation's headline is a
product decision hidden inside a modeling choice: whichever baseline the
tool picks decides which claim the user sees. Two teams computing
"why was this shown" for the same item can surface different headlines,
and both will insist theirs is correct. The fix is to name the
counterfactual the explanation answers — "compared with what?" — and to
verify the chosen baseline against the comparison the user actually
makes, not the one that makes the headline verifiable.

## Evidence boundary

The executed contribution comparison over one declared item and two
declared baselines (illustrative, deterministic). It demonstrates the
mechanism; real systems must audit which baseline their explanation
tool uses, and check the headline's stability across the baselines users
plausibly hold, before trusting the "why" text.

## Check your mental model

Answer each before opening it.

**1. Why is neither contribution table wrong?**

<details>
<summary>Answer</summary>

Because an attribution is always relative to a counterfactual: the zero
baseline asks "compared with an item with no feature values", the mean
baseline asks "compared with the average item". Both are legitimate
questions about the same score, and each produces its own answer. The
score does not change; the question does, and the headline follows the
question.

</details>

**2. How would you catch this in a real product?**

<details>
<summary>Answer</summary>

By asking "compared with what" of the explanation copy, and by diffing
the headlines two attribution tools produce for the same item. If the
headline flips between tools or between versions of the same tool, the
baseline is driving the user-visible claim. The fix is to pin the
counterfactual to the comparison users actually make — the previous
slate, the category default, the average item — and measure whether the
explanation stays verifiable under it.

</details>

## Next

Back to [stage 52](../). The explanation must be verifiable and its
headline stable; [stage 53 — fairness and
allocation](../../53-fairness-and-allocation/) asks how the page is
allocated across the whole catalogue, where the same aggregate-vs-slice
discipline applies to exposure.
