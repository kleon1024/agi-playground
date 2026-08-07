"""What interconnect topology actually costs -- the part you can measure without a cluster.

foundations/04-distributed-training/core/distributed.py proves data parallelism
is correct on CPU gloo and deliberately reports no throughput numbers, because
one machine's loopback has none of the bandwidth contention that makes real
interconnect topology (NVLink inside a node, PCIe to the host, Ethernet or
InfiniBand between nodes) a design decision at all.

This file measures a different, honest thing: how the *wall-clock cost of a
single all-reduce call* changes with world size on one CPU, isolated from any
model forward/backward pass. That number is not bandwidth-bound the way a real
multi-node all-reduce is -- gloo's loopback has effectively unlimited bandwidth
for these tensor sizes. What it *can* show is the coordination/dispatch
overhead component of a collective: launching a torch.distributed op, having
every rank rendezvous, and returning. That overhead is real, it does scale
with world size, and it is one real component of the same total cost a GPU
cluster pays -- it is just not the component that differs between NVLink and
Ethernet. The bandwidth-bound component cannot be produced on one CPU at all,
and this file does not pretend otherwise.

Run:
    torchrun --standalone --nproc_per_node=2 topology_timing.py
    torchrun --standalone --nproc_per_node=4 topology_timing.py
    torchrun --standalone --nproc_per_node=8 topology_timing.py
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import torch
import torch.distributed as dist

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "platform", "training", "01-distributed", "core"
    ),
)
from distributed import log, setup


def time_all_reduce(world: int, device: str, tensor_mb: float, iters: int, warmup: int) -> float:
    """Mean wall-clock per all_reduce call, in seconds, over `iters` repeats after `warmup`."""
    numel = int(tensor_mb * 1e6 / 4)  # fp32 elements
    t = torch.randn(numel, device=device)

    for _ in range(warmup):
        dist.all_reduce(t, op=dist.ReduceOp.SUM)
    dist.barrier()

    start = time.perf_counter()
    for _ in range(iters):
        dist.all_reduce(t, op=dist.ReduceOp.SUM)
    dist.barrier()
    elapsed = time.perf_counter() - start
    return elapsed / iters


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tensor-mb", type=float, default=4.0)
    ap.add_argument("--iters", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    if "RANK" not in os.environ:
        raise SystemExit(
            "launch with torchrun, e.g.\n"
            "  torchrun --standalone --nproc_per_node=4 topology_timing.py"
        )

    rank, world = setup(args.device)
    per_call = time_all_reduce(world, args.device, args.tensor_mb, args.iters, args.warmup)
    log(
        rank,
        f"world_size={world:2d}  tensor={args.tensor_mb:.1f}MB  "
        f"mean all_reduce wall-clock = {per_call * 1e3:.4f} ms/call  (over {args.iters} iters)",
    )

    dist.barrier()
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
