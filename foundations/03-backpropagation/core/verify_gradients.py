"""Check 1: does the engine's gradient match a hand-derived closed form?

f(a, b, c) = (a*b + c) * a = a^2*b + a*c, L = tanh(f)

Written out as a single expression, 'a' appears twice, so the closed-form
partial derivatives already reflect the total derivative:
    dL/df = 1 - tanh(f)^2
    dL/da = dL/df * (2*a*b + c)
    dL/db = dL/df * a^2
    dL/dc = dL/df * a

No dependency beyond stdlib -- this check never imports torch.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

from engine import Value, diamond_expression

A, B, C = 0.7, -0.5, 1.2


def analytical_gradients(a: float, b: float, c: float) -> dict:
    f = (a * b + c) * a
    loss = math.tanh(f)
    dloss_df = 1 - loss * loss
    return {
        "loss": loss,
        "da": dloss_df * (2 * a * b + c),
        "db": dloss_df * (a * a),
        "dc": dloss_df * a,
    }


def engine_gradients(a: float, b: float, c: float) -> dict:
    va, vb, vc = Value(a), Value(b), Value(c)
    loss = diamond_expression(va, vb, vc)
    loss.backward()
    return {"loss": loss.data, "da": va.grad, "db": vb.grad, "dc": vc.grad}


def main() -> None:
    start = time.perf_counter()
    analytical = analytical_gradients(A, B, C)
    engine = engine_gradients(A, B, C)
    wall_clock_s = time.perf_counter() - start

    max_abs_diff = max(abs(analytical[k] - engine[k]) for k in ("loss", "da", "db", "dc"))
    assert max_abs_diff < 1e-12, (
        f"engine gradient diverged from closed-form analytical gradient: "
        f"max abs diff {max_abs_diff}"
    )

    print(f"a={A}, b={B}, c={C}")
    print(f"L               engine={engine['loss']:.12f}  analytical={analytical['loss']:.12f}")
    print(f"dL/da           engine={engine['da']:.12f}  analytical={analytical['da']:.12f}")
    print(f"dL/db           engine={engine['db']:.12f}  analytical={analytical['db']:.12f}")
    print(f"dL/dc           engine={engine['dc']:.12f}  analytical={analytical['dc']:.12f}")
    print(f"max_abs_diff={max_abs_diff:.3e}  (assert threshold 1e-12, passed)")

    out = {
        "inputs": {"a": A, "b": B, "c": C},
        "engine": engine,
        "analytical": analytical,
        "max_abs_diff_engine_vs_analytical": max_abs_diff,
        "wall_clock_s": wall_clock_s,
    }
    out_path = Path(__file__).resolve().parent.parent / "runs" / "gradient-check.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
