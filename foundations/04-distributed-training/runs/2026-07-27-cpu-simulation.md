# Run — distributed training mechanics, 4 ranks on CPU

**Date:** 2026-07-27
**Hardware:** Apple Silicon MacBook Pro, CPU only. **No GPU was used or needed.**
**Software:** Python 3.12, torch 2.x, `gloo` backend.
**Cost:** \$0.

The point of this run is that it required no cluster. Four real processes doing
real collective operations demonstrate every mechanic that matters; multiple
GPUs would only make it faster.

## Commands

```bash
torchrun --standalone --nproc_per_node=4 distributed.py --mode ddp   --steps 5
torchrun --standalone --nproc_per_node=4 distributed.py --mode zero1 --steps 5
```

## Data parallel (`--mode ddp`)

```
=== ddp | world_size=4 | backend=gloo ===
  step 0: local-vs-averaged gradient delta = 0.000119
  after all-reduce every rank holds an identical gradient (asserted)
  final weight divergence across ranks: 0.00e+00

  per-rank parameters          1.31 MB
  per-rank optimizer state     2.62 MB
  ratio optimizer:params       2.00x
```

Three things are established here:

**Gradients genuinely differ before the reduction.** The 0.000119 delta is the
distance between what one rank computed from its own batch and the averaged
result. If that number were zero, the ranks would be seeing identical data and
the whole exercise would be a no-op.

**They are identical afterwards, and the code asserts it.** Every rank compares
its post-reduction gradient against rank 0's and raises if they differ by more
than 1e-6. This is the entire mechanism of data-parallel training, so it is
checked rather than assumed — a silent desynchronization produces ranks that
drift apart while throughput dashboards look perfectly healthy.

**Final weight divergence is exactly zero.** Identical initialization plus
identical gradients plus identical optimizer states must yield bit-identical
weights, and it does.

**Optimizer state is 2× the parameters**, even on this toy. Adam keeps two
moment estimates per parameter; a realistic setup with an fp32 master copy
alongside bf16 weights pushes the ratio higher still. This is the number that
motivates everything below — the weights are not what fills the card.

## ZeRO-1 optimizer sharding (`--mode zero1`)

```
=== zero1 | world_size=4 | backend=gloo ===
  final weight divergence across ranks: 0.00e+00

  per-rank parameters          1.31 MB  (still replicated)
  per-rank optimizer state     1.05 MB  (sharded /4)
  owned parameters         2 of 5
```

Optimizer state per rank drops from 2.62 MB to 1.05 MB — a **2.5× reduction**,
not the full 4× the world size might suggest, because this toy has 5 parameter
tensors distributed round-robin across 4 ranks, so ownership cannot divide
evenly. That imbalance is not an artifact of the toy: production
implementations shard by element count precisely because tensor count divides
badly. Seeing the uneven split here is more instructive than hiding it.

Weights still agree exactly across ranks, which is the correctness bar — memory
was saved without changing the mathematics of the update.

## What this does not show

Communication cost. On one machine over `gloo`, all-reduce is nearly free, so
none of the bandwidth trade-offs that dominate real multi-node training appear
in these numbers. ZeRO's memory saving is paid for in communication, and this
run cannot measure that price. Throughput figures here would be meaningless and
are deliberately not reported.

It also does not exercise tensor or pipeline parallelism, which split a single
matmul or a layer stack across devices, and which need real interconnect to be
worth anything.

Both belong on the Modal lane with 2–4 real GPUs, and that run has not happened
yet.
