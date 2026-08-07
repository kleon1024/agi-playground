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

## The mechanism, named

The cascade costs a fraction of exhaustive scoring, and every stage
exists to buy the next one a smaller problem: recall cuts 10M to 100k,
pre-rank cuts 100k to 1k, fine-rank cuts 1k to 50, mixing scores the
survivors. Each stage's budget is candidates times per-candidate cost,
and the product stays flat at 1.0 by design — the whole architecture is
an arithmetic answer to a question the fine model alone cannot afford.
Cost per query is the unit that turns that arithmetic into a budget,
which is what capacity planning (stage 49) spends.

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

## Next

The query has a price; the next stages spend it deliberately. A detour
from here: [the cache pays when the hit rate is a cost decision](when-the-cache-pays/)
— the executed read: at 90% hits the per-served cost drops to 0.44 units
from 4.0.

Another detour: [the model is too big when the last point of quality
doubles the bill](when-the-model-is-too-big/) — the executed read: the
large model adds 0.013 NDCG and doubles the daily cost of fine-rank.
