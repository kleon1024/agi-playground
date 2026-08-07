---
status: verified
level: applied
base: scratch
label: Search retrieval
verified: 2026-08-06
---

# BM25: the lexical first stage that dense retrieval has to beat

**Question:** search retrieval is the search analogue of recommendation
recall — a cheap first stage that returns a candidate set. This stage
builds BM25 from scratch and asks what lexical retrieval does and where it
fails.

**Before this:** [stage 10 — query understanding](../10-query-understanding/)
for the normalized query, and [stage 02's recall](../../shared/02-recall/) for the
candidate-set contract.

## The index, executed

The run ([record](runs/2026-08-06-bm25-retrieval.md)) executes the
from-scratch BM25 over a five-document corpus:

| query | top result | score |
|---|---:|
| wireless headphones | doc1 (wireless headphones noise cancelling bluetooth) | 1.9592 |
| running shoes | doc3 (running shoes lightweight breathable) | 3.0939 |
| iphone camera | doc4 (iphone pro max camera battery life) | 2.5931 |
| headphones 2026 | doc5 (headphones price comparison review 2026) | 1.9592 |

## The mechanism, named

BM25 scores a document for a query by summing, per term, an IDF weight
times a term-frequency factor normalized by document length (k1=1.5,
b=0.75 here). Three properties fall out:

1. **Term frequency matters, sublinearly** — a term appearing twice helps
   but not twice as much.
2. **Length normalization** — a short document matching a term beats a long
   one that mentions it once.
3. **IDF weights rarity** — a rare query term contributes more than a
   common one.

## The failure the stage exists to show

The vocabulary-mismatch gap is visible in the executed run: for "running
shoes", every document without those exact words scores 0.0000 — a
document about "athletic footwear" is invisible to the lexical index even
though it is semantically on-topic. That is the gap dense retrieval (stage
02's embedding path) exists to close, and it is why production search is
hybrid: lexical for exact terms and entities, dense for meaning.

## Evidence boundary

The executed index over a five-document synthetic corpus (deterministic,
illustrative). It demonstrates the scoring mechanism and the mismatch
failure; it does not measure real-corpus retrieval quality, which needs a
real document set and relevance labels.

## Check your mental model

Answer each before opening it.

**1. Why does BM25 still matter if dense retrieval exists?**

<details>
<summary>Answer</summary>

Because lexical and dense retrieval fail differently. BM25 matches exact
terms and entities — "iPhone 17" finds the page with those exact words —
while dense retrieval matches meaning and misses exactness. Production
search runs both and fuses: the hybrid covers the mismatch either alone
would miss. BM25 is also the baseline every dense paper compares against,
so understanding it is how you read those papers.

</details>

**2. What does the zero-score row teach about candidate sets?**

<details>
<summary>Answer</summary>

That retrieval is a hard gate: a document scoring 0.0000 is not in the
candidate set, so no ranker downstream can ever surface it. The
vocabulary-mismatch failure is therefore not "slightly worse ranking" —
it is an invisible recall loss. That is why the mission treats retrieval
as a stage to measure, not a parameter to tune.

</details>

## Next

Forward to [stage 12 — search ranking](../12-search-ranking/) where the
retrieved candidate set is re-ordered.

A detour from here: [the document that means the same but scores less](when-the-synonym-is-invisible/) — the executed index read: 'running footwear' scores 1.04 against 'running shoes'' 2.86, the vocabulary mismatch dense retrieval closes.

Another detour: [the embedding that sees the synonym](when-the-dense-path-exists/) — the executed contrast read: cosine scores meaning (0.816 for the synonym doc) where BM25 scored low, which is why production search runs hybrid.
