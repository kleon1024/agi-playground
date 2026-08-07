---
status: verified
level: applied
base: scratch
label: When the scheduler chooses
verified: 2026-08-06
---

# A scheduler doesn't do more work — it decides whose work waits

**Question:** [the orchestration chapter](../) compared FIFO and priority
scheduling on two slots. This chapter reads the recorded run and asks what
the scheduler actually changes.

**Before this:** [the orchestration chapter](../) and its recorded scheduler
comparison.

## The comparison, read

The run ([record](runs/2026-08-06-scheduler-read.md)) reads the recorded
JSON:

| policy | makespan | high-priority wait | low-priority wait |
|---|---:|---:|---:|
| FIFO | 0.0182s | 0.0074s | 0.0074s |
| priority | 0.0187s | 0.0012s | 0.0094s |

## Two readings

**Makespan barely moves — the scheduler is not doing more work.** 0.0182
versus 0.0187 seconds, within trial noise. Both policies run the same jobs
on the same two slots; the total work and the total time are essentially
unchanged. The scheduler's job is not to speed work up; it is to decide
whose work happens first.

**The wait distribution is the entire difference.** Priority scheduling
cuts high-priority wait ~6x (0.0074 -> 0.0012s) while low-priority wait
grows (0.0074 -> 0.0094s). The same jobs, the same slots, and a completely
different answer to "who waits" — which is exactly the product decision an
orchestrator makes. A scheduler that claims to make everything faster is
lying; one that says who waits is telling the truth.

## Evidence boundary

The recorded scheduler run (2 slots, 3 trials per policy, warmup and
alternating order to remove cold-start artifacts). It reads that artifact;
it does not re-run the jobs and does not extend the result to preemption
or gang scheduling, which the chapter's landscape covers.

## Check your mental model

Answer each before opening it.

**1. If makespan is unchanged, why does priority scheduling exist?**

<details>
<summary>Answer</summary>

Because makespan is the wrong metric for a mixed-priority workload. The
value of a scheduler is whose deadline is met, not the aggregate finish
time: priority scheduling trades low-priority latency for high-priority
latency, and that trade is exactly what a production cluster (or a
multi-tenant serving system) is buying. A scheduler that only made
everything finish sooner would be optimizing the metric nobody's request
actually depends on.

</details>

**2. What does the 6x high-priority wait cut cost the low-priority jobs?**

<details>
<summary>Answer</summary>

It costs them the 0.0020s of extra wait (0.0094 vs 0.0074) — the recorded
trade. Priority is not free: every high-priority job that jumps the queue
pushes some low-priority job back. The scheduler's honesty is showing both
sides of that trade in the same table, which is why the recorded run is the
evidence rather than a "priority is better" headline.

</details>

## Next

Back to [the orchestration chapter](../), or to
[the rollout-concurrency chapter](../../../../01-language-model/04-rl/rollout-concurrency/) where the same
who-waits question is asked of RL rollouts.
