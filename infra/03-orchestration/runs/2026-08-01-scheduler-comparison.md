# Run: scheduler policy comparison (FIFO vs priority)

**Command:**
```bash
cd infra/03-orchestration/core
python scheduler.py --slots 2 --trials 3 --out ../runs
```

**Hardware:** local dev box (CPU only, no GPU involved — this chapter's
"slots" are threads, not devices).

**Software:** Python 3.11, NumPy 2.4.2.

**Wall-clock:** ~0.2s total (6 trials x ~0.02-0.04s each, plus warmup).

**Cost:** \$0 (local lane, CPU only).

**Metrics** (see `scheduler-result.json` in this directory for the full
per-trial, per-job breakdown):

```
                    FIFO                          Priority
makespan            0.0182s (0.0171-0.0195)       0.0187s (0.0169-0.0214)
high-priority wait  0.0074s (0.0069-0.0079)       0.0012s (0.0011-0.0012)
low-priority wait    0.0074s (0.0069-0.0079)       0.0094s (0.0088-0.0099)
```

**Notes:** the first version of this script (no warmup, no alternating
trial order) measured FIFO's makespan at roughly 2x priority's — a
cold-start artifact (BLAS thread-pool + page-cache warmup absorbed entirely
by whichever policy ran first), not a real scheduling effect. Adding a
throwaway `warmup()` call before any timed trial, and alternating which
policy runs first each trial, removed the artifact: makespan converges to
statistically indistinguishable between policies, exactly as the mechanism
predicts (a scheduler reorders completion, it does not create throughput).
The high-priority-wait effect (FIFO ~0.0074s vs priority ~0.0012s, non-
overlapping ranges across 3 trials each) survived this correction and is the
real result this chapter reports.
