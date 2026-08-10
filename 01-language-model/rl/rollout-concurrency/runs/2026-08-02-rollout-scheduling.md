# Run record: lockstep vs. asynchronous rollout scheduling

**Command:**

```bash
cd 01-language-model/04-rl/rollout-concurrency/core
python3 rollout_scheduling.py --workers 2,4,8 --n-trajectories 40 --trials 3 --seed 0 --out ../runs
```

**Hardware:** local dev box, CPU only (thread pool over NumPy BLAS matmul),
no GPU, \$0. Total wall-clock for all three worker counts: under 1 second.

**What ran:** 40 synthetic "trajectories" per trial, each doing 1-40 real
`200x200` matmul reps (80% drawn from 2-4 reps, 20% from a 20-40 rep long
tail — the heavy-tailed episode-length shape described in the chapter). The
same trajectory-length list is generated once per trial and fed to both the
`lockstep` and `async` policies, so any measured difference is the scheduling
policy, not a different random draw. 3 trials per worker count, alternating
which policy runs first, plus a throwaway warmup pass before any timed trial
(matching `foundations/04-distributed-training/orchestration`'s own warmup discipline).

**Full output:**

```
=== workers=2 trajectories=40 trials=3 ===
lockstep makespan: {'mean': 0.0394980829829971, 'min': 0.035248541040346026, 'max': 0.044815832981839776}
async makespan:    {'mean': 0.02288505535883208, 'min': 0.020427166018635035, 'max': 0.024783042026683688}
async speedup: 1.73x

=== workers=4 trajectories=40 trials=3 ===
lockstep makespan: {'mean': 0.030745277646929026, 'min': 0.025571333011612296, 'max': 0.03753345902077854}
async makespan:    {'mean': 0.020716291309023898, 'min': 0.018146707909181714, 'max': 0.02256800001487136}
async speedup: 1.48x

=== workers=8 trajectories=40 trials=3 ===
lockstep makespan: {'mean': 0.026285832980647683, 'min': 0.021553833037614822, 'max': 0.030798082938417792}
async makespan:    {'mean': 0.020273360734184582, 'min': 0.016648166114464402, 'max': 0.02451150002889335}
async speedup: 1.30x
```

Full per-trial trajectories are in `rollout-scheduling-result.json` in this
directory.

**Reading the trend:** async's speedup over lockstep shrinks monotonically as
worker count rises (1.73x -> 1.48x -> 1.30x at 2, 4, 8 workers respectively)
against the same fixed 40-trajectory workload. Fewer workers means more
sequential lockstep batches (20 batches of 2, vs. 5 batches of 8) — more
batch boundaries means more chances for one long-tail trajectory to strand
its batch-mates idle. Async has no batch boundary at all, so its own
makespan is comparatively stable across worker counts (0.0229s / 0.0207s /
0.0203s) while lockstep's drops faster as more workers absorb the same
straggler cost in parallel. Neither policy's ranges fully separate at n=3
trials per cell — this is a small, fast, illustrative run, not a
statistically tight one; see "what this does not establish" in the README.
