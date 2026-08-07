---
status: verified
level: applied
base: scratch
label: When the vocabulary mismatches
verified: 2026-08-07
---

# The relevant document that scores zero is not ranked — it is gone

**Question:** [stage 11's BM25 index](../) scores exact terms. The
synonym detour showed a partial match being under-ranked; this chapter
is the harder half — a relevant document that shares no query term at
all scores 0.0000 and is cut before ranking, and only expansion or a
dense path can bring it back.

**Before this:** [stage 11 — search retrieval](../), and the
[synonym that lexical retrieval cannot see](../when-the-synonym-is-invisible/)
for the under-ranking half of the same failure.

## The cut, executed

The run ([record](runs/2026-08-07-lexical-gap-read.md)) searches
"cheap headphones" with doc6 ("affordable earbuds budget friendly
sound") declared relevant:

| query variant | top-3 | recall@3 | doc6 score |
|---|---|---:|---:|
| cheap headphones | doc7, doc1, doc5 | 0.00 | 0.0000 |
| cheap headphones affordable budget | doc6, doc7, doc1 | 1.00 | 3.3903 |

## Two findings

**The zero-score document is cut, not ranked last.** "affordable earbuds
budget friendly sound" shares no term with "cheap headphones" — not
"cheap", not "headphones" ("earbuds" is a different token) — so it ties
at 0.0000 and sorts below the other zero-scoring docs. Recall@3 is 0.00
because the document is not in the candidate set at all; the ranker
downstream ([stage 12](../../12-search-ranking/)) can only re-order what
it was handed. This is the same recall-vs-precision split the stage's
own audit measures: "running shoes" still finds its partial-match doc
d7 because one term hits, while zero overlap is an absolute miss.

**Expansion fixes recall and costs precision.** Adding the synonyms
"affordable budget" lifts doc6 to the top (recall@3 1.00) but also
pulls in doc7 — "cheap running shoes on sale" — as a false positive for
headphones. The trade is the whole cascade: retrieval widens to protect
recall, and reranking pays the precision bill. Production search runs
synonym expansion ([stage 19 — query expansion](../../19-query-expansion/))
or a dense path ([stage 20 — dense retrieval](../../20-dense-retrieval/))
precisely because the zero-overlap cut is otherwise unrecoverable.
Robertson and Zaragoza ("The Probabilistic Relevance Framework: BM25 and
Beyond", Foundations and Trends in Information Retrieval 3(4), 2009)
formalize the lexical scoring; Karpukhin et al. ("Dense Passage
Retrieval for Open-Domain Question Answering", EMNLP 2020) motivate the
dense alternative.

## Evidence boundary

The corpus is the stage's five documents plus two synthetic additions
(illustrative, deterministic). It measures the cut mechanism and the
expansion trade; real recall needs declared relevance on a production
document set, which the stage's audit would need a labeled corpus to
estimate.

## Check your mental model

Answer each before opening it.

**1. Why is recall@3 0.00 even though doc6 is "on topic"?**

<details>
<summary>Answer</summary>

Because retrieval is a hard gate over exact terms. Doc6 shares no query
term — "cheap" is absent and "earbuds" is not "headphones" — so its BM25
score is 0.0000 and it never enters the top-3, however relevant a
human would call it. Semantic relevance and lexical score are different
things; the lexical index only sees the latter, which is why a meaning
path (expansion or dense) must run alongside it.

</details>

**2. What does the doc7 false positive prove about expansion?**

<details>
<summary>Answer</summary>

That expansion trades precision for recall: the same synonym list that
rescues doc6 also matches a running-shoes sale doc. The candidate set
grows, and the ranker must re-check relevance with richer features.
Expansion without a reranking stage just moves the error downstream.

</details>

## Next

Back to [stage 11](../), or forward to
[stage 12 — search ranking](../../12-search-ranking/) where the
retrieved candidate set is re-ordered.
