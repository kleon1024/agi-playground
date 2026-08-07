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
decode accuracy falls as the ID vocabulary grows, which the three
detours price.

## How you find it: the decode-recall audit, executed

The failure mode this audit exists for is the aggregate decode metric:
a head-dominated log reports "the generative retriever decodes well"
while the tail — where training has the least evidence — loses most of
its recall and emits nonexistent IDs. The run
([record](runs/2026-08-07-genret-audit.md)) emits a 20-query log and
stratifies decode recall@5 and emitted-ID precision by head and tail:

| stratum | queries | recall@5 | precision |
|---|---:|---:|---:|
| head | 10 | 1.000 | 1.000 |
| tail | 10 | 0.540 | 0.740 |

The verdict is DECODE RECALL DIVERGES IN THE TAIL: the aggregate
recall@5 of 0.770 is a head artifact — head decodes perfectly while
tail recall is 0.540 with 0.740 precision, so a quarter of the emitted
tail IDs do not exist. The decode is a trained behavior (the
Differentiable Search Index, Tay et al., NeurIPS 2022), so it inherits
the training distribution. The decision that follows: gate the
generative path to queries it can decode, and fall back to the dense
or hybrid path for the tail.

## Who owns the loop

The decode is a trained behavior, so its quality is owned at the
training-serving boundary, and the handoffs are where the tail gets
lost:

- **The generative-model team** owns the decode itself: recall and
  emitted-ID precision per stratum, and the ID-format decision that
  sets how ambiguous a decode can be — the
  [when-the-id-is-a-phrase detour](when-the-id-is-a-phrase/) is its
  failure mode.
- **The serving or fallback team** owns the routing: which queries are
  gated into the generative path and which fall back to dense or
  hybrid, priced by where the decode breaks — the
  [when-the-id-space-grows detour](when-the-id-space-grows/) is its
  pricing.
- **The evaluation team** owns the stratified report: the head/tail
  table instead of the aggregate, and the check that emitted IDs exist
  — the [when-the-generator-hallucinates
  detour](when-the-generator-hallucinates/) is its failure mode.

When the ownership is implicit, the evaluation team reports an
aggregate recall, the model team owns a head-validated decode, and
nobody owns the tail — so the tail collapse ships as "generative
retrieval works" until the stratified report exists.

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
detours quantify.

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

And a third: [the ID is a phrase and the phrase names too
much](when-the-id-is-a-phrase/) — the executed substring count read:
"search" names five of eight titles, so the no-index claim softens
once IDs are human-readable and a resolution lookup returns.
