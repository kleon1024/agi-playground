# Run record — all-reduce coordination-overhead timing

**Command:**

```bash
cd infra/05-gpu-cluster-concepts/core
torchrun --standalone --nproc_per_node=2 topology_timing.py --tensor-mb 4 --iters 200 --warmup 20
torchrun --standalone --nproc_per_node=4 topology_timing.py --tensor-mb 4 --iters 200 --warmup 20
torchrun --standalone --nproc_per_node=8 topology_timing.py --tensor-mb 4 --iters 200 --warmup 20
```

**Hardware:** local dev machine, 10 logical CPUs (`sysctl -n hw.ncpu` / `nproc`), no GPU.

**Software:** `torch==2.10.0`, `gloo` backend (CPU default), Python 3 (repo's
`uv` environment).

**Wall-clock:** each invocation completes in under 5 seconds; the reported
metric is the per-call mean over 200 timed iterations after 20 warmup calls
and a `dist.barrier()`, not the total script wall-clock.

**Cost:** \$0 (local lane, CPU only).

**Metrics:**

```
world_size= 2  tensor=4.0MB  mean all_reduce wall-clock = 1.8181 ms/call  (over 200 iters)
world_size= 4  tensor=4.0MB  mean all_reduce wall-clock = 3.5970 ms/call  (over 200 iters)
world_size= 8  tensor=4.0MB  mean all_reduce wall-clock = 8.3138 ms/call  (over 200 iters)
```

Scaling factors: 2->4 ranks = 1.98x; 4->8 ranks = 2.31x; 2->8 ranks = 4.57x.

**Notes:** Ran three times consecutively on an otherwise idle machine; results
were stable within about 5% run-to-run (not separately logged — a single run
per world size is what this chapter reports, consistent with the mechanism
question it asks, not a claim requiring seed-level statistics). The
near-linear scaling with world size, on a machine whose loopback bandwidth is
never remotely saturated by a 4MB tensor, is what this chapter's README reads
as coordination-overhead dominance rather than bandwidth-bound cost — see
README's "What this number is, and what it is not" section for the full
reasoning and its stated boundary.
