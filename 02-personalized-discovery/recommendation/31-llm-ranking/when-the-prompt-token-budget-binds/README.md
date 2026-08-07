---
status: verified
level: applied
base: scratch
label: When the prompt token budget binds
verified: 2026-08-07
---

# The prompt token budget binds and becomes the recall boundary

**Question:** [stage 31's LLM ranker](../) can only see what fits the
prompt. This chapter reads the executed truncation and asks what the
budget costs in recall.

**Before this:** [stage 31 — LLM ranking](../) and its executed reorder
model.

## The truncation, executed

The run ([record](runs/2026-08-07-prompt-token-budget-binds-read.md))
feeds a five-item list to a four-item budget:

| item | score | fate |
|---|---:|---|
| d1 | 0.61 | seen |
| d2 | 0.72 | seen |
| d3 | 0.88 | seen |
| d4 | 0.95 | seen |
| d5 | 0.99 | truncated |

Best truncated score: 0.99.

## The reading

d5 scores 0.99 — higher than anything the LLM sees — but sits outside
the budget, so the LLM never sees it and the pointwise order decides
its fate. The prompt budget is the LLM ranker's recall boundary: the
set the ranker can influence is the set the prompt can carry. This is
the same cutoff question stage 22 asked, with tokens instead of
milliseconds — the budget is a design decision, and it silently
excludes the documents beyond it.

## Evidence boundary

The executed truncation over one declared list (illustrative,
deterministic, assumed scores and budget). It demonstrates the
mechanism; real LLM ranking needs the actual token cost per document,
the latency budget, and measured recall beyond the cutoff.

## Check your mental model

Answer each before opening it.

**1. How can the best document be invisible to the ranker?**

<details>
<summary>Answer</summary>

Because visibility is set by the prompt, not by quality. The budget
fits four documents; d5 is fifth. Its 0.99 score is irrelevant to the
LLM — the pointwise order that fed the list already decided it cannot
be reordered. The ranker's influence is bounded by what the prompt
carries, which is exactly the token-budget problem stage 31 names.

</details>

**2. What is the difference between this budget and stage 22's
millisecond budget?**

<details>
<summary>Answer</summary>

Only the unit. Stage 22 cut the candidate set to fit a latency budget;
the LLM ranker cuts it to fit a token budget. Both decide how many
candidates the expensive model can influence, both are set by cost, and
both silently exclude documents beyond the cutoff. The mechanism is the
same funnel arithmetic from stage 08, priced in a different currency.

</details>

## Next

Back to [stage 31](../). The
[disagreement detour](../when-the-llm-disagrees/) shows where the LLM
spends the budget's positions when the list does fit.
