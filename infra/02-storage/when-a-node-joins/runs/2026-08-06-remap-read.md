# Run — the remap that adding a node costs, read from the recorded shard run

**Date:** 2026-08-06
**Command:** `uv run python core/remap_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the remap was the chapter's recorded 2026-08-01
run).

## Purpose

The storage chapter placed 2,000 keys over 4 nodes, added a 5th, and
measured the real disk remap under modulo and consistent hashing. This run
reads the record and lays out the comparison.

## Output

```
modulo vs consistent-hash, read from the recorded run:
  modulo      remap 0.802 vs ideal 0.200
  consistent  remap 0.180 vs ideal 0.200

real disk remap (write under old placement, move to new):
  modulo      moved 1604 keys, 105119744 bytes, 0.1581s, 634 MB/s
  consistent  moved 360 keys, 23592960 bytes, 0.0398s, 565 MB/s
```

## Notes

- Modulo remaps ~4x the ideal share (0.802 vs the 0.200 a new node should
  take): one node's change rehashes every key. Consistent hashing moves
  only the keys the new node actually takes (0.180).
- The real disk move confirms the fractions: 105 MB under modulo vs 24 MB
  under consistent — a 4.4x difference in bytes moved.
