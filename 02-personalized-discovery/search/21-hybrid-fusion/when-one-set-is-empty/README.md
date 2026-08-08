---
status: verified
level: applied
base: scratch
label: When one set is empty
verified: 2026-08-07
---

# The hybrid degrades into whoever is alive

**Question:** [stage 21's hybrid fusion](../) promises coverage from two
matchers. This chapter reads the executed degradation case and asks
what happens when one matcher returns nothing.

**Before this:** [stage 21 — hybrid fusion](../) and its executed
reciprocal-rank-fusion model.

## The degradation, executed

The run ([record](runs/2026-08-07-empty-set-read.md)) fuses with both
matchers, then with the dense set empty:

| case | top of list |
|---|---|
| two matchers | d2, d1, d4, d3, d5 |
| dense empty | d1, d2, d3 |

## The reading

With both matchers, d2 ranks top on agreement; with the dense set empty,
the fusion is just the lexical ranking. The hybrid degrades silently
into whichever matcher is alive. Nothing flags the change — the output
still looks like a fused list — which is why fusion needs a health
check per set: the system has to know it lost a matcher, because the
coverage promise stage 21 makes is only true while both sets are alive.

## The fix and its trade

The fix is a health check per matcher — result counts and latency as
served signals — because the coverage promise stage 21 makes is only
true while both sets are alive. The executed degradation prices the
failure: with both matchers the fused list leads d2, d1, d4, d3, d5;
with the dense set empty it is simply the lexical ranking d1, d2, d3.
Nothing flags the change — the output still looks like a fused list —
while every document that only dense retrieval would have found,
including the vocabulary-mismatch matches fusion exists to keep, is
gone.

The trade, named: per-matcher monitoring costs signals and alerting on
each retrieval path, and the alternative is a silent recall loss that
only shows up as a user-visible gap — an empty or stale matcher is
indistinguishable from a working one at the list level. The coverage
contract of hybrid search is a liveness property, and liveness needs
the monitor, not the fusion formula.

## Who owns the loop

- **The retrieval teams** own their sets' health — an empty or stale
  matcher is their artifact failing, not the fusion's.
- **The serving team** owns the per-matcher result-count and latency
  monitoring that raises the alarm.
- **The evaluation team** owns the coverage-promise read that converts a
  degraded list into a recall number.

## Evidence boundary

The executed degradation over two hand-built lists (illustrative,
deterministic). It demonstrates the failure mode; real systems monitor
per-matcher result counts and latency as signals, because an empty or
stale matcher is a silent recall loss.

## Check your mental model

Answer each before opening it.

**1. Why is the degradation dangerous if the output still looks fine?**

<details>
<summary>Answer</summary>

Because the list looks normal but the coverage contract changed. With
the dense set empty, every document that only dense retrieval would
have found is gone — including the vocabulary-mismatch matches stage 21
exists to keep. The ranking looks healthy while recall quietly
collapses, which is exactly the failure a health check exists to catch.

</details>

**2. What should the health check watch?**

<details>
<summary>Answer</summary>

Per-set signals: result count per matcher, matcher latency, and vector
store freshness. An empty set, a timed-out matcher, or a stale index
each break one side of the fusion, and the check has to say which
matcher is missing before the fused list can be interpreted.

</details>

## Next

Back to [stage 21](../), which fuses the two sets. The
[fusion-weight detour](../when-the-fusion-weight-moves/) shows the
healthy side of the same lever: what the blend weight decides when both
sets are alive.
