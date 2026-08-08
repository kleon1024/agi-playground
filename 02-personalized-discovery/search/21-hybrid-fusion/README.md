---
status: verified
level: applied
base: scratch
label: Hybrid fusion
verified: 2026-08-07
---

# Two retrieval sets, one answer list

**Question:** [stage 11's BM25](../11-search-retrieval/) and [stage
20's dense retrieval](../20-dense-retrieval/) each have a blind spot.
This stage asks how two candidate sets become one answer list, and
answers with reciprocal rank fusion: keep the union, reward the
documents both matchers agree on.

**Before this:** [stage 11 — search retrieval](../11-search-retrieval/)
and [stage 20 — dense retrieval](../20-dense-retrieval/) for the two
matchers being fused.

## The fusion, executed

The run ([record](runs/2026-08-07-hybrid-fusion.md)) fuses a lexical
list `[d1, d2, d3, d4]` and a dense list `[d4, d5, d1, d6]`:

| document | fusion score | ranked by |
|---|---:|---|
| d1 | 0.0323 | lexical#1, dense#3 |
| d4 | 0.0320 | lexical#4, dense#1 |
| d2 | 0.0161 | lexical#2 |
| d5 | 0.0161 | dense#2 |
| d3 | 0.0159 | lexical#3 |
| d6 | 0.0156 | dense#4 |

## The mechanism, named

Reciprocal rank fusion gives each matcher's rank a score of
1/(k + rank) and sums across matchers. Two consequences fall out of the
run:

1. **Agreement is rewarded.** d1 and d4 appear in both sets and score
   roughly double the survivors.
2. **The union is preserved.** d2/d3 survive only from lexical and
   d5/d6 only from dense — nothing a matcher retrieved is dropped.

That is the point of hybrid search: coverage without choosing a blind
spot, with shared confidence ranked first.

## How you find it: the fusion-weight audit, executed

Fusion has a knob — the weight between lexical and dense — and the
failure mode the aggregate hides is the weight tuned on the wrong
queries. A head-dominated sweep looks flat, so the team concludes the
weight does not matter, while the tail swings with it. The run
([record](runs/2026-08-07-fusion-audit.md)) emits a 20-query log with
the fused-list NDCG at three weights — lexical-only, balanced,
dense-only — and stratifies the swing:

| stratum | queries | NDCG@w0 | NDCG@w0.5 | NDCG@w1 | mean swing |
|---|---:|---:|---:|---:|---:|
| head | 10 | 0.900 | 0.920 | 0.900 | 0.020 |
| tail | 10 | 0.557 | 0.794 | 0.451 | 0.343 |

The verdict is WEIGHT SWING CONCENTRATED IN THE TAIL: head queries are
covered by either matcher, so the weight moves their score by 0.020;
tail queries swing 0.343 — from 0.451 served dense-only to 0.794
balanced. The flat aggregate sweep is a head artifact. Cormack, Clarke
and Büttcher ("Reciprocal Rank Fusion Outperforms Condorcet and
Individual Rank Learning Methods", SIGIR 2009) is the source for the
RRF mechanism; this audit is the operational check that the fusion's
trust decision is query-dependent. The decision that follows: tune the
weight on the tail, report the swing per stratum, and never ship "the
weight does not matter" from a head-dominated experiment.

## The fix and its trade

The fix is reciprocal rank fusion with a per-stratum weight audit and a
per-set health check — the coverage promise only holds while both
matchers are alive. The executed runs price the failure the fix
removes: fusion rewards agreement (d1 and d4 appear in both sets and
score roughly double the single-source survivors), but the weight
decision is a tail decision — head queries move 0.020 with the weight
while tail queries swing 0.343, from 0.451 served dense-only to 0.794
balanced — and the flat aggregate sweep that concludes "the weight does
not matter" is a head artifact. Cormack, Clarke and Büttcher (SIGIR
2009) established RRF's mechanism: it rewards documents several
rankings place highly.

The trade, named: the weight is a product decision, not a tuning
constant — it states which retrieval failure the platform trusts less
(leaning lexical accepts vocabulary misses; leaning dense accepts
exactness loss) — and it must be tuned on the tail and reported per
stratum. The health check is the other half: without per-matcher
result-count and latency signals, the hybrid silently degrades into
whichever matcher is alive, and the list still looks like a fusion.

## Who owns the loop

The fusion decides which matcher's confidence wins per query; someone
must own that trust decision, and the handoffs are where fusion fails:

- **The fusion or ranking team** owns the weight and the overlap
  contract: how lexical and dense confidence are combined, and the
  per-stratum swing report that shows where the weight decides. It
  owns the knob, and the when-the-fusion-weight-moves detour is its
  failure mode.
- **The retrieval teams** own the two sets being fused: lexical recall
  and dense recall, each with its own blind spot, and each required to
  stay healthy — because the when-one-set-is-empty detour shows the
  hybrid silently degrades into whoever is alive. They own the sets,
  and the audit's tail verdict is their signal.
- **The evaluation or relevance team** owns the overlap-rate
  monitoring: the served overlap between matchers, the disjoint case
  that means one matcher failed, and the head/tail stratification that
  makes the weight decision visible. It owns the measurement, and the
  when-the-sets-disagree-entirely detour is its failure mode.

When the ownership is implicit, the fusion team tunes the weight on an
aggregate sweep, the retrieval teams ship their sets, and nobody owns
the tail — so a flat-looking experiment ships a weight that silently
serves the tail whichever matcher the aggregate happened to prefer.

## Why this belongs in the mission

[Stage 02's rule](../../shared/02-recall/) — a perfect ranker cannot rank an item
that was never retrieved — applies to search verbatim. Hybrid fusion is
how production search keeps both matchers' coverage: the first stage of
the funnel retrieves with every method it has, and downstream ranking
works on the union.

## Evidence boundary

The executed fusion over two hand-built lists (illustrative,
deterministic, equal-weight matchers). It demonstrates the mechanism;
real fusion also needs score calibration between matchers and a health
check per set — the [empty-set detour](when-one-set-is-empty/) shows
what happens without it.

## Check your mental model

Answer each before opening it.

**1. Why do d1 and d4 score roughly double the survivors?**

<details>
<summary>Answer</summary>

Because reciprocal rank fusion sums each matcher's contribution. A
document ranked by both matchers collects two terms; a document in one
set collects one. The fusion is designed so that agreement — both
matchers confident in the same document — is worth more than either
alone.

</details>

**2. Why not just concatenate the two lists?**

<details>
<summary>Answer</summary>

Concatenation keeps coverage but throws away rank information and
duplicates. Fusion keeps the union while making shared documents rise,
so the merged list reflects both matchers' confidence instead of
whichever list happened to be appended second.

</details>

## Next

Forward to [stage 22 — reranking](../22-reranking/) where the fused
list meets a second, more expensive ranker.

A detour from here: [the fusion weight is a trust decision](when-the-fusion-weight-moves/) — the executed weight sweep read: at w=0 the
dense-only winner (d2) takes the top slot, at w=1 the lexical-only
winner (d1) does, so the weight is the product decision about how much
the platform trusts meaning versus exact terms.

Another detour: [the hybrid degrades into whoever is alive](when-one-set-is-empty/) — the executed degradation read: with the dense set
empty the fusion is exactly the lexical ranking, so fusion needs a
health check per matcher.

And a third: [fusion with no agreement to reward](when-the-sets-disagree-entirely/) — when the two matchers return disjoint lists,
RRF interleaves two priors and the page top is a coin flip; the check
is the served overlap rate.
