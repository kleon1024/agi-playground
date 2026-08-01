---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Orchestration
---

# A scheduler doesn't do more work. It decides whose work happens first.

**Goal:** understand what a GPU job scheduler actually buys you, and verify
it, without a real cluster — a fixed pool of 2 worker slots on one CPU is
enough to make dispatch order, not compute, the thing under test.

Every lesson in [`infra/`](../README.md) so far has been a runbook: how to
reach the local 4090, when to reach for Modal instead. Both docs describe a
*single* job running on a *known* lane. Neither says what happens when more
jobs want a slot than there are slots — which is the actual daily condition
of any shared GPU pool, including a future version of this repository's own
compute lanes if more than one lesson ever wants the 4090 at once.

**Before this:** [`platform/training/01-distributed/`](../../platform/training/01-distributed/)
established that distributed *training* mechanics (all-reduce, sharding) are
CPU-simulable without real GPUs. This chapter asks the same question one
layer up: is *scheduling* — deciding which job gets a slot next — also
simulable without a real cluster? It is, because scheduling is a decision
about order, and order has consequences you can measure on any machine.

```bash
cd core && python scheduler.py --slots 2 --trials 3 --out ../runs
```

## The one idea in job scheduling

A scheduler with `N` slots and `M > N` pending jobs cannot make the jobs
finish faster in total — the total compute is fixed. What it controls is
**which job finishes first**. `core/scheduler.py` runs the exact same 10-job
batch (3 high priority, 7 low priority, interspersed — not front-loaded) over
2 worker slots, real CPU-bound work (a real matmul loop, timed with
`time.perf_counter`, not `time.sleep`), under two policies:

- **FIFO** — dispatch in arrival order, ignore priority entirely.
- **Priority** — sort the pending queue by priority once, always dispatch
  the highest-priority job still waiting.

Measured over 3 trials, alternating which policy runs first each trial (so
neither absorbs a one-time cold-start cost the other doesn't):

```
                    FIFO                          Priority
makespan            0.0182s (0.0171-0.0195)       0.0187s (0.0169-0.0214)
high-priority wait  0.0074s (0.0069-0.0079)       0.0012s (0.0011-0.0012)
low-priority wait    0.0074s (0.0069-0.0079)       0.0094s (0.0088-0.0099)
```

Two things to read off this table, and the second is the one that matters
more:

1. **High-priority wait drops by roughly 6x** under the priority policy, and
   the two policies' ranges do not overlap — a real, reproducible effect,
   not noise.
2. **Makespan barely moves** (0.0182s vs 0.0187s, well within each policy's
   own trial-to-trial spread). Priority scheduling does not make the total
   batch finish faster. It reassigns *whose* wait shrinks and whose grows —
   low-priority wait rises from 0.0074s to 0.0094s, almost exactly the
   amount high-priority wait fell. A scheduler is a reallocation mechanism,
   not a throughput mechanism.

## Why the first version of this measurement was wrong

The first run of this comparison (before the warmup pass and alternating
trial order existed) showed FIFO's makespan at roughly *double* priority's —
0.0389s vs 0.0202s. That was not a scheduling effect. FIFO ran first in that
version, absorbing one-time NumPy BLAS thread-pool warmup and page-cache
cold-start cost that priority — running second, against an already-warm
process — did not pay. Once a throwaway `warmup()` pass runs before either
policy is timed, and the two policies alternate which one goes first across
trials, the confound disappears and makespan converges to what the mechanism
actually predicts: no difference. This is the same class of mistake this
repository's own architecture-ablation and audio-latency chapters catch
elsewhere — a real measurement can still measure the wrong variable.

## What this does not show

**No preemption.** Once a job starts, it runs to completion; a high-priority
job that arrives while both slots are busy with low-priority work still
waits for one to finish naturally. A production scheduler (Slurm, Kubernetes)
can checkpoint or kill-and-requeue a running job to free a slot immediately —
that mechanism is not modeled here.

**Batch scheduling, not continuous arrival.** All 10 jobs are known and
queued at t=0. Real schedulers handle jobs arriving continuously over time,
which changes what "priority order" even means mid-run (a low-priority job
already running does not get bumped by a high-priority job that arrives a
second later).

**Threads on one CPU, not separate GPUs.** The "2 slots" here are Python
threads sharing one machine's cores, standing in for 2 separate GPU devices.
NumPy's BLAS calls release the GIL during the matmul itself, so real
concurrent compute does happen, but nothing here shows real GPU-to-GPU
scheduling, NVLink contention, or multi-node queueing (Slurm/Kubernetes
scale) — that would need the Modal lane's multi-GPU labs, which have not run
this comparison.

## Exercises

1. Change `--slots` to 1 and to 4. Predict what happens to the gap between
   FIFO's and priority's high-priority wait before running it, then check.
2. Add a `preempt` policy: when a high-priority job arrives and all slots
   are full of low-priority work, kill the newest low-priority thread and
   requeue it. Measure whether this closes the remaining gap to zero.
3. Make jobs arrive at different real times (via `time.sleep` before each
   job's queue-insertion) instead of all at t=0, and confirm priority
   ordering still produces the same qualitative effect under continuous
   arrival.

## Run record

[`runs/2026-08-01-scheduler-comparison.md`](runs/2026-08-01-scheduler-comparison.md)
— 2 slots, 3 alternating trials, CPU (local dev box), $0.
