---
status: verified
level: applied
base: scratch
verified: 2026-08-02
label: Rollout concurrency
---

# Why does an RL update step wait on its slowest rollout?

**Question:** [mission 01's RL stage](../../missions/01-language-model-agent/04-rl/what-a-real-loop-adds/#the-sampler-is-part-of-the-training-loop-now)
already covers why the sampler is part of the training loop — temperature,
top-p, and group size decide what enters the advantage estimate. That
chapter stops at the algorithm boundary: it does not ask how the *many*
trajectories one update step needs actually get generated concurrently, or
what happens when those trajectories take wildly different amounts of time
to finish. This chapter asks the systems question underneath it: given a
fixed pool of rollout workers and a batch of trajectories of unknown,
variable length, does the way you schedule them change how fast the batch
completes?

**The artifact this chapter follows** is a real, measured wall-clock
comparison: the same 40-trajectory, heavy-tailed-length workload, run under
two scheduling policies (batch-synchronized vs. continuous/asynchronous), at
three worker-pool sizes.

**Before this:** [`infra/03-orchestration/`](../03-orchestration/) — that
chapter's scheduler dispatches jobs of *fixed*, known cost, and finds that
priority order reassigns wait time without changing total makespan. This
chapter breaks that fixed-cost assumption on purpose: RL rollout length is
not known in advance and is not uniform, which is exactly the condition
under which a scheduling *policy*, not just an *order*, starts to matter.

## 1. What breaks when trajectory length is variable, not fixed

A synchronized ("lockstep") rollout loop submits exactly `W` trajectories to
`W` workers, then waits for all `W` to finish before starting the next `W` —
mirroring a training loop that cannot run its update step until the whole
rollout batch is in hand. If every trajectory took the same time, this would
cost nothing beyond `03-orchestration`'s own finding. But RL episode length
is heavy-tailed in practice: most rollouts terminate quickly, and a minority
run much longer (a reasoning chain that doesn't converge, an agent episode
that hits its step limit before succeeding). In a lockstep batch, **the
slowest trajectory in the batch sets the batch's finish time** — every
worker that finished its own trajectory early sits idle waiting for the one
straggler, and that idle time is thrown away every single batch boundary.

## 2. What the toy measures

[`core/rollout_scheduling.py`](core/rollout_scheduling.py) generates 40
synthetic trajectories per trial from a heavy-tailed length distribution (80%
draw 2-4 real matmul reps, 20% draw a 20-40 rep long tail — the toy's stand-in
for "most episodes end quickly, a minority run much longer"), then runs the
identical trajectory list under two policies:

- **lockstep** — submit `W` trajectories, wait for all `W`, repeat.
- **async** — a fixed pool of `W` worker threads pulls the next pending
  trajectory the instant it finishes its current one; no batch boundary at
  all.

Every trajectory's "work" is a real `200x200` NumPy matmul repeated `reps`
times, timed with `time.perf_counter` — not simulated with `time.sleep` — so
NumPy's BLAS call releases the GIL during the matmul itself and real
concurrent compute happens across threads, the same mechanism
`infra/03-orchestration`'s scheduler relies on.

```bash
cd infra/07-rollout-concurrency/core
python3 rollout_scheduling.py --workers 2,4,8 --n-trajectories 40 --trials 3 --out ../runs
```

## 3. The measured result

```
workers   lockstep makespan (mean)   async makespan (mean)   async speedup
   2            0.0395s                    0.0229s               1.73x
   4            0.0307s                    0.0207s               1.48x
   8            0.0263s                    0.0203s               1.30x
```

Async beats lockstep at every worker count tried, and the gap is largest at
the smallest worker count: 1.73x at 2 workers, shrinking to 1.30x at 8. The
reason is the batch-boundary count, not the worker count itself — 2 workers
means 20 sequential lockstep batches over the same 40 trajectories, versus 5
batches at 8 workers, and every batch boundary is one more chance for a
long-tail trajectory to strand its batch-mates idle. Async's own makespan is
comparatively stable across worker counts (0.0229s / 0.0207s / 0.0203s)
because it never pays a batch-boundary cost at all — a worker that finishes
its current trajectory just pulls the next one, straggler or not, from the
same shared queue every other worker draws from.

<!-- interactive: RolloutSchedulingSpeedup -->

## 4. Why this motivates a real distributed system, not just this toy

At 40 trajectories on one CPU thread pool, the effect is measurable but
small in absolute terms (tens of milliseconds). At real RL post-training
scale — thousands of concurrent rollouts across many GPU-backed inference
workers, each trajectory taking seconds to minutes rather than milliseconds
— the same straggler mechanism this toy isolates is large enough in absolute
wall-clock terms that production RL systems build their entire training
architecture around avoiding it: they decouple rollout generation from the
training step entirely, so training GPUs never sit idle waiting on the
slowest in-flight rollout. That decoupled, continuously-streaming design —
not merely "run more matmuls per second" — is what a real Modal-lane,
multi-GPU rollout deployment would need to reproduce this toy's async policy
at real scale, per [`infra/README.md`](../README.md)'s decision table.

## 5. What this does not establish

**No GPU was used anywhere in this chapter, and no real distributed system
was built.** This is a CPU-thread-pool timing toy showing *why* lockstep
batching loses time to stragglers as trajectory length grows more variable —
it does not benchmark AReaL, OpenRLHF, or any real asynchronous RLHF system,
and it makes no claim about what speedup a real multi-GPU deployment would
see. That number needs a real Modal-lane run, which is not attempted here.

**No real RL training loop, reward, or policy update runs here.** The
"trajectories" are synthetic matmul workloads standing in for the *shape* of
episode-length variance, not real rollouts against a real environment or
policy — nothing here says anything about [mission 06's own GRPO
training](../../missions/06-game-ai/01-grpo/) or any other mission's actual
rollout cost.

**The measured speedups (1.73x / 1.48x / 1.30x) are a property of this toy's
80/20 length-mixture and 40-trajectory count, not a universal constant.** A
more heavily skewed length distribution, or a larger trajectory count per
worker, would change the exact numbers; recompute for your own workload
before treating any one of these ratios as a general rule. The three trials
per cell also do not fully separate in range — this is a small, fast,
illustrative run, not a statistically tight one; see the full run record for
per-trial numbers.

## A brief history

Reinforcement learning's own sample-efficiency and off-policy-correction
literature is old; the specific systems problem this chapter isolates —
generation and training competing for the same synchronization barrier in
LLM post-training — became visible only once RL post-training moved to
long, heavy-tailed generation lengths (multi-step reasoning, agentic
trajectories) at production scale. Noukhovitch et al., "Asynchronous RLHF:
Faster and More Efficient Off-Policy RL for Language Models" (submitted
October 23, 2024; ICLR 2025), is the paper that names this exact mechanism —
decoupling generation from training removes the global synchronization
barrier this chapter's `lockstep` policy models, at the cost of training on
slightly off-policy (stale) rollouts. AReaL (2025, arXiv:2505.24298)
describes a fully asynchronous system built around the same decoupling,
with rollout workers continuously streaming trajectories into a shared
buffer that training workers retrieve from independently — the real-system
analogue of this chapter's `async` policy pulling from a shared queue.

