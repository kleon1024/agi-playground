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

## How you find it: the lexical recall audit, executed

The mismatch is not a ranking detail; it is a recall loss, and the
aggregate hides it. The run ([record](runs/2026-08-07-search-retrieval-audit.md))
emits the audit corpus and per-query rankings with declared relevance,
and the audit measures recall@3 per query:

| query | freq | recall@3 | mean term overlap | zero-score miss |
|---|---|---:|---:|---|
| wireless headphones | head | 1.00 | 2.00 | - |
| running shoes | head | 1.00 | 1.50 | - |
| iphone camera | head | 1.00 | 2.00 | - |
| laptop battery | head | 1.00 | 2.00 | - |
| cheap headphones | tail | 0.50 | 1.00 | d6 |

The verdict is LEXICAL GAP: aggregate recall@3 is 0.90, but "cheap
headphones" lost d6 ("affordable bluetooth earbuds budget friendly")
because it shares no query term and scored 0.0000 — cut before ranking,
so no ranker downstream can recover it. The partial-match half is the
contrast: "running shoes" keeps d7 ("sneakers athletic footwear
lightweight running") because one term, "running", still hits. The
cut is reserved for zero overlap. Robertson and Zaragoza ("The
Probabilistic Relevance Framework: BM25 and Beyond", Foundations and
Trends in Information Retrieval 3(4), 2009) formalize the lexical
scoring; Karpukhin et al. ("Dense Passage Retrieval for Open-Domain
Question Answering", EMNLP 2020) are the dense alternative the audit
points to as the fix.

## Who owns the loop

Retrieval is a hard gate; someone must own what the gate cuts, and the
handoffs are where lexical search fails:

- **The retrieval team** owns the index and the cutoff: BM25 parameters,
  the candidate-set size, and the zero-score policy. It owns recall,
  and the vocabulary-mismatch and synonym detours are its failure modes.
- **The query-understanding team** owns the query side of the contract:
  expansion lists, spelling correction, and the head/tail coverage of
  the query log. It owns the fix that expansion provides, and it shares
  the audit's LEXICAL GAP verdict with retrieval.
- **The relevance or evaluation team** owns the declared labels: which
  documents are relevant to which queries, and the recall@k bar. It
  owns the measurement, and the audit's per-query table is its signal.

When the ownership is implicit, retrieval tunes scores, nobody holds the
relevance labels, and the zero-score cut ships as "BM25 working as
intended" — until a support ticket about a missing product surfaces the
document the index never saw.

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

**3. Why is "cheap headphones" the query the audit catches?**

<details>
<summary>Answer</summary>

Because its relevant document shares zero query terms — "affordable
earbuds budget friendly" has neither "cheap" nor "headphones" — so it
scores exactly 0.0000 and is cut. The head queries all match on at least
one term and keep recall at 1.00, which is why the 0.90 aggregate looks
fine. The audit's per-query table is the point: recall is a per-query
claim, and the tail query is where lexical search breaks.

</details>

## Next

Forward to [stage 12 — search ranking](../12-search-ranking/) where the
retrieved candidate set is re-ordered.

A detour from here: [the document that means the same but scores less](when-the-synonym-is-invisible/) — the executed index read: 'running footwear' scores 1.04 against 'running shoes'' 2.86, the vocabulary mismatch dense retrieval closes.

Another detour: [the embedding that sees the synonym](when-the-dense-path-exists/) — the executed contrast read: cosine scores meaning (0.816 for the synonym doc) where BM25 scored low, which is why production search runs hybrid.

A third detour: [the vocabulary mismatch cuts the candidate](when-the-vocabulary-mismatches/) — the executed read: 'cheap headphones' cuts the relevant doc at 0.0000 (recall@3 0.00) and expansion recovers it (1.00) at the cost of a false positive, so the zero-overlap cut is a recall loss no ranker can fix.
