---
status: verified
level: applied
base: scratch
label: When the index is ANN
verified: 2026-08-07
---

# Approximate is the only feasible index at scale

**Question:** [stage 20's dense retrieval](../) retrieves by vector
similarity, but against how many vectors? This chapter reads the
executed scan-cost curve and asks when exact search stops being
feasible.

**Before this:** [stage 20 — dense retrieval](../) and its executed
cosine model.

## The curve, executed

The run ([record](runs/2026-08-07-ann-read.md)) reads recall against
the scanned fraction of a 100,000-item index:

| scanned | recall |
|---|---:|
| 100 | 0.001 |
| 1,000 | 0.010 |
| 10,000 | 0.100 |
| 100,000 | 1.000 |

## The reading

Exact retrieval scans the whole index — full recall, full latency. ANN
scans a fraction and accepts a recall loss at the boundary. The curve
is linear here: 1,000 scanned of 100,000 returns 0.010 recall. The
index size decides which is even feasible: when the catalogue fits the
latency budget, exact search is an option; when it does not, ANN is not
a quality choice but the only working choice, and the recall loss at
the boundary is the price of scale.

## Evidence boundary

The executed linear scan model (illustrative, deterministic, uniform
matches). It demonstrates the shape; real ANN recall curves are
measured per index configuration, and the search's p95 budget decides
where on the curve the system can afford to sit.

## Check your mental model

Answer each before opening it.

**1. Why is exact search not the default at scale?**

<details>
<summary>Answer</summary>

Because exact search means scanning every vector, and scanning a
100,000-item index inside a request budget is not possible — the
mission's latency guardrail applies to search too. ANN trades a
measured recall loss for a scan that fits the budget; the question is
which side of that trade the product can accept.

</details>

**2. What does the linear curve say about the trade?**

<details>
<summary>Answer</summary>

That recall grows exactly with the scanned fraction in this model — no
free lunch, but also a predictable price. The system's p95 budget fixes
the scan it can afford, and the curve says what recall that scan buys.
Real ANN indexes bend the curve with structure, which is measured per
configuration.

</details>

## Next

Back to [stage 20](../), which retrieves by embedding. The
[stale-embedding detour](../when-the-embedding-is-stale/) shows the
indexing-side cost: items without a vector are unreachable whatever the
index structure.