## Exercises

1. **Change the length-mixture skew.** Try 95% short / 5% very long (a
   sharper tail) versus a uniform 2-40 rep spread (no tail at all) at a
   fixed worker count. Does async's speedup over lockstep grow with the
   skew, as the straggler mechanism predicts?
2. **Change `--n-trajectories`.** Run 200 trajectories instead of 40 at the
   same worker counts. Does the speedup-vs-worker-count trend (larger gap at
   fewer workers) still hold, or does it change once there are enough
   trajectories that even lockstep's batches average out the tail?
3. **Read `run_lockstep` again.** It waits for every worker in a batch with
   a plain `thread.join()` per worker, so a batch of `W` can never start its
   next round until literally all `W` threads return — confirm from the
   per-trial `start_s`/`end_s` values in `rollout-scheduling-result.json`
   that a short trajectory's `end_s` really can lag behind a long
   trajectory's `start_s` within the same batch, which is the idle time this
   chapter's whole argument depends on.

## Run it

```bash
cd infra/07-rollout-concurrency/core
python3 rollout_scheduling.py --workers 2,4,8 --n-trajectories 40 --trials 3 --out ../runs
```

CPU only, stdlib + NumPy, under 1 second total wall-clock, \$0. Full trace:
[`runs/2026-08-02-rollout-scheduling.md`](runs/2026-08-02-rollout-scheduling.md).
