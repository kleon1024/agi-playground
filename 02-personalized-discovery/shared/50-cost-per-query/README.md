---
status: verified
level: applied
base: scratch
label: Cost per query
verified: 2026-08-07
---

# Cost per query is the budget capacity planning spends

**Question:** stage 49 sized the machine. This stage asks what a query
costs to serve, and answers: the cascade is arithmetic with a price tag —
each stage scores a smaller set with a more expensive model, and the
cost of a query is the sum over stages of candidates times per-candidate
cost.

**Before this:** [stage 08 — serving](../08-serving/) for the cascade
this cost describes, and [stage 22 — reranking](../../search/22-reranking/) for the
latency-budget split between stages.

## The cascade arithmetic, executed

The run ([record](runs/2026-08-07-cost-per-query.md)) prices each stage
in cost units:

| stage | candidates | per-candidate cost | stage cost |
|---|---|---:|---:|
| recall (ann) | 100,000 | 0.00001 | 1.0 |
| pre-rank | 1,000 | 0.00100 | 1.0 |
| fine-rank | 50 | 0.02000 | 1.0 |
| mixing | 20 | 0.05000 | 1.0 |

Total per query: 4.0 units. Exhaustive fine-rank of 10M items: 200,000
units. Per 1M queries, the cascade costs 4,000,000 units; exhaustive
scoring costs 200,000,000,000.

<!-- interactive: CostPerQuery -->

## The mechanism, named

The cascade costs a fraction of exhaustive scoring, and every stage
exists to buy the next one a smaller problem: recall cuts 10M to 100k,
pre-rank cuts 100k to 1k, fine-rank cuts 1k to 50, mixing scores the
survivors. Each stage's budget is candidates times per-candidate cost,
and the product stays flat at 1.0 by design — the whole architecture is
an arithmetic answer to a question the fine model alone cannot afford.
Cost per query is the unit that turns that arithmetic into a budget,
which is what capacity planning (stage 49) spends.

## How you find it: the per-stage cost attribution at scale, executed

The flat 1.0-each design is a property of one catalogue size. The run
([record](runs/2026-08-07-cost-per-query.md)) prices the cascade at
10M, 100M, and 1B items — recall candidates scale sublinearly with the
catalogue while the later stages keep fixed budgets — and the audit
([record](runs/2026-08-07-cost-audit.md) —
[`prod/cost_audit.py`](prod/cost_audit.py)) attributes the query budget
per stage the way a cost team reads sampled traces:

| catalogue | recall (ann) | pre-rank | fine-rank | mixing | total |
|---:|---:|---:|---:|---:|---:|
| 10M | 1.00 (25%) | 1.00 (25%) | 1.00 (25%) | 1.00 (25%) | 4.00 |
| 100M | 2.51 (46%) | 1.00 (18%) | 1.00 (18%) | 1.00 (18%) | 5.51 |
| 1B | 6.31 (68%) | 1.00 (11%) | 1.00 (11%) | 1.00 (11%) | 9.31 |

The verdict is RECALL DOMINANT: recall owns 68% of the query budget at
the 1B catalogue against 25% at 10M. The flat design holds only at the
declared size; as the catalogue grows, the ANN index's candidate set is
what the budget follows, and optimizing fine-rank before recall is
optimizing the wrong stage. This is the cost half of the same
attribution discipline the mission applies to relevance — the
levers that move the attributed budget are the ones the compression
line of work formalized — Han, Mao and Dally, "Deep Compression:
Compressing Deep Neural Networks with Pruning, Trained Quantization and
Huffman Coding" (ICLR 2016) — cheaper per-candidate models, plus the
candidate-budget cuts that reduce the volume itself.

## The fix and its trade

The fix is to re-attribute the query budget per stage whenever the
catalogue or the model changes, and to optimize the stage the
attribution says is dominant. The audit prices the repair — recall owns
25 percent of the query budget at 10M items and 68 percent at 1B
(total 4.00 to 9.31), so tuning fine-rank before recall is optimizing
the wrong stage, and the same attribution discipline the mission applies
to relevance has to apply to cost. The levers are cheaper per-candidate
models (compression) and candidate-budget cuts that reduce the volume
itself.

