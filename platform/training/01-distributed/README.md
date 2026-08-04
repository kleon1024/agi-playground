---
status: verified
level: applied
base: scratch
verified: 2026-07-27
label: Distributed training
---

# Distributed training, without a cluster

**Goal:** understand what actually happens between cards in data-parallel
training — and verify it — on a machine with no GPU at all.

Distributed training is normally taught as configuration: set a flag, read a
throughput number, move on. That teaches the API and none of the design. The
mechanics, though, are not GPU-specific. PyTorch's `gloo` backend performs real
collective operations between real processes on a CPU, so gradient all-reduce,
parameter sharding, and the memory arithmetic behind ZeRO can all be executed,
measured, and deliberately broken on one laptop.

What multiple GPUs buy is speed. Speed is the one part you do not need in order
to understand the design.

```bash
torchrun --standalone --nproc_per_node=4 core/distributed.py --mode ddp
torchrun --standalone --nproc_per_node=4 core/distributed.py --mode zero1
```

**Before this:** [what makes a training run worth its compute](../README.md).
You need the single-card picture — a token budget, a step, an optimizer state —
before it means anything to split one across eight cards.

## The one idea in data parallelism

Every rank holds a complete copy of the model and sees a *different* batch. It
computes gradients from its own data, which are therefore different from every
other rank's. Then a single collective operation — all-reduce — sums the
gradients across ranks and divides by the world size, so every rank ends up
holding the **average** gradient over the combined batch. Each then applies the
same update to the same weights, and they stay in lockstep forever after.

That is the whole mechanism. Everything else in data-parallel training is an
optimization of when and how that reduction happens.

Because it is the whole mechanism, `core/distributed.py` asserts it rather than
describing it: after all-reduce, each rank compares its gradient against rank
0's and raises if they differ by more than 1e-6. Measured on 4 ranks:

```
step 0: local-vs-averaged gradient delta = 0.000119
after all-reduce every rank holds an identical gradient (asserted)
final weight divergence across ranks: 0.00e+00
```

The first number matters as much as the last. It is the distance between what
one rank computed alone and the average — non-zero, confirming the ranks really
did see different data. The last confirms the synchronization was exact.

**The failure mode this guards against is quiet.** Ranks that drift apart do not
crash. Throughput looks perfect, loss curves look plausible, and you have
trained N slightly different models whose weights get averaged into something
none of them would have produced. Anything that skips a rank's gradient — a
conditional branch taken on some ranks only, a parameter that receives no
gradient in some batches — causes exactly this.

## Why optimizer state, not weights, fills the card

Measured on the same toy model:

```
per-rank parameters          1.31 MB
per-rank optimizer state     2.62 MB
ratio optimizer:params       2.00x
```

Adam stores two moment estimates per parameter. Under mixed precision, a
production setup also keeps an fp32 master copy of the weights, so the ratio
climbs further: for a model trained in bf16 with Adam, optimizer state plus
master weights routinely costs **six times** the bf16 parameters themselves.

This is the arithmetic that produced ZeRO. If the weights were the problem, you
would shard the weights first. They are not, so you do not.

## ZeRO stage 1, implemented directly

Each rank takes ownership of a slice of the parameters and allocates optimizer
state only for that slice. Gradients are still all-reduced — every rank needs
the full averaged gradient to update its own shard correctly — but after the
optimizer step, each owner **broadcasts** the parameters it just updated, since
every other rank now holds a stale copy.

```
per-rank optimizer state     1.05 MB  (sharded /4, was 2.62 MB)
owned parameters             2 of 5
final weight divergence      0.00e+00
```

Note the saving is 2.5×, not 4×. This toy has 5 parameter tensors round-robined
across 4 ranks, so ownership cannot divide evenly. That is not an artifact of
the example — production implementations shard by *element count* rather than
tensor count for exactly this reason, and seeing the uneven split is more
instructive than hiding it behind a convenient model size.

**Memory went down; communication went up.** ZeRO does not make training
cheaper in any absolute sense. It trades a resource you have run out of for one
you have not, and stages 2 and 3 push the same trade further by sharding
gradients and then parameters.

## What this cannot show you

**Communication cost.** On one machine, `gloo` all-reduce is nearly free. Every
bandwidth trade-off that dominates real multi-node training is invisible here,
which is precisely why this lesson reports no throughput numbers — they would
be meaningless and actively misleading.

**Tensor and pipeline parallelism.** Splitting a single matmul across devices,
or a layer stack across stages, only pays off with real interconnect. The
bubble arithmetic of pipeline parallelism and the all-reduce placement of
tensor parallelism need multiple GPUs to mean anything.

Both belong on the Modal lane with 2–4 real cards. That run has not happened
yet, and this lesson does not pretend otherwise.

## How this maps to what you will actually use

You will not write `dist.all_reduce` by hand. You will use `DistributedDataParallel`
or FSDP2, which do the same reduction with overlapping — starting each
parameter's all-reduce as soon as its gradient is ready, during the backward
pass, rather than waiting for backward to finish. That overlap is the main
engineering difference between this file and the real thing.

FSDP2 is ZeRO-3 built on DTensor: parameters, gradients, and optimizer state
are all sharded per-parameter, and each layer's full weights are gathered
just-in-time for its forward and freed immediately after. Read
[the serving stage](../../../missions/01-language-model-agent/05-serve/) for the inference-side counterpart, where
the same memory pressure reappears as KV cache rather than optimizer state.

## Exercises

1. **Break the synchronization.** Skip the all-reduce on one parameter and
   watch the assertion fire. Then remove the assertion and observe that nothing
   else complains — this is what a silent desync looks like.
2. **Change the world size** to 2, 3, and 8, and confirm the optimizer-state
   saving tracks the ownership split rather than the world size exactly.
3. **Shard by element count** instead of round-robin tensor count, and measure
   how much more even the memory split becomes.
4. **Implement ZeRO-2.** Shard the gradients too: replace all-reduce with
   reduce-scatter so each rank only ever materializes the gradient slice it
   owns.
5. **Measure the communication.** Count bytes moved per step in `ddp` versus
   `zero1`. The ratio is the price of the memory saving.

## Run record

[`runs/2026-07-27-cpu-simulation.md`](runs/2026-07-27-cpu-simulation.md) — 4
ranks, gloo, CPU, both modes.

## The layer underneath this one

This chapter chooses *what* to shard. Four infrastructure chapters measure the
machine that decides whether the choice is affordable, each one running the
comparison on hardware you already have:

- [Why allreduce topology matters even though the sum comes out the same](../../../infra/01-networking/) —
  ring versus star, measured over real inter-process IPC.
- [Why the cluster's wiring decides the parallelism strategy](../../../infra/05-gpu-cluster-concepts/) —
  which of data, tensor, and pipeline parallelism tolerates which link.
- [A scheduler decides whose work happens first](../../../infra/03-orchestration/) —
  what happens to a multi-rank job when it has to queue for slots.
- [How much data actually moves when a storage node is added](../../../infra/02-storage/) —
  where the sharded checkpoints this chapter writes end up living.
