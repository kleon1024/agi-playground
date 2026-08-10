"""Distributed training mechanics you can run without a second GPU.

Multi-card training is usually taught as configuration — set a flag, read a
throughput number — because the reader is assumed not to own a cluster. That
teaches nothing about what actually happens between the cards.

But the mechanics are not GPU-specific. PyTorch's `gloo` backend runs real
collective operations between real processes on a CPU, so every idea that
matters — gradient all-reduce, parameter sharding, the memory arithmetic that
motivates ZeRO — can be executed, measured, and broken on one laptop. What
multiple GPUs buy is speed, and speed is the one part you do not need in order
to understand the design.

This file demonstrates three things in order:

1. **What data parallelism actually does.** Each rank sees different data,
   computes different gradients, and then all-reduce averages them so every
   rank applies the *same* update. We assert that the gradients really are
   identical afterwards, because "the gradients get synchronized" is the whole
   mechanism and it is worth seeing proved rather than asserted.

2. **Why optimizer state dominates memory.** Adam keeps two moment estimates
   plus an fp32 master copy. For a model with N parameters trained in bf16,
   the optimizer typically costs several times what the weights do — which is
   why sharding *optimizer state* (ZeRO stage 1) is the first and cheapest win,
   before anyone touches the parameters.

3. **What sharding buys, measured.** Each rank owns 1/world_size of the
   optimizer state and broadcasts its slice of the update. We print the
   per-rank memory both ways so the saving is a number rather than a claim.

Run:
    torchrun --standalone --nproc_per_node=4 distributed.py --mode ddp
    torchrun --standalone --nproc_per_node=4 distributed.py --mode zero1

On CPU this uses gloo; with `--device cuda` and real GPUs it uses nccl and the
identical code path.
"""

from __future__ import annotations

import argparse
import os

import torch
import torch.distributed as dist
from torch import nn


def setup(device: str) -> tuple[int, int]:
    """Join the process group. Returns (rank, world_size)."""
    backend = "nccl" if device.startswith("cuda") else "gloo"
    dist.init_process_group(backend=backend)
    rank = dist.get_rank()
    world = dist.get_world_size()
    if device.startswith("cuda"):
        torch.cuda.set_device(rank % torch.cuda.device_count())
    return rank, world


def log(rank: int, msg: str) -> None:
    """Print from rank 0 only, unless the message is explicitly per-rank."""
    if rank == 0:
        print(msg, flush=True)


class Toy(nn.Module):
    """Small enough to run on CPU, structured like the real thing.

    The point is the communication pattern, not the model — every layer here is
    a matrix whose gradient must be reduced across ranks, which is exactly the
    property that matters.
    """

    def __init__(self, d: int = 256, layers: int = 4):
        super().__init__()
        self.net = nn.Sequential(
            *[m for _ in range(layers) for m in (nn.Linear(d, d, bias=False), nn.GELU())]
        )
        self.head = nn.Linear(d, d, bias=False)

    def forward(self, x):
        return self.head(self.net(x))


def bytes_of(tensors) -> int:
    return sum(t.numel() * t.element_size() for t in tensors)


# ---------------------------------------------------------------------------
# 1. Data parallelism: different data per rank, identical update
# ---------------------------------------------------------------------------


