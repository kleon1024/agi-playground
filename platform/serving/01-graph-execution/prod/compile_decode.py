"""The same win, asked for instead of built: `torch.compile(mode="reduce-overhead")`.

`core/graph_decode.py` captures a CUDA graph by hand, which meant rewriting the
decode step three ways to make it capturable — device-side token selection, a
device-side position, and a fixed attention shape. `reduce-overhead` mode uses
CUDA graphs underneath and does that work for you: it traces the step, decides
what is static, and manages the memory pool the replay writes into.

What it cannot do is change the *shape* problem. A decode step whose attention
window grows every token still triggers a recompilation per shape unless the
shape is pinned, so this file pins it the same way `core/` does and lets the
compiler handle everything else. That is the honest comparison: same fixed-shape
step, hand-rolled capture against the compiler's.

Run it after `core/graph_decode.py bench`, and expect the two to land close. If
the compiler wins, the hand-rolled version left something on the table; if it
loses, the tracing overhead is not paying for itself at this size. Either
outcome is worth knowing before writing capture code by hand in production.

Usage:
    python compile_decode.py --checkpoint <ckpt.pt> --max-new-tokens 128
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "platform/serving/01-graph-execution/core"))
sys.path.insert(0, str(ROOT / "missions/01-language-model-agent/05-serve/core"))
sys.path.insert(0, str(ROOT / "missions/01-language-model-agent/02-pretrain/core"))
from engine import load_model
from graph_decode import GraphedDecoder, decode_eager
from model import build_rope_cache


class CompiledDecoder(GraphedDecoder):
    """`GraphedDecoder` with the explicit capture replaced by the compiler.

    Everything the base class does to make the step *capturable* is still
    required — a compiler cannot remove a host synchronisation that the
    algorithm asks for, and it cannot pin a shape the code varies. What it
    replaces is `capture()`: the stream warm-up, the graph object, the replay,
    and the memory-pool reasoning behind them.
    """

    def compile(self) -> None:
        self._compiled = torch.compile(self._step, mode="reduce-overhead")

    @torch.no_grad()
    def generate(self, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
        self.prefill(prompt_ids)
        for _ in range(max_new_tokens):
            self._compiled()
        return self.generated[:max_new_tokens].tolist()


def _time(fn, *, repeat: int, tokens: int) -> list[float]:
    out = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        torch.cuda.synchronize()
        out.append(tokens / (time.perf_counter() - t0))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", type=Path, default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--prompt-len", type=int, default=64)
    ap.add_argument("--max-len", type=int, default=1024)
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--repeat", type=int, default=15)
    args = ap.parse_args()

    model, cfg = load_model(args.checkpoint, args.device)
    cos, sin = build_rope_cache(args.max_len, cfg.d_head, cfg.rope_theta, args.device)
    prompt = list(range(args.prompt_len))
    n = args.max_new_tokens

    ref = decode_eager(model, cfg, cos, sin, prompt, 32, args.device)

    graphed = GraphedDecoder(model, cfg, args.max_len, args.device)
    graphed.generate(prompt, 8)

    compiled = CompiledDecoder(model, cfg, args.max_len, args.device)
    compiled.compile()
    t0 = time.perf_counter()
    first = compiled.generate(prompt, 32)
    torch.cuda.synchronize()
    warmup_s = time.perf_counter() - t0

    # Correctness first, for both, against the same eager reference.
    for name, got in (("hand-rolled graph", graphed.generate(prompt, 32)), ("compiled", first)):
        if got != ref:
            bad = next(i for i, (a, b) in enumerate(zip(ref, got)) if a != b)
            raise SystemExit(f"{name} disagrees with eager at token {bad}: {ref[bad]} vs {got[bad]}")
    print(f"identity check: both paths match eager on {len(ref)} tokens")
    print(f"first compiled call (trace + capture): {warmup_s:.1f}s\n")

    rows = [
        ("eager (engine.py)",
         _time(lambda: decode_eager(model, cfg, cos, sin, prompt, n, args.device),
               repeat=args.repeat, tokens=n)),
        ("hand-rolled CUDA graph",
         _time(lambda: graphed.generate(prompt, n), repeat=args.repeat, tokens=n)),
        ("torch.compile reduce-overhead",
         _time(lambda: compiled.generate(prompt, n), repeat=args.repeat, tokens=n)),
    ]

    base = statistics.median(rows[0][1])
    print(f"prompt {args.prompt_len}, {n} new tokens, batch 1, {args.repeat} rounds each")
    print(f"{'configuration':<32}{'tok/s':>9}{'round spread':>16}{'vs eager':>10}")
    for name, tps in rows:
        med = statistics.median(tps)
        print(f"{name:<32}{med:9.1f}{min(tps):8.1f}-{max(tps):<7.1f}{med / base:9.2f}x")


if __name__ == "__main__":
    main()
