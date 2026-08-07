"""Continue training the parent and its upcycled child on identical data, and
see which one the next hour of GPU time is better spent on.

`upcycle.py` proves the surgery preserved the function. It says nothing about
whether the new shape is worth having, and the honest comparison is not against
an untrained model — it is against **the same GPU-hours spent continuing to
train the parent**, because that is the alternative actually available.

Both arms start from the same 3.0B-token checkpoint, see the same batches in
the same order, and follow the same schedule. One of them has four experts
where the other has one feed-forward.

The budget is declared and it is *tokens*, not FLOPs. Activating two experts of
the parent's width costs 1.64x the parameters per token, so the MoE arm spends
more compute for the same tokens and considerably more wall-clock than that,
because the expert dispatch here is a Python loop rather than a grouped kernel.
Both numbers are reported. A win for the MoE arm on equal tokens is a weaker
claim than a win on equal FLOPs, and the run record says so rather than picking
whichever framing flatters the result.

Usage:
    python continue_training.py --arm dense --checkpoint ckpt.pt --data ~/tokens --tokens 3e8
    python continue_training.py --arm moe   --checkpoint moe.pt  --data ~/tokens --tokens 3e8
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
from upcycle import VariantConfig, VariantTransformer, mission_model, variants


def batches(data, batch: int, block: int, steps: int, device: str, seed: int):
    """The same batch sequence for both arms, so a difference between them
    cannot be a difference in what they were shown."""
    rng = np.random.default_rng(seed)
    for _ in range(steps):
        starts = rng.integers(0, len(data) - block - 1, size=batch)
        x = np.stack([data[s : s + block].astype(np.int64) for s in starts])
        y = np.stack([data[s + 1 : s + 1 + block].astype(np.int64) for s in starts])
        yield torch.from_numpy(x).to(device), torch.from_numpy(y).to(device)


@torch.no_grad()
def evaluate(model, data, batch, block, device, iters) -> float:
    model.eval()
    total = 0.0
    for x, y in batches(data, batch, block, iters, device, seed=999):
        with torch.autocast("cuda", dtype=torch.bfloat16):
            total += model(x, y)[1].item()
    model.train()
    return total / iters


def build(arm: str, checkpoint: Path, device: str):
    blob = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if arm == "dense":
        cfg = mission_model.Config(**blob["config"])
        model = mission_model.Transformer(cfg)
        model.load_state_dict(blob["model"])
        block_size = cfg.block_size
    else:
        cfg = VariantConfig(**blob["config"])
        model = VariantTransformer(cfg)
        model.load_state_dict(blob["model"], strict=False)
        block_size = cfg.block_size
    return model.to(device), cfg, block_size


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=["dense", "moe"], required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--tokens", type=float, default=3e8)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--accum", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--eval-every", type=int, default=200)
    ap.add_argument("--eval-iters", type=int, default=40)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    model, _, block = build(args.arm, args.checkpoint, args.device)
    moes = [m for m in model.modules() if isinstance(m, variants.MoE)]
    train = np.memmap(args.data / "train.bin", dtype=np.uint16, mode="r")
    val = np.memmap(args.data / "val.bin", dtype=np.uint16, mode="r")

    per_step = args.batch * args.accum * block
    steps = int(args.tokens / per_step)
    warmup = max(1, steps // 50)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.95),
                            weight_decay=0.1, fused=True)

    start_loss = evaluate(model, val, args.batch, block, args.device, args.eval_iters)
    history = [{"step": 0, "tokens": 0, "val_loss": round(start_loss, 4)}]
    print(f"{args.arm}: starting val loss {start_loss:.4f} over {steps} steps of {per_step:,} tokens")

    source = batches(train, args.batch, block, steps * args.accum, args.device, seed=1234)
    started = time.perf_counter()
    for step in range(steps):
        lr = (args.lr * (step + 1) / warmup if step < warmup
              else args.lr * (0.1 + 0.45 * (1 + math.cos(math.pi * (step - warmup) / max(1, steps - warmup)))))
        for group in opt.param_groups:
            group["lr"] = lr
        for _ in range(args.accum):
            x, y = next(source)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = model(x, y)[1] / args.accum
            loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        opt.zero_grad(set_to_none=True)
        for moe in moes:
            moe.rebalance()

        if (step + 1) % args.eval_every == 0 or step == steps - 1:
            v = evaluate(model, val, args.batch, block, args.device, args.eval_iters)
            elapsed = time.perf_counter() - started
            history.append({"step": step + 1, "tokens": (step + 1) * per_step,
                            "val_loss": round(v, 4), "elapsed_s": round(elapsed, 1),
                            "tokens_per_s": round((step + 1) * per_step / elapsed)})
            print(f"  step {step + 1:>5}  tokens {(step + 1) * per_step / 1e6:>7.1f}M  "
                  f"val {v:.4f}  {(step + 1) * per_step / elapsed / 1e3:>6.1f}k tok/s")
            if args.out:
                args.out.write_text(json.dumps(
                    {"arm": args.arm, "budget": "equal additional tokens",
                     "lr": args.lr, "history": history}, indent=2))

    print(f"{args.arm}: {start_loss:.4f} -> {history[-1]['val_loss']:.4f} "
          f"in {history[-1]['elapsed_s'] / 60:.1f} minutes")


if __name__ == "__main__":
    main()
