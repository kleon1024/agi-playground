# Run — best-of-N null inflation across search breadth

**Date:** 2026-08-06
**Command:** `uv run python core/best_of_n_null.py --replicates 200`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only (plus the stage 00 Yahoo /
EDGAR HTTP fetch).
**Software:** Python 3.11.14 via uv; numpy; the stage's own
`signal_search.py` reused for fetch, forward returns, and permutation.
**Wall-clock:** ~2 minutes (fetch + 200 replicates x 5,408 candidate draws).
**Cost:** \$0 (local lane).

## Purpose

Stage 01's recorded run measured the permutation null at the grid it actually
searched: 32 candidates. This run measures the same null at the breadth a
real idea library produces — 256, 1,024, and 4,096 candidates — to answer
"search over 1,000 signals finds losers" with a measured curve instead of an
assertion. The machinery is identical to the stage's `run_permutation_null`:
forward returns are permuted within each date (destroying any real
signal-return pairing), and candidates are scored against the permutation.
The only difference is the candidate generator: pure-noise standard-normal
exposures per name instead of the momentum/volatility/value families.

## Metrics

The ten-name universe fetched with 59 usable monthly cross-sections (the
recorded run had 60; the window drifts between pulls, as its run record
noted). 200 seeded replicates per grid size:

| grid size N | best-of-N IC mean | median | max | P(best >= 0.0947) |
|---:|---:|---:|---:|---:|
| 32 | 0.0904 | 0.0891 | 0.1721 | 0.400 |
| 256 | 0.1240 | 0.1215 | 0.1834 | 0.960 |
| 1,024 | 0.1399 | 0.1378 | 0.1897 | 1.000 |
| 4,096 | 0.1572 | 0.1542 | 0.2088 | 1.000 |

0.0947 is the best in-sample IC of the 32 real variants in the recorded
stage-01 run. Under pure-noise candidates, a search that tries 256 ideas
beats that number 96% of the time, and a 1,024-idea search beats it in every
one of the 200 replicates.

## Calibration against the recorded null

The recorded run's best-of-32 null (the real grid, 300 replicates) had mean
0.0818; this run's synthetic best-of-32 is 0.0904. The gap is expected and is
part of the result: the real 32 variants are structurally similar to each
other (momentum lookbacks, volatility windows, value freshness), so their
ICs are correlated and their best-of-null is *lower* than what i.i.d. noise
candidates produce. The synthetic curve is therefore the honest null for
"I tried N independent ideas," not for "I tried N variants of three
families" — the chapter reads the two numbers side by side.

## Notes

- The inflation curve is a pure order-statistic effect: under a null, the
  maximum of N draws grows with N even though every draw is noise. The mean
  best-of-N rises 0.090 -> 0.124 -> 0.140 -> 0.157.
- The threshold probability saturates: 0.40 @ 32, 0.96 @ 256, 1.00 @ 1,024+.
  The measured winner 0.0947 is only "special" relative to a 32-idea search;
  at 1,000-idea breadth it is the expectation, not an edge.
- This is a synthetic-noise null on a ten-name, continuously listed,
  survivorship-limited universe. It demonstrates search accounting; it is
  not investment evidence, exactly as stage 01's run record says of its own
  null.
