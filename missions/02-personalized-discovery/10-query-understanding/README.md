---
status: verified
level: applied
base: scratch
label: Query understanding
verified: 2026-08-06
---

# The query is a string with noise

**Question:** search begins with a query, and the query is not a clean key.
This stage builds the minimal query-understanding pipeline — tokenize,
normalize, classify — and asks what each step does to retrieval.

**Before this:** [mission 01's tokenizer](../../01-language-model-agent/01-tokenizer/)
for why tokens, not strings; [stage 02's recall](../02-recall/) for why a
candidate set precedes ranking.

## The pipeline, executed

The run ([record](runs/2026-08-06-query-understanding.md)) executes the
stage's core over six realistic queries:

| query | normalized tokens | intent |
|---|---|---|
| best wireless headphones 2026 | best wireless headphones 2026 | navigational |
| buy iPhone 17 Pro Singapore | buy iphone 17 pro singapore | transactional |
| how to fix sleep schedule | how fix sleep schedule | informational |
| Nike Air Max size 9 | nike air max size 9 | navigational |
| cheap flights SIN to NRT | cheap flights sin nrt | transactional |
| redmi note 13 vs poco x6 | redmi note 13 vs poco x6 | informational |

## The three steps, named

1. **Tokenize** — split the string into terms (`[a-z0-9]+`), lowercased.
2. **Normalize** — drop stopwords (the, a, to, of) so the index is not
   split by noise; every variant of a term maps to one key.
3. **Classify** — decide intent: navigational (exact product), 
   transactional (buy/price), informational (how/why/vs).

The intent is not decoration. It decides the retrieval path: a
navigational query wants exact match on an entity, a transactional query
wants price-bearing results, an informational query wants coverage. The
vocabulary across the six queries (28 terms) is the size of the key space
the retrieval index must serve.

## Why this belongs in the mission

Mission 02's contract covers search as one of its three surfaces. Every
search query passes through this pipeline before retrieval, and every
failure upstream (a stopword kept, a casing mismatch) is a recall failure
that no ranker downstream can recover. Query understanding is the search
analogue of stage 00's interaction cleaning: the split between "what the
user meant" and "what they typed" is decided here.

## Evidence boundary

The executed pipeline over six hand-picked realistic queries (synthetic,
illustrative — no real query log). It demonstrates the mechanism and the
vocabulary; it does not measure real-query distributions, which a
production system would need a query log to characterize.

## Check your mental model

Answer each before opening it.

**1. Why is the query normalized before retrieval rather than after?**

<details>
<summary>Answer</summary>

Because the index is built on normalized terms. If the index stores
"Headphones" and the query is "headphones", a case-sensitive match fails;
normalizing both sides to the same key is what makes the index
query-agnostic. The same logic applies to stopwords: the index should not
store "the" as a meaningful term, so it is dropped from the query too.
Normalize once, on both sides, before any retrieval.

</details>

**2. Why does intent classification matter for the candidate set?**

<details>
<summary>Answer</summary>

Because the same words can mean different retrieval jobs. "buy iPhone"
needs results with price and availability; "iPhone vs Pixel" needs
comparisons; "iPhone" alone may need the entity page. Classifying intent
lets the retrieval stage weight the right features — price for
transactional, coverage for informational — instead of treating every
query the same.

</details>

## Next

Forward to [stage 11 — search retrieval](../11-search-retrieval/) where
the normalized query hits the BM25 index.

A detour from here: [where normalization stops and correction must begin](when-the-query-is-misspelled/) — the executed tokenizer read: 'heaphones' never becomes 'headphones', so retrieval must correct the query or match by edit distance.
