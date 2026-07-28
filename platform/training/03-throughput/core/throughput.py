"""Measure one training configuration's throughput, so a ladder of them can
say where the wall-clock actually goes.

Stage 02 of mission 01 measured a single pair: the same model, the same batch,
the same card, 85.5k tokens/second without `torch.compile` and 165.6k with it.
That is a 1.76x wall-clock saving from one flag, and it raises the obvious
question this script exists to answer — which of the other flags matter, and
by how much, on the same hardware.

The measured quantities are tokens/second and MFU. Tokens/second is what you
feel; MFU is what lets you compare across model sizes, because it is the
fraction of the card's advertised bf16 throughput the run actually converts
into gradient. A configuration that doubles tokens/second by shrinking the
model has not improved anything, and MFU is what says so.

One configuration per process, deliberately. `torch.compile` leaves compiled
artifacts and allocator state behind, and SDPA backend selection is process
global; measuring rung N+1 in a process that already ran rung N measures the
leftovers as much as the change. The `ladder` subcommand therefore re-invokes
this file as a subprocess per rung.

Usage:
    python throughput.py run --dtype bf16 --compile --attn flash --fused-adam
    python throughput.py ladder --out runs/ladder.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from contextlib import nullcontext
from pathlib import Path

import torch
import torch.utils.checkpoint  # `import torch` alone does not bring this in

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "missions/01-language-model-agent/02-pretrain/core"))
from model import Config, Transformer

# The card this repository's local lane uses, bf16 dense, no sparsity. Only the
# MFU column depends on it; tokens/second does not.
PEAK_FLOPS = 165e12

# Each rung is a delta from the one above it, so the table reads as a running
# total rather than a set of unrelated experiments. The last two are not
# cumulative and say so in their own field: they answer "what does this cost"
# rather than "what does this save".
LADDER = [
    {"name": "fp32 eager, math attention", "dtype": "fp32", "attn": "math"},
    {"name": "+ bf16 autocast", "dtype": "bf16", "attn": "math"},
    {"name": "+ flash attention", "dtype": "bf16", "attn": "flash"},
    {"name": "+ fused AdamW", "dtype": "bf16", "attn": "flash", "fused_adam": True},
    {"name": "+ torch.compile", "dtype": "bf16", "attn": "flash", "fused_adam": True, "compile": True},
    {
        "name": "+ activation checkpointing",
        "dtype": "bf16",
        "attn": "flash",
        "fused_adam": True,
        "compile": True,
        "recompute": True,
        "cumulative": False,
    },
]


class _Recomputed(torch.nn.Module):
    """Run a block without saving its intermediate activations, and recompute
    them during the backward pass instead.

    This is the memory-for-time trade in its most direct form: the block's
    forward runs twice and its activations are held for microseconds instead of
    for the whole step. The `use_reentrant=False` implementation is the one
    that composes with `torch.compile`; the older reentrant path silently
    breaks under it.
    """

    def __init__(self, block: torch.nn.Module) -> None:
        super().__init__()
        self.block = block

    def forward(self, *args):
        return torch.utils.checkpoint.checkpoint(self.block, *args, use_reentrant=False)


def _wrap_blocks_in_checkpoint(model: torch.nn.Module) -> None:
    model.blocks = torch.nn.ModuleList([_Recomputed(b) for b in model.blocks])


def measure(
    *,
    dtype: str,
    attn: str,
    fused_adam: bool,
    compile_model: bool,
    recompute: bool,
    micro_batch: int,
    steps: int,
    warmup: int,
) -> dict:
    """Time `steps` full training steps and report tokens/second, MFU, and peak
    memory. `warmup` steps run first and are discarded, because the first step
    pays for cuDNN autotuning, allocator growth, and — with `compile_model` —
    the entire compilation.
    """
    torch.manual_seed(0)
    device = "cuda"
    cfg = Config()
    model = Transformer(cfg).to(device)
    n_params = sum(p.numel() for p in model.parameters())

    if recompute:
        _wrap_blocks_in_checkpoint(model)

    raw_model = model
    if compile_model:
        model = torch.compile(model)

    opt = torch.optim.AdamW(
        raw_model.parameters(), lr=6e-4, betas=(0.9, 0.95), weight_decay=0.1, fused=fused_adam
    )
    autocast = (
        torch.autocast("cuda", dtype=torch.bfloat16) if dtype == "bf16" else nullcontext()
    )
    backends = {
        "math": [torch.nn.attention.SDPBackend.MATH],
        "flash": [torch.nn.attention.SDPBackend.FLASH_ATTENTION],
    }[attn]

    tokens = torch.randint(0, cfg.vocab_size, (micro_batch, cfg.block_size + 1), device=device)
    x, y = tokens[:, :-1].contiguous(), tokens[:, 1:].contiguous()

    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    with torch.nn.attention.sdpa_kernel(backends):
        for step in range(warmup + steps):
            if step == warmup:
                torch.cuda.synchronize()
                t0 = time.perf_counter()
            with autocast:
                _, loss = model(x, y)
            loss.backward()
            opt.step()
            opt.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - t0

    tokens_seen = steps * micro_batch * cfg.block_size
    tps = tokens_seen / elapsed
    # The standard approximation: 6 FLOPs per parameter per token for the
    # forward-and-backward matmuls, plus the attention term, which is quadratic
    # in sequence length and therefore not absorbed by the parameter count.
    flops_per_token = 6 * n_params + 12 * cfg.n_layer * cfg.block_size * cfg.d_model
    return {
        "tokens_per_second": round(tps),
        "mfu_pct": round(tps * flops_per_token / PEAK_FLOPS * 100, 1),
        "step_ms": round(elapsed / steps * 1000, 1),
        "peak_memory_mb": round(torch.cuda.max_memory_allocated() / 1e6, 1),
        "params": n_params,
    }


def run_ladder(out: Path | None, micro_batch: int, steps: int, warmup: int) -> None:
    """Run every rung in its own process and print the table.

    A rung that dies is recorded as a failure rather than skipped. Out of
    memory is a real property of a configuration at this batch size, and a
    table that silently omits it would suggest the configuration is simply
    absent rather than unusable.
    """
    results = []
    for rung in LADDER:
        cmd = [sys.executable, __file__, "run", "--json",
               "--micro-batch", str(micro_batch), "--steps", str(steps), "--warmup", str(warmup),
               "--dtype", rung["dtype"], "--attn", rung["attn"]]
        if rung.get("fused_adam"):
            cmd.append("--fused-adam")
        if rung.get("compile"):
            cmd.append("--compile")
        if rung.get("recompute"):
            cmd.append("--recompute")

        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            tail = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "no stderr"
            record = {"name": rung["name"], "failed": tail}
        else:
            record = {"name": rung["name"], **json.loads(proc.stdout.splitlines()[-1])}
        record["cumulative"] = rung.get("cumulative", True)
        results.append(record)
        print(json.dumps(record))

    print(f"\n{'configuration':<32}{'tok/s':>10}{'MFU':>8}{'step':>10}{'peak':>11}")
    baseline = next((r["tokens_per_second"] for r in results if "tokens_per_second" in r), None)
    for r in results:
        if "failed" in r:
            print(f"{r['name']:<32}{r['failed']:>39}")
            continue
        rel = f"{r['tokens_per_second'] / baseline:.2f}x" if baseline else ""
        print(f"{r['name']:<32}{r['tokens_per_second']:>10}{r['mfu_pct']:>7.1f}%"
              f"{r['step_ms']:>9.1f}ms{r['peak_memory_mb']:>9.1f}MB  {rel}")

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"micro_batch": micro_batch, "steps": steps,
                                   "peak_flops": PEAK_FLOPS, "rungs": results}, indent=2))
        print(f"\nwrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    one = sub.add_parser("run", help="measure a single configuration")
    one.add_argument("--dtype", choices=["fp32", "bf16"], default="bf16")
    one.add_argument("--attn", choices=["math", "flash"], default="flash")
    one.add_argument("--fused-adam", action="store_true")
    one.add_argument("--compile", dest="compile_model", action="store_true")
    one.add_argument("--recompute", action="store_true", help="activation checkpointing")
    one.add_argument("--micro-batch", type=int, default=16)
    one.add_argument("--steps", type=int, default=30)
    one.add_argument("--warmup", type=int, default=10)
    one.add_argument("--json", action="store_true", help="emit one JSON line and nothing else")

    lad = sub.add_parser("ladder", help="run every rung in its own process")
    lad.add_argument("--out", type=Path, default=None)
    lad.add_argument("--micro-batch", type=int, default=16)
    lad.add_argument("--steps", type=int, default=30)
    lad.add_argument("--warmup", type=int, default=10)

    args = ap.parse_args()
    if args.command == "ladder":
        run_ladder(args.out, args.micro_batch, args.steps, args.warmup)
        return

    result = measure(
        dtype=args.dtype, attn=args.attn, fused_adam=args.fused_adam,
        compile_model=args.compile_model, recompute=args.recompute,
        micro_batch=args.micro_batch, steps=args.steps, warmup=args.warmup,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
