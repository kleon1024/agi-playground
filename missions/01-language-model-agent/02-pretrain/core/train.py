"""Pretraining loop: token binary in, trained checkpoint out.

The model lives in `model.py`; this file is the engineering that decides whether
a mathematically correct model actually converges. Four things here are load
bearing, and each has a failure mode you will otherwise meet at 2am:

**Gradient accumulation.** The batch size that trains well and the batch size
that fits in memory are different numbers. Run several micro-batches, divide
each one's loss by the accumulation count, and step once. The division is not
cosmetic: skip it and you have silently multiplied your learning rate by the
accumulation count.

**Warmup then cosine decay.** Adam's moment estimates start at zero and are
badly biased for the first few hundred steps. A large learning rate applied to a
biased estimate produces an update the rest of training has to recover from.
Warmup buys the optimizer time to calibrate before the step size matters.

**Gradient clipping.** One bad batch — a document of repeated characters, a
tokenizer artifact — produces a gradient large enough to undo hours of progress.
Clipping bounds the damage any single batch can do.

**MFU.** Model FLOPs Utilization is the honest throughput number: what fraction
of the GPU's arithmetic capability the run actually uses. Tokens per second
flatters small models; MFU does not, and a sudden drop in it is the first sign
something has gone wrong in the data path.

Run:  python train.py --data data/tokens --out ckpt
"""

from __future__ import annotations

import argparse
import json
import math
import time
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import torch
from model import Config, Transformer