def run_ddp(rank: int, world: int, device: str, steps: int, d: int) -> None:
    torch.manual_seed(0)  # identical initialization on every rank
    model = Toy(d).to(device)

    # Every rank must start from the same weights, or averaging gradients is
    # meaningless. Broadcasting from rank 0 is how that is guaranteed in
    # practice; seeding identically is the shortcut we can take here.
    for p in model.parameters():
        dist.broadcast(p.data, src=0)

    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)

    for step in range(steps):
        # Different data per rank — this is the "data" in data parallel.
        torch.manual_seed(1000 + step * world + rank)
        x = torch.randn(8, d, device=device)
        y = torch.randn(8, d, device=device)

        loss = ((model(x) - y) ** 2).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()

        # Before all-reduce, each rank holds a gradient computed from its own
        # batch. They differ.
        before = model.head.weight.grad.clone()

        for p in model.parameters():
            dist.all_reduce(p.grad, op=dist.ReduceOp.SUM)
            p.grad /= world  # SUM then divide == mean

        after = model.head.weight.grad
        drift = (before - after).abs().max().item()

        # Now every rank must hold the *same* gradient. Prove it: gather rank
        # 0's copy and compare. If this assertion ever fails, training is
        # silently diverging across ranks and no throughput number matters.
        reference = after.clone()
        dist.broadcast(reference, src=0)
        mismatch = (after - reference).abs().max().item()
        assert mismatch < 1e-6, f"rank {rank} gradient differs from rank 0 by {mismatch}"

        opt.step()

        if step == 0:
            log(rank, f"  step 0: local-vs-averaged gradient delta = {drift:.6f}")
            log(rank, "  after all-reduce every rank holds an identical gradient (asserted)")

    # Because gradients were identical, weights must be identical too.
    w = model.head.weight.data.clone()
    ref = w.clone()
    dist.broadcast(ref, src=0)
    log(rank, f"  final weight divergence across ranks: {(w - ref).abs().max().item():.2e}")

    params = list(model.parameters())
    opt_state = [v for s in opt.state.values() for v in s.values() if torch.is_tensor(v)]
    log(rank, "")
    log(rank, f"  per-rank parameters      {bytes_of(params) / 1e6:8.2f} MB")
    log(rank, f"  per-rank optimizer state {bytes_of(opt_state) / 1e6:8.2f} MB")
    log(rank, f"  ratio optimizer:params   {bytes_of(opt_state) / max(bytes_of(params), 1):8.2f}x")


# ---------------------------------------------------------------------------
# 2. ZeRO stage 1: shard the optimizer state
# ---------------------------------------------------------------------------


def run_zero1(rank: int, world: int, device: str, steps: int, d: int) -> None:
    """Each rank optimizes only its slice of the parameters.

    Gradients are still all-reduced — every rank needs the full averaged
    gradient to compute its own slice correctly. What changes is that a rank
    allocates optimizer state for its shard only, then broadcasts the updated
    parameters it owns. Communication goes up; memory goes down.
    """
    torch.manual_seed(0)
    model = Toy(d).to(device)
    for p in model.parameters():
        dist.broadcast(p.data, src=0)

    params = list(model.parameters())
    # Round-robin assignment. Production implementations balance by element
    # count rather than parameter count; this keeps the ownership rule visible.
    owned = [p for i, p in enumerate(params) if i % world == rank]
    owner_of = {i: i % world for i in range(len(params))}

    opt = torch.optim.AdamW(owned, lr=1e-3)

    for step in range(steps):
        torch.manual_seed(1000 + step * world + rank)
        x = torch.randn(8, d, device=device)
        y = torch.randn(8, d, device=device)

        loss = ((model(x) - y) ** 2).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()

        for p in params:
            dist.all_reduce(p.grad, op=dist.ReduceOp.SUM)
            p.grad /= world

        opt.step()  # updates only this rank's shard

        # Every rank now holds stale copies of the parameters it does not own,
        # so the owner broadcasts the fresh values. This is the communication
        # ZeRO trades for memory.
        for i, p in enumerate(params):
            dist.broadcast(p.data, src=owner_of[i])

    w = model.head.weight.data.clone()
    ref = w.clone()
    dist.broadcast(ref, src=0)
    log(rank, f"  final weight divergence across ranks: {(w - ref).abs().max().item():.2e}")

    opt_state = [v for s in opt.state.values() for v in s.values() if torch.is_tensor(v)]
    log(rank, "")
    log(rank, f"  per-rank parameters      {bytes_of(params) / 1e6:8.2f} MB  (still replicated)")
    log(rank, f"  per-rank optimizer state {bytes_of(opt_state) / 1e6:8.2f} MB  (sharded /{world})")
    log(rank, f"  owned parameters         {len(owned)} of {len(params)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["ddp", "zero1"], default="ddp")
    ap.add_argument("--steps", type=int, default=5)
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    if "RANK" not in os.environ:
        raise SystemExit(
            "launch with torchrun, e.g.\n"
            "  torchrun --standalone --nproc_per_node=4 distributed.py --mode ddp"
        )

    rank, world = setup(args.device)
    log(rank, f"\n=== {args.mode} | world_size={world} | backend={dist.get_backend()} ===")

    if args.mode == "ddp":
        run_ddp(rank, world, args.device, args.steps, args.dim)
    else:
        run_zero1(rank, world, args.device, args.steps, args.dim)

    dist.barrier()
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
