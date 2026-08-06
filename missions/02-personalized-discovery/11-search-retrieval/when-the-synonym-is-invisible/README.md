---
status: verified
level: applied
base: scratch
label: When the synonym is invisible
verified: 2026-08-06
---

# The document that means the same but scores less

**Question:** [stage 11's BM25 index](../) scores exact terms. This chapter
adds a synonym document and reads the partial-match gap — the exact
failure dense retrieval is built to close.

**Before this:** [stage 11 — search retrieval](../) and its executed
index.

## The gap, executed

The run ([record](runs/2026-08-06-synonym-read.md)) adds doc6 ("running
footwear lightweight athletic sneakers") to the corpus and re-runs the
query "running shoes":

| doc | score |
|---|---:|
| doc3 (running shoes lightweight breathable) | 2.8608 |
| doc6 (running footwear lightweight athletic sneakers) | 1.0448 |
| doc1, doc2, doc4, doc5 | 0.0000 |

## Two readings

**The synonym document partially matches and is under-ranked.** doc6's
"running" hits the query, but "footwear" does not equal "shoes", so it
scores 1.04 against doc3's 2.86 — semantically near-identical, ranked
half as relevant. The vocabulary mismatch is a graded failure, not an
all-or-nothing one: partial lexical overlap under-ranks meaning.

**Dense retrieval is the gap this stage names.** An embedding-based
matcher would place doc6 beside doc3, because "footwear" and "shoes"
embed near each other. The lesson is not "BM25 is bad" — it is that
lexical and dense retrieval fail differently, which is why production
search is hybrid: BM25 for exact terms and entities, dense for meaning,
fused into one candidate set.

## Evidence boundary

The executed index over a six-document synthetic corpus (deterministic,
illustrative). It demonstrates the mismatch; real hybrid search needs a
dense index and a fusion rule measured on a real corpus.

## Check your mental model

Answer each before opening it.

**1. Why does "running" alone lift doc6 at all?**

<details>
<summary>Answer</summary>

Because BM25 scores per matched term. "Running" appears in the query and
the document, so it contributes its IDF weight; only "shoes" finds no
match. The partial score (1.04) is the lexical residue of the overlap —
which is exactly why it is an under-rank rather than a zero: the system
knows doc6 is somewhat relevant but cannot see how relevant.

</details>

**2. What does "hybrid" actually mean for the candidate set?**

<details>
<summary>Answer</summary>

Running both matchers and taking the union (or a weighted fusion) of
their top results. BM25 catches the exact-term case dense might blur;
dense catches the synonym case BM25 misses; the union is what the ranker
receives. The stage's lesson — they fail differently — is what makes the
combination a design, not a belt-and-suspenders afterthought.

</details>

## Next

Back to [stage 11](../), or forward to
[stage 12 — search ranking](../../12-search-ranking/) where the candidate set
is re-ordered.
