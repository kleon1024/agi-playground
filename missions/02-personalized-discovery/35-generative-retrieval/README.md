---
status: verified
level: applied
base: scratch
label: Generative retrieval
verified: 2026-08-07
---

# The model emits the document ID directly

**Question:** every retrieval stage so far matched a query against an
index. This stage asks what happens when the model generates the
document IDs itself and answers: there is no index scan and no
candidate step — retrieval becomes a decode, with decode latency and
hallucination as the frontier costs.

**Before this:** [stage 20 — dense retrieval](../20-dense-retrieval/)
for the embedding index this stage removes, and [stage 22 —
reranking](../22-reranking/) for where the candidate step used to sit.

## The decode, executed

The run ([record](runs/2026-08-07-generative-retrieval.md)) beams over
four document IDs:

| doc | score |
|---|---:|
| doc_17 | 0.9 |
| doc_03 | 0.7 |
| doc_42 | 0.4 |
| doc_09 | 0.2 |

Beam top-2: doc_17, doc_03.

## The mechanism, named

A generative retriever is a sequence model over document IDs: it sees
the query and emits the IDs of the documents most likely to answer it.
There is no scan, no candidate generation, no fusion — the beam decode
is the whole retrieval path. That compresses the funnel, and it moves
the failure modes: the model can emit an ID that does not exist, and
decode accuracy falls as the ID vocabulary grows, which the two detours
price.

## Why this belongs in the mission

The funnel's first stages exist because scoring everything is
impossible. Generative retrieval attacks that constraint directly —
if the model can name the answer, the index and its latency are gone.
The mission's frontier claim is conditional, though: the decode must be
accurate over the real ID space and must not invent documents. This
stage states the mechanism and lets the evidence boundary say what the
approach does and does not prove.

## Evidence boundary

The executed beam over four declared scores (illustrative,
deterministic, assumed decode probabilities). It demonstrates the
mechanism; real generative retrieval needs the trained model, a
measured decode latency, and recall over the actual corpus, which the
ID-space and hallucination detours quantify.

## Check your mental model

Answer each before opening it.

**1. What does generative retrieval remove from the funnel?**

<details>
<summary>Answer</summary>

The index scan and the candidate generation step. Dense retrieval
embeds the query, scans the ANN index, and returns candidates for a
ranker. Generative retrieval emits the top document IDs in one decode —
no scan, no candidate list, no fusion. The cost moves to the decode:
latency per generation and the probability of emitting a wrong or
nonexistent ID.

</details>

**2. Why is recall now a decode property instead of an index property?**

<details>
<summary>Answer</summary>

Because the document is found by generating its ID, not by searching
for it. Recall depends on how often the decode produces the right ID,
which falls as the ID vocabulary grows — the executed curve drops from
0.98 accuracy at 100 docs to 0.71 at 100,000. The index was the
guarantee before; now the beam is the constraint.

</details>

## Next

This opens the frontier search track (stages 35-37). Next is [stage 36 —
conversational search](../36-conversational-search/), where the query
carries a session.

A detour from here: [the ID space grows and decode accuracy
falls](when-the-id-space-grows/) — the executed sweep read: beam
accuracy drops from 0.98 at 100 docs to 0.71 at 100,000, so
generative retrieval's recall is a decode property, not an index
property.

Another detour: [the generator hallucinates an ID that does not
exist](when-the-generator-hallucinates/) — the executed check read:
doc_99 is emitted but missing from the corpus, so the beam slot is
wasted and the result is dropped at the corpus check.
