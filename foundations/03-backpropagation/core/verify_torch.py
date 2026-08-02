"""Check 2: does the engine's gradient match torch's own `.backward()`?

This is the load-bearing cross-check: it connects the scalar engine built in
this chapter to the exact call ../01-first-training-loop/core/train_gpt.py
already makes without explaining. Same diamond expression as
verify_gradients.py, built once with this chapter's `Value` engine and once
with torch tensors, on the identical inputs.

Requires the optional `torch` dependency group:
    uv run --group torch python core/verify_torch.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from engine import Value, diamond_expression
from verify_gradients import A, B, C


def torch_gradients(a: float, b: float, c: float) -> dict:
    ta = torch.tensor(a, dtype=torch.float64, requires_grad=True)
    tb = torch.tensor(b, dtype=torch.float64, requires_grad=True)
    tc = torch.tensor(c, dtype=torch.float64, requires_grad=True)
    d = ta * tb
    e = d + tc
    f = e * ta
    loss = torch.tanh(f)
    loss.backward()
    return {
        "loss": loss.item(),
        "da": ta.grad.item(),
        "db": tb.grad.item(),
        "dc": tc.grad.item(),
    }


def engine_gradients(a: float, b: float, c: float) -> dict:
    va, vb, vc = Value(a), Value(b), Value(c)
    loss = diamond_expression(va, vb, vc)
    loss.backward()
    return {"loss": loss.data, "da": va.grad, "db": vb.grad, "dc": vc.grad}


def main() -> None:
    start = time.perf_counter()
    engine = engine_gradients(A, B, C)
    torch_result = torch_gradients(A, B, C)
    wall_clock_s = time.perf_counter() - start

    max_abs_diff = max(abs(engine[k] - torch_result[k]) for k in ("loss", "da", "db", "dc"))
    assert max_abs_diff < 1e-12, (
        f"engine gradient diverged from torch .backward(): max abs diff {max_abs_diff}"
    )

    print(f"torch version: {torch.__version__}")
    print(f"a={A}, b={B}, c={C}")
    print(f"L               engine={engine['loss']:.12f}  torch={torch_result['loss']:.12f}")
    print(f"dL/da           engine={engine['da']:.12f}  torch={torch_result['da']:.12f}")
    print(f"dL/db           engine={engine['db']:.12f}  torch={torch_result['db']:.12f}")
    print(f"dL/dc           engine={engine['dc']:.12f}  torch={torch_result['dc']:.12f}")
    print(f"max_abs_diff={max_abs_diff:.3e}  (assert threshold 1e-12, passed)")

    out = {
        "inputs": {"a": A, "b": B, "c": C},
        "torch_version": torch.__version__,
        "engine": engine,
        "torch": torch_result,
        "max_abs_diff_engine_vs_torch": max_abs_diff,
        "wall_clock_s": wall_clock_s,
    }
    out_path = Path(__file__).resolve().parent.parent / "runs" / "torch-cross-check.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
