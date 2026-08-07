---
status: verified
level: applied
base: scratch
label: When the LLM disagrees
verified: 2026-08-07
---

# The LLM disagrees with the pointwise order where the user looks

**Question:** [stage 31's LLM ranking](../) compares a pointwise order
with the LLM's listwise reorder. This chapter reads the executed
disagreement and asks where the reorder spends its latency.

**Before this:** [stage 31 — LLM ranking](../) and its executed reorder
model.

## The disagreement, executed

The run ([record](runs/2026-08-07-llm-disagrees-read.md)) compares two
orders of the same six documents:

| order | sequence |
|---|---|
| pointwise | d1, d2, d3, d4, d5, d6 |
| listwise | d2, d1, d3, d4, d5, d6 |

Head positions changed: 2/3. Tail positions changed: 0/3.

## The reading

The disagreement concentrates in the head — the LLM reorders the top of
the list where the user actually looks, and leaves the tail alone. That
is the desirable case: the reorder's value is spent on positions that
matter. The failure mode is the opposite — when the disagreement sits in
the tail, the LLM is spending its latency on positions nobody reaches,
and the expensive model is decorative. The position of the disagreement
is the diagnostic: head disagreement is the LLM doing its job, tail
disagreement is the LLM being wasted.

## Evidence boundary

The executed comparison over one hand-built pair of orders
(illustrative, deterministic, assumed pointwise scores and LLM
reorder). It demonstrates the mechanism; real disagreement analysis
needs the actual models and logged positions, which an online
experiment would estimate.

## Check your mental model

Answer each before opening it.

**1. Why is head disagreement the good case?**

<details>
<summary>Answer</summary>

Because the head is where the user decides. Positions one to three get
the attention and the clicks, so a reorder that changes them changes
what the user actually experiences — that is the LLM's value. The
executed run shows 2/3 head positions changing; the reorder is doing
real work where it is visible.

</details>

**2. What does tail-only disagreement mean for the ranker?**

<details>
<summary>Answer</summary>

It means the LLM is spending latency and prompt tokens reordering
positions the user never reaches. The expensive model changes the
document IDs far down the list and nothing else — the user-visible
result is identical, so the LLM ranker is decorative. Tail disagreement
is the signal to shrink the list the LLM sees or remove it from the
cascade.

</details>

## Next

Back to [stage 31](../), where the LLM reorders the list. The
[token-budget detour](../when-the-prompt-token-budget-binds/) shows the
other boundary the same ranker faces: what the prompt can afford to
include.
