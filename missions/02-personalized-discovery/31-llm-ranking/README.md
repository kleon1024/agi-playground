---
status: verified
level: applied
base: scratch
label: LLM ranking
verified: 2026-08-07
---

# The LLM reorders the list it can afford to see

**Question:** every ranker so far scored candidates with a model trained
for the job. This stage asks what changes when the ranker is a general
LLM that sees the whole list as context and answers: it reorders, but it
can only see what fits the prompt.

**Before this:** [stage 22 — reranking](../22-reranking/) for the
latency-budget split that decides how many candidates a second model may
see, and [stage 04 — fine-rank](../04-fine-rank/) for the pointwise
score the LLM is compared against.

## The reorder, executed

The run ([record](runs/2026-08-07-llm-ranking.md)) compares a pointwise
order with the LLM's listwise reorder of the same five documents:

| order | sequence |
|---|---|
| pointwise | d1, d2, d3, d4, d5 |
| listwise | d4, d2, d5, d1, d3 |
| positions changed | 4/5 |

## The mechanism, named

The pointwise ranker scores each document and sorts; the LLM reads the
list as one context and emits a new order, so it can use interactions
between documents — d4 jumps to the top because the instruction reading
favors it. The listwise view is the frontier advantage, and it is
expensive: the prompt grows with the list, which is why the LLM sits at
the top of a cascade over a short list, never over the whole candidate
set.

## Why this belongs in the mission

The funnel's arithmetic (stage 08's latency budget) decides where a
slow, powerful ranker can live. The LLM ranker is the strongest example:
its cost is prompt length, so the budget is measured in tokens, and the
cutoff question is the same one stage 22 asked in milliseconds. The
mission's frontier claim is not that LLMs replace the funnel — it is
that they occupy the position the latency budget allows, and the
disagreement and token-budget detours price the two failure modes.

## Evidence boundary

The executed comparison over one hand-built list (illustrative,
deterministic, assumed pointwise scores and LLM reorder). It
demonstrates the mechanism; real LLM ranking also depends on prompt
design, model choice, and measured latency, which an online experiment
would estimate.

## Check your mental model

Answer each before opening it.

**1. Why can the LLM ranker not score the whole candidate set?**

<details>
<summary>Answer</summary>

Because its cost is prompt length. Every candidate added to the prompt
adds tokens, and the latency budget (stage 08) is fixed. The LLM can
only see what fits — a cascade stages it after a cheap cut that shrinks
the set, and its recall boundary is the token budget, not the index.

</details>

**2. What does the listwise view buy that pointwise scoring cannot?**

<details>
<summary>Answer</summary>

Document-to-document comparison. The pointwise ranker scores each
document alone; the LLM sees the candidates together and can apply
preferences that depend on the set — like picking the one that
complements the rest. That interaction is exactly what the pointwise
score is blind to, and it is the reason the reorder changes 4 of 5
positions in the executed run.

</details>

## Next

This opens the frontier recommendation track (stages 31-34), which
revisits the recommendation surface with the tools that changed after
the core tracks were built. Next is [stage 32 — recommendation
RLHF](../32-recommendation-rlhf/), where the ranker learns from
preferences instead of labels.

A detour from here: [the LLM disagrees with the pointwise order
where the user looks](when-the-llm-disagrees/) — the executed
disagreement read: 2/3 head positions change while 0/3 tail positions
do, so the reorder spends its latency where the user actually looks.

Another detour: [the prompt token budget binds and becomes the
recall boundary](when-the-prompt-token-budget-binds/) — the executed
truncation read: d5 scores 0.99 but sits outside the budget, so the LLM
never sees it and the pointwise order decides its fate.
