# Run — the all-reduce that makes ranks agree, read from the recorded run

**Date:** 2026-08-06
**Command:** `uv run python core/rank_agreement.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the collectives were the chapter's recorded
2026-07-27 run).

## Purpose

The distributed chapter ran real DDP and ZeRO-1 collectives on four CPU
processes. This run reads the record and lays out the three numbers that
make data parallelism work.

## Output

```
  pre-all-reduce gradient delta: 0.000119
  post-all-reduce divergence: asserted zero across ranks
  DDP optimizer state: 2.62 MB vs parameters 1.31 MB (2.00x)
  ZeRO-1 optimizer state: 1.05 MB (sharded /4)
```

## Notes

- The 0.000119 delta is the whole point of DDP: ranks see different data so
  their gradients differ, and the all-reduce is what makes them identical
  again (asserted to zero divergence).
- Optimizer state at 2x parameters is why ZeRO exists; sharding it drops
  each rank's share from 2.62 MB to 1.05 MB without changing the math.
