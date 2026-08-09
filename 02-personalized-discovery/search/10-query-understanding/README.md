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

**Before this:** [mission 01's tokenizer](../../../01-language-model/01-tokenizer/)
for why tokens, not strings; [stage 02's recall](../../shared/02-recall/) for why a
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

<!-- interactive: QueryUnderstanding -->

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

## How you find it: the intent-mix audit, executed

The six queries classify cleanly, and an aggregate intent mix over a
real log would look the same way. The failure mode the aggregate hides
is the query the keyword classifier cannot commit on: one whose keywords
fire two intent classes, and one whose keywords fire none. The run
([record](runs/2026-08-07-query-understanding-audit.md)) emits a
32-query log — 12 head, 20 tail — and the audit stratifies it:

| stratum | queries | no-keyword | collision |
|---|---:|---:|---:|
| head | 12 (37.5%) | 3 (25.0%) | 0 (0.0%) |
| tail | 20 (62.5%) | 5 (25.0%) | 3 (15.0%) |

The verdict is INTENT COLLISION: all three collision queries are tail
queries, and each is assigned by rule order — "cheap how to fix iphone
screen" fires transactional (cheap) and informational (how, fix), and
the transactional check wins silently. The aggregate mix says the rule
order is fine; the stratified view says the tail carries every
ambiguity. Intent labels in production are click-derived and noisy —
Kumar, Hu, Headden, Goutam, Lin and Yin ("Shareable Representations for
Search Query Understanding", arXiv:2001.04345, 2020) build intent
representations for shopping search while accounting for exactly this
noisiness and sparseness of query data — so the classifier inherits the
noise, and the audit shows where it concentrates: the long tail of
short, rare, ambiguous queries.

## The fix and its trade

The fix is a confidence-aware intent model with an explicit ambiguous
bucket, audited by a stratified intent-mix read. The executed audit prices
the failure the fix removes: over a 32-query log (12 head, 20 tail), all
three keyword-collision queries are tail queries — 15% of tail versus 0%
of head — and each is assigned silently by rule order, so the aggregate
mix says the rule order is fine while the tail carries every ambiguity.
Intent labels in production are click-derived and noisy, which Kumar et
al. 2020 (arXiv:2001.04345) build for shopping search while accounting
for exactly this sparseness; the classifier inherits the noise, and the
stratified audit shows where it concentrates.

The trade, named: an explicit ambiguous bucket trades classification
coverage for retrieval flexibility — a query declared ambiguous costs a
defined fallback path instead of a confident wrong route. The
alternative, dual-path retrieval, guarantees the right candidate type is
present but raises candidate count per query and pushes disambiguation
downstream to stage 12's ranker, which can use features where keyword
order cannot. The confidence floor below which intent is declared
ambiguous is a tunable that trades misroute rate against retrieval
complexity, and it belongs to the query-understanding team, not to the
rule author.

## Who owns the loop

The pipeline assigns intent; someone must own what each assignment
commits the system to, and the handoffs are where query understanding
fails:

- **The search query-understanding team** owns the classifier: keyword
  coverage, the rule order, and the confidence floor below which intent
  is declared ambiguous. It owns the collision handling, and the
  when-the-intent-misroutes detour is its failure mode.
- **The retrieval team** owns the path contract: what each intent is
  allowed to fetch, and what happens when a path returns nothing. It
  owns the recall consequence, and the misspelling and short-query
  detours are its failure modes.
- **The data or logging team** owns the intent labels the classifier is
  judged on: the click-derived taxonomy, its noise, and the head/tail
  distribution of the query log. It owns the label source, and the
  audit's verdict is its signal.

When the ownership is implicit, the classifier ships, the retrieval
team trusts its intents, and nobody owns the tail — so a collision
query is silently routed to the wrong path, and the ranker downstream
re-orders a candidate set that was wrong before it started.

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

**3. Why does the aggregate intent mix hide the collision problem?**

<details>
<summary>Answer</summary>

Because collisions and fallbacks are small shares of the log: three of
32 queries, 9.4%. The aggregate says 40.6% transactional and 34.4%
informational and nothing looks wrong, while every collision query is a
tail query whose retrieval path was decided by rule order, not by
meaning. The mix reports what was assigned; it cannot report which
assignments were forced. That is why the audit stratifies by head and
tail instead of reading the mix.

</details>

## Next

Forward to [stage 11 — search retrieval](../11-search-retrieval/) where
the normalized query hits the BM25 index.

A detour from here: [where normalization stops and correction must begin](when-the-query-is-misspelled/) — the executed tokenizer read: 'heaphones' never becomes 'headphones', so retrieval must correct the query or match by edit distance.

Another detour: [one word, many intents](when-the-query-is-short/) — the executed classifier read: every one-word query normalizes to a single token with no intent signal, so disambiguation must come from context.

A third detour: [the intent misroutes](when-the-intent-misroutes/) — the executed path read: four of seven queries keep NDCG@3 at 1.0000 while the collision and no-signal queries collapse to 0.3333, so the candidate set is the wrong type before ranking runs.
