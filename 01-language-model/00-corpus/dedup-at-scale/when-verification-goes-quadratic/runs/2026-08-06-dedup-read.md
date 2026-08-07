# Run — the quadratic verification tail, read from the recorded scaling run

**Date:** 2026-08-06
**Command:** `uv run python core/dedup_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the scaling run was the chapter's recorded
2026-08-01 run).

## Purpose

The dedup chapter ran MinHash hashing and LSH bucket verification at
corpus sizes 1k, 4k, 16k, 48k. This run reads the record and lays out the
linear-vs-quadratic pattern.

## Output

```
  n=  1000  hash     1.41s  verify     0.04s  pairs      4079  near-dupes      3778
  n=  4000  hash     5.64s  verify     0.64s  pairs     66925  near-dupes     62816
  n= 16000  hash    22.83s  verify     9.93s  pairs   1080164  near-dupes   1009939
  n= 48000  hash    67.65s  verify    92.40s  pairs   9655349  near-dupes   9028482
  n x4.0 -> hash_time x4.01, verify_time x16.22
```

## Notes

- Hashing is per-document and grows linearly (x4.01 for x4 corpus);
  verification is per-pair and grows quadratically (x16.22) because the
  pair count scales with n^2.
- The LSH trade is accepting a bounded false-negative risk to keep the
  verify step from exploding: at 48k the verify time has already overtaken
  hashing (92.4s vs 67.7s).
