---
status: verified
level: applied
base: scratch
label: When the heavy tail waits
verified: 2026-08-06
---

# Async wins because a finished worker does not wait

**Question:** [the rollout-concurrency chapter](../) fed the same
40-trajectory list to lockstep and async scheduling at 2, 4, 8 workers.
This chapter reads the recorded run and asks what the speedup actually
comes from.

**Before this:** [the rollout-concurrency chapter](../) and its recorded
scheduling run.

## The comparison, read

The run ([record](runs/2026-08-06-rollout-read.md)) reads the recorded JSON:

| workers | lockstep makespan | async makespan | speedup |
|---:|---:|---:|---:|
| 2 | 0.0395s | 0.0229s | 1.73x |
| 4 | 0.0307s | 0.0207s | 1.48x |
| 8 | 0.0263s | 0.0203s | 1.30x |

The trajectory list is identical in both policies, with alternating trial
order — the only difference is the scheduling policy.

## Two readings

**Async wins because a finished worker grabs the next rollout instead of
waiting on the long tail.** The trajectory lengths are heavy-tailed (80%
short, 20% very long). In lockstep, every worker waits for the slowest
rollout of each batch before the next batch starts; in async, a worker
that finishes early takes the next trajectory immediately. The speedup at
2 workers (1.73x) is the heavy tail being hidden, not eliminated.

**The speedup narrows as workers increase — but the tail never
disappears.** 1.73x at 2 workers falls to 1.30x at 8: with more workers,
the batch's slowest rollout is less likely to idle everyone, so lockstep
catches up. The measured pattern is the honest version of the mechanism —
async is not "more workers are better," it is "waiting on the tail is
worse," and the gap between the policies is exactly the tail's size.

## The fix and its trade

The failure is lockstep waiting on the slowest rollout of each batch:
the trajectory lengths are heavy-tailed (80 percent short, 20 percent
very long), so every worker idles until the batch's tail finishes. The
fix is the scheduling policy, not more workers — async lets a finished
worker grab the next trajectory immediately, and the recorded speedup is
the tail being hidden: 1.73x at 2 workers, 1.48x at 4, 1.30x at 8. The
trade is measured in the same table. Async buys makespan at the cost of
rollout order — trajectories complete out of their original order, which
matters only if downstream bookkeeping assumes a batch order — and the
speedup narrows as workers increase (1.73x to 1.30x), because a larger
pool dilutes the tail's relative cost. The honest read is "waiting on
the tail is worse," not "async is better," and the same policy question
is the production one: the sampler half of the RL loop, not the trainer
half, is what the run is usually paying for.

## Who owns the loop

The scheduling result is only useful if someone owns each failure the
table exposes:

- **The training-infra team** owns the scheduling policy: lockstep
  versus async is a deployment decision, and the worker count is the
  knob that changes the speedup (1.73x at 2 workers to 1.30x at 8).
- **The rollout-sampler owner** owns the trajectory distribution: the
  80/20 heavy tail is a property of the task and the sampling
  configuration, not of the scheduler, and a policy tuned on a fixed
  length distribution will not transfer to a different one.
- **The evaluation team** owns the makespan-versus-throughput read: a
  speedup reported without the worker count and the tail shape is not
  comparable to another run's, and the crossover between policies is
  exactly where the honest number sits.

## Evidence boundary

The recorded scheduling run (40 trajectories, 80/20 heavy-tailed lengths,
3 trials per worker count, alternating order, one seed, local CPU thread
pool over NumPy BLAS). It reads that artifact; it does not re-run the
rollouts and does not extend the result to real GPU rollouts, where the
per-rollout cost and the scheduling overhead change the crossover.

## Check your mental model

Answer each before opening it.

**1. Why does the same trajectory list produce different makespans under
the two policies?**

<details>
<summary>Answer</summary>

Because the policies schedule the same work differently. Lockstep divides
the 40 trajectories into batches and every worker waits for the batch's
slowest rollout before proceeding. Async lets each worker take the next
trajectory as soon as it is free, so the long tail occupies one worker
instead of stalling all of them. Same work, different wait structure — the
measured speedup is the wait structure, not the work.

</details>

**2. Why does the speedup shrink at 8 workers?**

<details>
<summary>Answer</summary>

Because the tail's relative cost shrinks as parallelism grows. With more
workers, even lockstep has enough capacity that the slowest rollout of a
batch idles fewer of them, so its handicap is smaller. The recorded 1.73x
to 1.30x is the tail being diluted — which is also a warning: at any worker
count the tail still costs something, and only async (or tail-tolerant
scheduling) removes it entirely.

</details>

## Next

Back to [the rollout-concurrency chapter](../), or to
[the RL loop it schedules](../../what-a-real-loop-adds/)
where the same waiting problem appears at the mission scale.