def get_batch(data: np.memmap, batch: int, block: int, device: str):
    """Random windows into the token stream.

    Sampling offsets uniformly means a document's tokens appear in many
    different context positions across training, rather than always at the same
    offset — which is what you would get from sequential chunking.
    """
    ix = torch.randint(len(data) - block - 1, (batch,))
    x = torch.stack([torch.from_numpy(data[i : i + block].astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy(data[i + 1 : i + block + 1].astype(np.int64)) for i in ix])
    if device.startswith("cuda"):
        # Pinned (page-locked) host memory lets the copy to GPU overlap with
        # compute. It is CUDA-specific: requesting it on CPU or MPS fails.
        return (
            x.pin_memory().to(device, non_blocking=True),
            y.pin_memory().to(device, non_blocking=True),
        )
    return x.to(device), y.to(device)


def lr_at(step: int, warmup: int, total: int, peak: float, floor_ratio: float = 0.1) -> float:
    if step < warmup:
        return peak * (step + 1) / warmup
    if step >= total:
        return peak * floor_ratio
    progress = (step - warmup) / max(1, total - warmup)
    return peak * (floor_ratio + (1 - floor_ratio) * 0.5 * (1 + math.cos(math.pi * progress)))


def add_model_size_args(ap: argparse.ArgumentParser) -> None:
    """Scale the architecture away from the default 88M shape.

    Defaults match `Config()` exactly, so omitting every flag reproduces the
    recorded pretraining run. The flags exist so a single script can train
    small bases (e.g. the ~8M base the SFT model-size chapter uses) instead of
    forking a second trainer.
    """
    g = ap.add_argument_group("model size")
    g.add_argument("--n-layer", type=int, default=12)
    g.add_argument("--n-head", type=int, default=12)
    g.add_argument("--n-kv-head", type=int, default=4)
    g.add_argument("--d-model", type=int, default=768)
    g.add_argument("--d-ff", type=int, default=2048)
    g.add_argument("--block-size", type=int, default=1024)


@torch.no_grad()
def evaluate(model, data, batch, block, device, iters, autocast) -> float:
    model.eval()
    losses = torch.zeros(iters)
    for k in range(iters):
        x, y = get_batch(data, batch, block, device)
        with autocast:
            _, loss = model(x, y)
        losses[k] = loss.item()
    model.train()
    return losses.mean().item()


def save_checkpoint(path, model, opt, cfg, step, history, tokens_seen) -> None:
    """Everything needed to continue, not just to inspect.

    Weights alone are not a resumable state: Adam's moment estimates carry the
    optimizer's accumulated knowledge of the loss surface, and restarting
    without them re-introduces exactly the bias that warmup exists to avoid.
    Long runs on machines that sleep are the normal case, not the exception.
    """
    tmp = path.with_suffix(".tmp")
    torch.save(
        {
            "model": model.state_dict(),
            "optimizer": opt.state_dict(),
            "config": vars(cfg),
            "step": step,
            "history": history,
            "tokens_seen": tokens_seen,
        },
        tmp,
    )
    # Atomic replace: a checkpoint half-written when the machine dies is worse
    # than no checkpoint, because it looks resumable.
    tmp.replace(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data/tokens"))
    ap.add_argument("--out", type=Path, default=Path("ckpt"))
    ap.add_argument("--tokens", type=float, default=3.0e9, help="total token budget")
    ap.add_argument("--batch", type=int, default=16, help="micro-batch size")
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--lr", type=float, default=6e-4)
    ap.add_argument("--warmup", type=int, default=500)
    ap.add_argument("--weight-decay", type=float, default=0.1)
    ap.add_argument("--clip", type=float, default=1.0)
    ap.add_argument("--eval-every", type=int, default=500)
    ap.add_argument("--eval-iters", type=int, default=50)
    ap.add_argument("--checkpoint-every", type=int, default=2000)
    ap.add_argument("--compile", action="store_true")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--resume", action="store_true",
                    help="continue from ckpt.pt in --out if it exists")
    add_model_size_args(ap)
    args = ap.parse_args()

    torch.manual_seed(1337)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    args.out.mkdir(parents=True, exist_ok=True)

    cfg = Config(
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_kv_head=args.n_kv_head,
        d_model=args.d_model,
        d_ff=args.d_ff,
        block_size=args.block_size,
    )
    model = Transformer(cfg).to(args.device)
    n_params = sum(p.numel() for p in model.parameters())
    print(model.param_report(), flush=True)

    # Keep an explicit handle on the real module. torch.compile returns a
    # wrapper, and reaching through it for parameters or state_dict works only
    # by proxy — being explicit here avoids saving a checkpoint that cannot be
    # loaded without the compiler.
    raw_model = model
    if args.compile:
        model = torch.compile(model)

    train_data = np.memmap(args.data / "train.bin", dtype=np.uint16, mode="r")
    val_data = np.memmap(args.data / "val.bin", dtype=np.uint16, mode="r")

    tokens_per_step = args.batch * cfg.block_size * args.grad_accum
    total_steps = int(args.tokens / tokens_per_step)
    print(
        f"\ntrain tokens {len(train_data):,} | val tokens {len(val_data):,}\n"
        f"tokens/step  {tokens_per_step:,} "
        f"(micro {args.batch} x block {cfg.block_size} x accum {args.grad_accum})\n"
        f"steps        {total_steps:,} for a {args.tokens / 1e9:.2f}B token budget\n"
        f"epochs       {args.tokens / len(train_data):.2f} over the corpus",
        flush=True,
    )

    # Weight decay belongs on matrices, not on gains and biases: decaying a
    # LayerNorm/RMSNorm gain pulls it toward zero, which is a change in function,
    # not regularization.
    decay = [p for _, p in raw_model.named_parameters() if p.dim() >= 2]
    no_decay = [p for _, p in raw_model.named_parameters() if p.dim() < 2]
    opt = torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": args.weight_decay},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=args.lr,
        betas=(0.9, 0.95),
        eps=1e-8,
        fused=(args.device == "cuda"),
    )

    autocast = (
        torch.autocast("cuda", dtype=torch.bfloat16)
        if args.device == "cuda"
        else nullcontext()
    )
    peak_flops = 165e12  # bf16 dense, adjust per card; only affects the MFU figure
    history: list[dict] = []
    t0 = time.time()
    tokens_seen = 0
    start_step = 0

    ckpt_path = args.out / "ckpt.pt"
    if args.resume and ckpt_path.exists():
        ckpt = torch.load(ckpt_path, map_location=args.device, weights_only=False)
        raw_model.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["optimizer"])
        start_step = ckpt["step"]
        history = ckpt.get("history", [])
        tokens_seen = ckpt.get("tokens_seen", 0)
        print(
            f"resumed from {ckpt_path}: step {start_step:,}, "
            f"{tokens_seen / 1e9:.2f}B tokens already seen",
            flush=True,
        )

    for step in range(start_step, total_steps + 1):
        lr = lr_at(step, args.warmup, total_steps, args.lr)
        for g in opt.param_groups:
            g["lr"] = lr

        if step % args.eval_every == 0:
            val = evaluate(model, val_data, args.batch, cfg.block_size,
                           args.device, args.eval_iters, autocast)
            elapsed = time.time() - t0
            tps = tokens_seen / elapsed if elapsed > 0 else 0
            # 6N per token for fwd+bwd, plus attention's quadratic term
            flops_per_token = 6 * n_params + 12 * cfg.n_layer * cfg.block_size * cfg.d_model
            mfu = tps * flops_per_token / peak_flops * 100
            rec = {
                "step": step, "val_loss": val, "lr": lr,
                "tokens": tokens_seen, "elapsed_s": round(elapsed, 1),
                "tok_per_s": round(tps), "mfu_pct": round(mfu, 1),
            }
            history.append(rec)
            (args.out / "history.json").write_text(json.dumps(history, indent=1))
            print(
                f"step {step:>7,}  val {val:.4f}  lr {lr:.2e}  "
                f"{tokens_seen / 1e9:5.2f}B tok  {tps / 1e3:6.1f}k tok/s  "
                f"MFU {mfu:4.1f}%  {elapsed / 3600:5.2f}h",
                flush=True,
            )

        if step > 0 and step % args.checkpoint_every == 0:
            save_checkpoint(args.out / "ckpt.pt", raw_model, opt, cfg, step,
                            history, tokens_seen)

        if step == total_steps:
            break

        opt.zero_grad(set_to_none=True)
        for _ in range(args.grad_accum):
            x, y = get_batch(train_data, args.batch, cfg.block_size, args.device)
            with autocast:
                _, loss = model(x, y)
                # Divide so the accumulated gradient equals the gradient of the
                # mean loss over the full effective batch.
                loss = loss / args.grad_accum
            loss.backward()
        torch.nn.utils.clip_grad_norm_(raw_model.parameters(), args.clip)
        opt.step()
        tokens_seen += tokens_per_step

    save_checkpoint(args.out / "ckpt.pt", raw_model, opt, cfg, total_steps,
                    history, tokens_seen)
    print(f"\ndone in {(time.time() - t0) / 3600:.2f}h -> {args.out / 'ckpt.pt'}", flush=True)
    print(f"peak VRAM: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB", flush=True)


if __name__ == "__main__":
    main()
