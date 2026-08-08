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

## The fix and its trade

The fix is to use the position of the disagreement as the gate: measure
the head/tail split of the reorder, and where the disagreement sits in
the tail, shrink the list the LLM sees or remove it from the cascade.
The executed comparison prices the good case — 2 of 3 head positions
change while 0 of 3 tail positions do, so the reorder spends its
latency on the positions where the user decides. The failure mode is
the mirror image: tail-only disagreement means the expensive model
changes document IDs nobody reaches.

The trade is that the gate costs a head/tail measurement and can remove
a ranker that would have helped a different list: head agreement with
tail disagreement is not the absence of signal, and shrinking the list
to the head shrinks the reorder's reach with it. The diagnostic is
position-specific because that is where the user-visible value lives —
the reorder that changes the top of the page changes the experience,
and the reorder that only moves the tail is decorative at the price of
a full inference call.

## Who owns the loop

- **The ranking team** owns the head/tail disagreement gate and the
  list-size decision when the reorder spends itself on the tail.
- **The serving and inference team** owns the latency and token spend,
  the cost the gate decides whether the reorder is worth.
- **The evaluation team** owns the head/tail measurement from logged
  positions, the diagnostic that separates the working reorder from the
  decorative one.

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
