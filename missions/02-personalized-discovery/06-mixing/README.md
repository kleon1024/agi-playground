---
status: verified
verified: 2026-07-27
base: none
---

# Why is the best slate not the top ten items?

**Question:** stage 05 assigned each candidate one scalar value. Why not sort it and show the top ten? Because a page is consumed as a slate: the fifth sports clip is worth less after four similar clips, even when each clip scores well alone.

The artifact is an ordered slate. Its value depends on position and on the items already chosen, so static top-K is no longer the optimization problem. The core script makes that dependency explicit with a position discount and a category mechanism. Slot zero has weight 1.000 in the executed run; slot two has 0.500. A candidate's placement matters, and its marginal value is conditioned on its prefix.

## Search once values become set-level

Exhaustively testing every ordered k-item slate is the correct answer for a tiny catalogue and becomes impossible quickly: it is a permutation search. Beam search expands prefixes and retains only the best few partial slates. Beam width is therefore a compute-quality control, not a magic property. The harness compares each width with exhaustive search for nine candidates and five slots, so approximation is measured rather than asserted.

The default run's width-1, width-2, width-3, and width-9 beams all found the 2.2624 exhaustive optimum. That is not proof that a narrow beam is enough; it says this constructed catalogue did not expose an approximation loss. Change the seed, category cap, or catalogue shape before trusting a beam width. A benchmark where a heuristic always wins is normally a benchmark that forgot to contain the hard case.

Diversity as a constraint and diversity as an objective penalty are operationally different. A cap of two sports items is auditable: no slate may violate it. A multiplicative decay is a trade weight; it discourages repetition but can be outweighed by an unusually valuable duplicate. In the run, greedy top-K produced three sports items. The cap produced at most two. The penalty created a four-category slate, but made no promise it would do so for every request. Use constraints for obligations with an owner; use a penalty only when a product owner accepts its trade curve.

<!-- interactive: SlateMixing -->

## Price the ad's displacement

An ad is not extra inventory. It replaces an organic result at a position. The core script converts expected ad revenue, bid times predicted click probability, into the same utility scale as organic value through an explicit trade rate. That rate is tuned to 3.0 in the synthetic default solely so the demo shows displacement; it is not a recommended policy. The run prints revenue and the position-weighted organic user value displaced at each ad-load level.

The engineering obligation is to expose this curve. Where a business chooses to sit on it is a business decision. A system that reports ad revenue but not the organic item it displaced has hidden the cost, not avoided it. This is also why position bias is part of mixing: replacing slot one is not equivalent to replacing slot five, and a slot-allocation system must know the difference.

## Reproduce and scale honestly

```bash
uv run python core/slate_mixing.py
uv run python prod/mmr_assignment.py
```

The production path demonstrates maximal marginal relevance with NumPy; other production alternatives are a determinantal point process and an LP/ILP allocation solved by OR-Tools or a commercial solver. All retain the same required accounting: candidate source, slate constraints, position model, ad revenue, and displacement.

This run is a synthetic optimization exercise. Fine-rank values are not calibrated production estimates, and no offline slate metric here has been shown to predict online satisfaction. Stage 07 applies non-negotiable constraints after mixing and records which candidates were removed.

Search also has an ownership boundary. The ranker owns predicted value; the mixer owns the interaction between items and slots; policy owns hard eligibility. Folding all three into one opaque score prevents an operator from saying whether a missing item lost because it was low-value, redundant, blocked, or displaced by paid inventory. Preserve the candidate trace and every marginal score. Without it, later audits cannot reproduce a slate from the inputs that generated it.

The trade curve should be monitored by segment, not just page average. A high-revenue placement can displace an especially valuable organic result for a new user, a sparse category, or a constrained region while looking harmless in aggregate. This lesson does not invent a business optimum. Its durable invariant is simpler: every ad decision records the organic alternative, position, expected revenue, and estimated user value given up.

Do not confuse a category label with all similarity. A taxonomy cap catches obvious repetition, while embeddings, creator identity, language, format, and session intent can reveal redundancy the taxonomy cannot. Adding each signal increases the search state and makes explanations harder, so introduce it only when a measured failure slice requires it. The small core intentionally keeps category as the one causal variable. The production system may use richer marginal-relevance features, but must preserve the ability to answer what caused an item to lose a slot.

Finally, validate the candidate pool before diagnosing mixing. A diverse slate cannot be assembled from a homogeneous recall union. If a constraint repeatedly leaves too few feasible options, the diagnosis belongs upstream in content understanding or recall, not in a more aggressive beam heuristic. This division prevents the mixer from being blamed for a retrieval blind spot it cannot repair.
