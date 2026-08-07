# Run — the cold-start exploration sweep

**Date:** 2026-08-08
**Command:** `uv run python core/cold_start.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.17s.
**Cost:** \$0 (local lane).

## Purpose

The stage's audit shows greedy on lifetime CTR crowns the stale winner
and that the fix is a recency-aware estimator. This detour asks the
exploration side of the same question: a new creative has no history,
so how much traffic does it take to correct its cold-start prior — and
does exploration alone fix selection? It sweeps epsilon over 0.00 to
0.20 with the naive lifetime-average estimator: a mature creative
(lifetime 0.06, true rate decaying toward 0.025) versus a new creative
(true rate 0.04, pessimistic cold-start prior 0.02), 20,000 placements,
fixed seed.

## Output

```
cold-start audit: 20,000 placements, fixed seed
creative A: lifetime CTR 0.06, true rate decays 0.06 -> 0.025
creative B: true rate 0.04, pessimistic prior 0.02 (thin)

   epsilon  served B  B estimate   clicks clicks/imp
      0.00         0      0.0200      625     0.0312
      0.05       475      0.0435      667     0.0333
      0.10      1019      0.0357      645     0.0323
      0.20      1994      0.0358      653     0.0326

reading: raising epsilon corrects B's estimate (0.02 toward
0.04) but clicks barely move. The corrected estimate loses to A's
sticky 0.06 lifetime average, so the greedy arm still serves the
stale winner. Exploration learns the truth; the estimator decides
whether selection can use it — pair cold-start traffic with a
recency-aware estimate or the correction is wasted.
```

## Notes

- At epsilon 0.00 the new creative is never served: its 0.02 prior
  loses to A's 0.06 lifetime average, so the campaign earns 625 clicks
  all from the worn creative and never learns B.
- Raising epsilon serves B 475 to 1,994 placements and corrects its
  estimate from 0.02 toward 0.04 — but clicks move only 625 to 653 to
  667. The corrected estimate is still below A's sticky lifetime
  average, so the greedy arm keeps serving the stale winner.
- The reading is the operational lesson: exploration corrects the
  cold-start prior; the estimator decides whether selection can use
  the correction. Pair cold-start traffic with a recency-aware
  estimate or the exploration budget is wasted.
- Clicks drawn as Bernoulli from true rates at serve time; wear is a
  declared decay function. Illustrative and deterministic per seed,
  not real creative logs.
