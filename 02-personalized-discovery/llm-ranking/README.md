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

**Before this:** [stage 22 — reranking](../../search/22-reranking/) for the
latency-budget split that decides how many candidates a second model may
see, and [stage 04 — fine-rank](../../shared/04-fine-rank/) for the pointwise
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

## How you find it: the prompt-order audit, executed

The LLM reorder has a failure mode the pointwise ranker never faces:
the same candidate set can rank differently just because the prompt
wrote the candidates in a different order. The mean displacement
cannot see it — the aggregate hides which queries the prompt writing
actually decides. The run ([record](runs/2026-08-07-rank-order-audit.md))
emits a 20-query log, ranks each query under a forward and a reversed
prompt, and stratifies the displacement:

| stratum | queries | swing | mean displacement |
|---|---:|---:|---:|
| head | 10 | 0 | 0.000 |
| tail | 10 | 10 | 1.040 |

The verdict is PROMPT ORDER SWINGS THE REORDER IN THE TAIL: head
rankings are stable (0/10 swing) while every tail query changes with
the written order, at a mean displacement of 1.04 positions per
document. The aggregate displacement of 0.520 is a head artifact —
every unit of prompt-order sensitivity lives where the preference is a
judgment call. Sun et al. ("Is ChatGPT Good at Search?", arXiv:2304.09542,
2023) documents the reordering behavior of LLM rankers, and Qin et al.
("LLMs are Effective Text Rankers with Pairwise Ranking Prompting",
arXiv:2306.17563) shows how the way candidates are presented changes
the LLM's verdict. The decision that follows: gate the reorder on
forward-versus-reverse tail agreement, and where it swings keep the
pointwise order or sample the LLM more than once and aggregate.

<!-- interactive: LlmRanking -->

## The fix and its trade

The fix is the forward-versus-reverse gate: run each candidate set
under a forward and a reversed prompt, and where the tail swings, keep
the pointwise order or sample the LLM more than once and aggregate. The
executed audit prices the failure — head rankings are stable (0 of 10
queries swing, mean displacement 0.000) while every tail query changes
with the written order at 1.040 positions per document, so the
aggregate 0.520 is a head artifact that approves a reorder whose every
swing is a tail judgment call.

The trade is that the gate costs what the listwise view is worth: the
reorder changes 4 of 5 positions because the LLM sees the candidates
together, and gating means either forgoing that reorder where it swings
or paying extra inference to sample and aggregate. The prompt also
grows with the list, so the budget is measured in tokens and the
fallback to the pointwise order must be owned, not assumed — which is
exactly why the tail agreement check, not the mean displacement, is the
approval gate (Sun et al., arXiv:2304.09542, 2023; Qin et al.,
arXiv:2306.17563, 2023).

## Who owns the loop

The LLM ranker sits on top of a cascade, and every handoff around it is
where the reorder fails:

- **The ranking team** owns the prompt: the candidate presentation
  order, the instruction, and the forward-versus-reverse stability
  check that gates the reorder. The [when-the-llm-disagrees
  detour](when-the-llm-disagrees/) is its failure mode — head
  disagreement is the LLM doing its job, tail disagreement is the LLM
  being wasted.
- **The serving or inference team** owns the token and latency budget,
  the parsing and validation of the text answer, and the fallback to
  the pointwise order. The [token-budget
  detour](when-the-prompt-token-budget-binds/) and the
  [output-parse detour](when-the-output-cannot-be-parsed/) are its
  failure modes — a truncated candidate is invisible to the LLM, and
  an unparseable answer is not a ranking.
- **The evaluation team** owns the head/tail measurement, the
  offline/online consistency check, and the sample-and-aggregate
  decision when the tail swings. Its boundary is the served page: a
  reorder approved in the middle of the list changes nothing the user
  sees.

When the ownership is implicit, prompt writers tune against head
queries, serving trusts the text, and nobody owns the tail — so the
aggregate displacement of 0.520 approves a reorder whose every swing
is a tail judgment call.

## Why this belongs in the mission

The funnel's arithmetic (stage 08's latency budget) decides where a
slow, powerful ranker can live. The LLM ranker is the strongest example:
its cost is prompt length, so the budget is measured in tokens, and the
cutoff question is the same one stage 22 asked in milliseconds. The
mission's frontier claim is not that LLMs replace the funnel — it is
that they occupy the position the latency budget allows, and the
disagreement, token-budget, and output-parse detours price the three
failure modes.

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

And a third: [the text answer is not a
list](when-the-output-cannot-be-parsed/) — the executed parse read:
5 of 12 raw answers are not valid permutations, and the naive parse
silently serves five dropped documents and one phantom ID; the
structural check and resample repair all five at the cost of one extra
inference call each.