The trade is that every lever moves quality against money, and the
attribution is only as fresh as the last measurement. The large-model
detour prices the quality side: a bigger fine-ranker adds 0.013 NDCG and
doubles the daily cost of the stage. The cache lever is a head discount,
not a capacity plan: unique tail queries never hit, so 30 percent of
traffic still pays the full 4.0 units while the blended number reads
1.91. The attribution itself needs sampled per-stage spans, and the
50,000x gap that justified the funnel was measured at a catalogue size
that no longer exists — which is why the cost team's re-attribution,
not the launch-day ratio, is the number the budget decision is
denominated in.

## Who owns the loop

The attribution produces a number; someone must own what happens when
the scale moves, and the handoff is where the budget drifts:

- **The serving platform team** owns the cost measurement: the sampled
  per-stage spans, the candidate counts per query, and the
  attribution table that says which stage owns the budget. It owns the
  instrument, not the fix.
- **The ranking team** owns the stage tradeoffs: the candidate budget
  per stage, the model size per stage, and the decision to move cost
  between stages (the model-is-too-big detour). It owns the quality
  side of the trade.
- **The catalogue team** owns the growth curve: the recall candidates
  that scale with the catalogue, and the ANN index quality that decides
  whether recall's growing share buys relevance. It owns the input the
  attribution reads.

When the ownership is implicit, each team optimizes its own stage: the
ranking team tunes fine-rank because that is the model it owns, while
recall's share grows unseen with the catalogue — the budget drifts to
the stage nobody owns, and the "50,000x gap" that justified the funnel
is measured at the size that no longer exists.

## Why this belongs in the mission

The mission's funnel was justified in the README as "forced by
arithmetic". This stage makes the arithmetic explicit and measured: the
cascade's cost is 4 units against 200,000 for exhaustive scoring, a
50,000x gap per query. Every later stage — a bigger model, a deeper
cache, a second experiment — is a decision about how to spend that
budget, and this is the number the decision is denominated in.

## Evidence boundary

The executed arithmetic over declared candidate counts and per-candidate
costs (illustrative, deterministic). It demonstrates the structure; real
costs must be measured per stage on the live path — model inference,
index reads, network — and re-priced when the model or the traffic mix
changes.

## Check your mental model

Answer each before opening it.

**1. Why do all four stages cost exactly 1.0?**

<details>
<summary>Answer</summary>

Because each stage is sized so candidates times per-candidate cost lands
at the same budget: 100k times 0.00001, 1k times 0.001, 50 times 0.02,
20 times 0.05. The cascade is engineered to spend the same per stage —
the expensive model on a tiny set, the cheap model on a huge one. The
equality is the design, not a coincidence.

</details>

**2. What does the exhaustive comparison actually prove?**

<details>
<summary>Answer</summary>

That the cascade exists because exhaustive scoring is unaffordable: 200,000
units per query, or 200 billion units per million queries, against the
cascade's 4 million. It proves the funnel is not tradition — it is the
difference between a service that can run and one that cannot, and the
ratio is the standing justification for every stage the mission built.

</details>

**3. Why does the dominant stage move with the catalogue?**

<details>
<summary>Answer</summary>

Because recall is the only stage whose candidate set scales with the
catalogue: the ANN index serves more candidates as the catalogue grows
(100k at 10M, 631k at 1B here), while pre-rank, fine-rank, and mixing
hold fixed budgets. Recall's share of the query cost therefore grows
from 25% to 68% across the scanned sizes, and the "flat 1.0-each"
design is a point-in-time property, not a law — which is why the audit
re-attributes the budget when the catalogue or the model changes.

</details>

## Next

The query has a price; the next stages spend it deliberately. A detour
from here: [the cache pays when the hit rate is a cost decision](when-the-cache-pays/)
— the executed read: at 90% hits the per-served cost drops to 0.44 units
from 4.0.

Another detour: [the model is too big when the last point of quality
doubles the bill](when-the-model-is-too-big/) — the executed read: the
large model adds 0.013 NDCG and doubles the daily cost of fine-rank.

A third detour: [the cache discounts the head and leaves the tail
paying the full cascade](when-the-tail-misses/) — the executed read:
unique tail queries never hit, so 30% of traffic still pays 4.0 units
while the blended number says 1.91.
