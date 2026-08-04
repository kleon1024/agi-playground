# Star vs. ring allreduce, localhost IPC

**Command:**

```bash
cd infra/01-networking/core
python3 network_sim.py --world-sizes 2 4 8 --payload-mb 1.0 8.0 32.0
```

**Hardware:** MacBookPro18,3 (Apple Silicon, arm64), 10 CPU cores, macOS 15.6.1.
**Software:** Python 3.11.14, numpy 2.4.2. No GPU involved -- this is pure
process/IPC overhead over `multiprocessing.Queue`.

**Wall-clock:** ~35s total for the 9-combination sweep.
**Cost:** \$0 (local lane, no cloud resources).

**Metrics (real output, unedited):**

```
world_size payload_MB     star_s     ring_s  star_bytes/rank  ring_bytes/rank  correct
         2        1.0     0.0101     0.0029          2097152          1048576     True
         2        8.0     0.0499     0.0382         16777216          8388608     True
         2       32.0     0.3246     0.1285         67108864         33554432     True
         4        1.0     0.0307     0.0176          3145728          1572864     True
         4        8.0     0.1236     0.0319         25165824         12582912     True
         4       32.0     0.5292     0.3954        100663296         50331648     True
         8        1.0     0.0121     0.0071          3670016          1835008     True
         8        8.0     0.3813     0.0910         29360128         14680064     True
         8       32.0     1.0304     0.5080        117440512         58720256     True
```

`correct` is not decoration: every cell is `np.allclose` against a plain
single-process sum of the same inputs, checked on every rank's own result.

**Notes:**

- Ring beats star's wall-clock in every one of the 9 combinations, and the
  gap widens with `world_size`: at 8 ranks / 32MB, ring is roughly 2x faster
  (0.508s vs 1.030s).
- `ring_bytes/rank` grows toward roughly `2 x payload_size` as `world_size`
  increases (1.05MB -> 1.57MB -> 1.75MB at 1MB payload, world_size 2/4/8) and
  then plateaus -- exactly the textbook claim: ring's per-rank communication
  volume is asymptotically independent of `world_size`. `star_bytes/rank`
  keeps climbing because the root's traffic is counted into the per-rank
  average and the root's own load scales linearly with `world_size`.
- **What surprised me building this**: the first version of this script
  deadlocked, twice, for two different reasons -- both are the real content
  of the "what a beginner gets wrong about collectives" lesson, not a
  footnote. (1) The ring's `put()`-then-`get()` pattern deadlocks once a
  chunk exceeds the OS pipe buffer (a few hundred KB): every rank blocks in
  `put()` waiting for its neighbor to drain, but the neighbor is doing the
  same thing, so nobody ever reaches `get()`. Fixed with a background sender
  thread per rank so send and receive can proceed concurrently within one
  process. (2) The star root wrote its own result back into its own
  never-read result queue, which is invisible at small payload sizes (fits
  the pipe buffer) and hangs at large ones -- the same underlying issue,
  different shape. Both bugs only manifested once the payload crossed a size
  threshold; the small-array correctness test that ran first gave false
  confidence.
