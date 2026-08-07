---
status: verified
level: applied
verified: 2026-07-27
base: none
---

# Why is the best slate not the top ten items?

**Question:** stage 05 assigned each candidate one scalar value. Why not sort it and show the top ten? Because a page is consumed as a slate: the fifth sports clip is worth less after four similar clips, even when each clip scores well alone.

The artifact is an ordered slate. Its value depends on position and on the items already chosen, so static top-K is no longer the optimization problem. The core script makes that dependency explicit with a position discount and a category mechanism. Slot zero has weight 1.000 in the executed run; slot two has 0.500. A candidate's placement matters, and its marginal value is conditioned on its prefix.

**Before this:** [stage 05's value tree](../05-value-tree/), which gave every
candidate one scalar score — this stage is what happens once you try to turn
a list of scores into a page.

## Search once values become set-level

Try testing every ordered k-item slate exhaustively and you get the correct answer on a tiny catalogue, then hit a wall almost immediately — it is a permutation search. Run beam search instead: it expands prefixes and keeps only the best few partial slates, so beam width becomes a compute-quality dial you turn, not a magic property. Compare each width against exhaustive search on nine candidates and five slots and you get a measured approximation, not an asserted one.

The default run's width-1, width-2, width-3, and width-9 beams all found the 2.2624 exhaustive optimum. That is not proof that a narrow beam is enough; it says this constructed catalogue did not expose an approximation loss. Change the seed, category cap, or catalogue shape before trusting a beam width. A benchmark where a heuristic always wins is normally a benchmark that forgot to contain the hard case.

Treat diversity as a constraint and you get something auditable: cap sports items at two and no slate may violate it. Treat it as an objective penalty instead and you get a trade weight — it discourages repetition but an unusually valuable duplicate can still outweigh it. Run greedy top-K in this harness and watch it produce three sports items; add the cap and it produces at most two; add the penalty and it happens to produce a four-category slate, without promising it will do so for every request. Reach for a constraint when the obligation has an owner; reach for a penalty only when a product owner accepts its trade curve.

<!-- interactive: SlateMixing -->

## Price the ad's displacement

Remember that an ad is not extra inventory — it replaces an organic result at a position. Run the core script and watch it convert expected ad revenue, bid times predicted click probability, into the same utility scale as organic value through an explicit trade rate. That rate is tuned to 3.0 in the synthetic default solely so the demo shows displacement; do not read it as a recommended policy. The run prints revenue and the position-weighted organic user value displaced at each ad-load level.

The engineering obligation is to expose this curve. Where a business chooses to sit on it is a business decision. A system that reports ad revenue but not the organic item it displaced has hidden the cost, not avoided it. This is also why position bias is part of mixing: replacing slot one is not equivalent to replacing slot five, and a slot-allocation system must know the difference.

## Reproduce and scale honestly

```bash
uv run python core/slate_mixing.py
uv run python prod/mmr_assignment.py
```

A detour from here: [what does a mixing weight actually trade off?](when-the-trade-weight-moves/)
measures the constraint-versus-penalty price and the ad curve's knee on the
same catalogue — the two tradeoffs this stage names in prose, run as numbers.

The production path demonstrates maximal marginal relevance with NumPy; other production alternatives are a determinantal point process and an LP/ILP allocation solved by OR-Tools or a commercial solver. All retain the same required accounting: candidate source, slate constraints, position model, ad revenue, and displacement.

This run is a synthetic optimization exercise. Fine-rank values are not calibrated production estimates, and no offline slate metric here has been shown to predict online satisfaction. Stage 07 applies non-negotiable constraints after mixing and records which candidates were removed.

Search also has an ownership boundary. The ranker owns predicted value; the mixer owns the interaction between items and slots; policy owns hard eligibility. Folding all three into one opaque score prevents an operator from saying whether a missing item lost because it was low-value, redundant, blocked, or displaced by paid inventory. Preserve the candidate trace and every marginal score. Without it, later audits cannot reproduce a slate from the inputs that generated it.

The trade curve should be monitored by segment, not just page average. A high-revenue placement can displace an especially valuable organic result for a new user, a sparse category, or a constrained region while looking harmless in aggregate. This lesson does not invent a business optimum. Its durable invariant is simpler: every ad decision records the organic alternative, position, expected revenue, and estimated user value given up.

Do not confuse a category label with all similarity. A taxonomy cap catches obvious repetition, while embeddings, creator identity, language, format, and session intent can reveal redundancy the taxonomy cannot. Adding each signal increases the search state and makes explanations harder, so introduce it only when a measured failure slice requires it. The small core intentionally keeps category as the one causal variable. The production system may use richer marginal-relevance features, but must preserve the ability to answer what caused an item to lose a slot.

Finally, validate the candidate pool before diagnosing mixing. A diverse slate cannot be assembled from a homogeneous recall union. If a constraint repeatedly leaves too few feasible options, the diagnosis belongs upstream in content understanding or recall, not in a more aggressive beam heuristic. This division prevents the mixer from being blamed for a retrieval blind spot it cannot repair.

## Next

[Stage 07 — the rule engine](../07-rule-engine/) applies constraints this
stage does not know about — legal, safety, contractual — after mixing has
already assembled the slate this stage optimized.

A detour from here: [a narrow beam finding the optimum is not proof a beam
is enough](when-the-beam-is-wide-enough/) — the recorded slate run read:
greedy violates the cap, beam widths 1/2/3/9 all match the exhaustive
optimum, and the displacement column prices the ad revenue.

A third detour: [the diverse slate that underperforms](when-diversity-hurts/) — the executed constraint read: forcing a fourth category costs 0.50 of relevance, so diversity is bought with relevance and the weight must price it.
