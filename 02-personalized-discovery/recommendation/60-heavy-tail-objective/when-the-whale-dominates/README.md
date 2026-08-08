---
status: verified
level: applied
base: scratch
label: When the whale dominates
verified: 2026-08-07
---

# The top 1% that owns a quarter of the gradient

**Question:** [stage 60](../) compares GMV regressions. This chapter makes
the whale mechanism concrete: under raw MSE, the top 1% of orders own a
quarter of the gradient — twenty-five times their fair share.

**Before this:** [stage 60 — heavy-tail objective](../).

## The gradient share, executed

The run ([record](runs/2026-08-07-whale-dominates.md)) reads the top 1%'s
gradient share:

| objective | top 1% of orders gradient share |
|---|---:|
| raw MSE | 25.4% |
| log amount | 3.3% |

## The reading

Under raw MSE the top 1% of orders own a quarter of the gradient —
twenty-five times their fair share — so the model fits whales and treats
the 99% as noise. The log transform compresses the tail to 3.3%: a whale
is still worth more, but it no longer is the whole argument. The share is
the number to watch when choosing the objective, because it is the
mechanism behind stage 60's error table.

## The fix and its trade

The fix is to transform the target so the whale's influence falls to
something like its fair share. The executed read prices the mechanism
behind stage 60's error table: under raw MSE the top 1% of orders own
25.4% of the gradient — twenty-five times their fair share — and the log
transform compresses that to 3.3%. The whale is still the largest
residual contributor; it just no longer is the whole argument.

The trade, named: the transform buys a balanced gradient at the price of
tail fidelity and interpretability. A whale order is still worth more,
but the model no longer spends a quarter of its capacity on one percent
of orders — and the log scale changes what a "unit of error" means, which
is a real cost when the value tree multiplies the resulting scores
downstream. Whether that trade is worth it is a product decision about
whether the tail is signal, and the gradient share is the number to
watch: it turns the objective debate from an argument into a measured
dial.

## Who owns the loop

- **The model team** owns the objective and the per-class gradient-share
  read during training — the share is the diagnostic that says the
  objective is doing what the team thinks it is.
- **The product team** owns the tail-is-signal decision: fitting the
  whales or the common case changes what the ranker serves, and that is a
  business judgment.
- **The monitoring team** owns the top-decile share on every training
  run, so a distributional shift that quietly re-whales the gradient is
  visible before it re-whales the model.

## Evidence boundary

The executed read over a synthetic order distribution (illustrative,
deterministic). It demonstrates the share mechanics; real systems must
measure the top-decile gradient share during training and decide whether
the tail is signal worth keeping.

## Check your mental model

Answer each before opening it.

**1. Why is the top 1% owning 25% of the gradient a defect?**

<details>
<summary>Answer</summary>

Because it means the model spends a quarter of its capacity on one percent
of orders. The common case gets the remaining 75% spread over 99% of the
data, so the fit follows the whales.

</details>

**2. What does the log transform change about the whale?**

<details>
<summary>Answer</summary>

Its influence, not its existence: the whale is still the largest residual
contributor, but at 3.3% it no longer dominates the update, so the model
can fit the common case too.

</details>

## Next

Back to [stage 60](../). The cohort face of the same decomposition: [a
flash sale doubles the rate and halves the AOV](../when-the-aov-skews/).
