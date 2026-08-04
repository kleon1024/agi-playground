"""The same INT8 weight-only quantization, through torchao's real kernel path,
against the same checkpoint core/quantize.py used.

torchao's `Int8WeightOnlyConfig` stores the identical representation --
per-channel scale plus an int8 tensor -- that `core/quantize.py` builds by
hand. The difference is what runs the matmul: torchao dispatches to
`torch.ops.aten._int_mm`, a real int8 GEMM, instead of dequantizing to fp32
and calling an ordinary `F.linear`. That is the one question this file
answers: does a real int8 kernel get further than the honest-but-naive
dequant-then-matmul `core/` uses, on the same shapes.

Usage:
    python torchao_quantize.py bench --checkpoint <ckpt.pt>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "missions/01-language-model-agent/05-serve/core"))
sys.path.insert(0, str(ROOT / "missions/01-language-model-agent/02-pretrain/core"))
sys.path.insert(0, str(ROOT / "missions/01-language-model-agent/05-serve/graph-execution/core"))
from engine import load_model
from graph_decode import _median, _time, decode_eager
from model import build_rope_cache
from torchao.quantization import Int8WeightOnlyConfig, quantize_


def cmd_bench(args) -> None:
    model, cfg = load_model(args.checkpoint, args.device)
    cos, sin = build_rope_cache(args.max_len, cfg.d_head, cfg.rope_theta, args.device)
    prompt = list(range(args.prompt_len))
    n = args.max_new_tokens

    q_model, q_cfg = load_model(args.checkpoint, args.device)
    # Quantize every nn.Linear reachable from the blocks -- attention and
    # SwiGLU projections -- the same scope core/quantize.py covers. The tied
    # embedding/head module is `model.tok` / `model.head`; filtering to
    # `model.blocks` only leaves them fp32, matching core/'s scope exactly.
    quantize_(q_model.blocks, Int8WeightOnlyConfig())

    ref = decode_eager(model, cfg, cos, sin, prompt, args.verify_tokens, args.device, False)
    got = decode_eager(q_model, q_cfg, cos, sin, prompt, args.verify_tokens, args.device, False)
    n_match = sum(1 for a, b in zip(ref, got) if a == b)
    print(f"identity check: {n_match}/{args.verify_tokens} tokens match eager fp32\n")

    configs = [
        ("eager, fp32",
         lambda: decode_eager(model, cfg, cos, sin, prompt, n, args.device, False)),
        ("eager, torchao int8",
         lambda: decode_eager(q_model, q_cfg, cos, sin, prompt, n, args.device, False)),
    ]
    rows = [(name, _time(fn, warmup=1, repeat=args.repeat, tokens=n)) for name, fn in configs]

    base = _median(rows[0][1])
    print(f"prompt {args.prompt_len}, {n} new tokens, batch 1, {args.repeat} rounds each")
    print(f"{'configuration':<28}{'tok/s':>10}{'ms/token':>11}{'round spread':>15}{'vs eager fp32':>15}")
    for name, tps in rows:
        med = _median(tps)
        print(f"{name:<28}{med:10.1f}{1000 / med:11.3f}"
              f"{min(tps):7.1f}-{max(tps):<7.1f}{med / base:14.2f}x")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("bench")
    p.add_argument("--checkpoint", type=Path, default=None)
    p.add_argument("--device", default="cuda")
    p.add_argument("--prompt-len", type=int, default=64)
    p.add_argument("--max-len", type=int, default=1024)
    p.add_argument("--max-new-tokens", type=int, default=128)
    p.add_argument("--repeat", type=int, default=5)
    p.add_argument("--verify-tokens", type=int, default=64)
    args = ap.parse_args()
    cmd_bench(args)


if __name__ == "__main__":
    main()
