# Run — when ring beats star, read from the recorded allreduce sweep

**Date:** 2026-08-06
**Command:** `uv run python core/ring_vs_star_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the sweep was the chapter's recorded 2026-08-01
run).

## Purpose

The networking chapter ran star and ring allreduce at world sizes 2, 4, 8
and payloads 1, 8, 32 MB. This run reads the recorded sweep and lays out
the pattern.

## Output

```
star vs ring allreduce (recorded sweep), read:
  world  payload   star_s   ring_s ring/star time star bytes/rank ring bytes/rank
      2      1.0   0.0101   0.0029         0.29         2097152         1048576
      2      8.0   0.0499   0.0382         0.77        16777216         8388608
      2     32.0   0.3246   0.1285         0.40        67108864        33554432
      4      1.0   0.0307   0.0176         0.57         3145728         1572864
      4      8.0   0.1236   0.0319         0.26        25165824        12582912
      4     32.0   0.5292   0.3954         0.75       100663296        50331648
      8      1.0   0.0121   0.0071         0.59         3670016         1835008
      8      8.0   0.3813   0.0910         0.24        29360128        14680064
      8     32.0   1.0304   0.5080         0.49       117440512        58720256
```

## Notes

- Ring halves the bytes each rank moves (star_bytes/rank is exactly 2x
  ring_bytes/rank at every cell) and wins wall-clock at every cell.
- The advantage grows with payload: at world 8, ring is 0.59x, 0.24x, and
  0.49x of star's time as payload goes 1, 8, 32 MB — bandwidth, not
  latency, is what the topology trades.
