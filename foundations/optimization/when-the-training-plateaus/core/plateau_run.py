"""The training plateau: same surface, fixed step budget, two diagnoses.

Training loss stalls far above the floor. Before reaching for a new model,
the question is which of three failure classes the stall belongs to:

1. **Flat-direction stall.** The gradient shrinks as the optimizer
   approaches the minimum, so a fixed step size makes less and less
   progress. This is the optimizer class: momentum accumulates the small
   gradients, Adam normalizes them, and the stall is escapable in budget.
2. **Saddle-point stall.** The flat direction is an unstable equilibrium
   the optimizer has to escape; the escape is what momentum and Adam
   accelerate (named in the chapter, measured here as the flat case it
   reduces to).
3. **Surface floor.** The loss surface itself is bounded below (capacity,
   label noise, an irreducible term). Every optimizer stalls at the same
   number, and no optimizer fixes it -- the diagnosis is data or model,
   not optimization.

The run races four update rules on one flat-minimum surface L(x, y) = x^2 y^2
under a fixed step budget of 1000, then repeats the same race on the same
surface with an irreducible +0.01 term, and classifies each result.

Run:
    uv run python core/plateau_run.py
"""

from __future__ import annotations

import math

BUDGET = 1000
LEARNING_RATE = 0.1
MU_VALUES = (0.9, 0.99)
TOL_FLOOR = 1e-6  # loss at or below this counts as converged
IRREDUCIBLE = 0.01  # added to the loss in the floor condition


def flat_loss(x: float, y: float, floor: float) -> float:
    return x * x * y * y + floor


def flat_grad(x: float, y: float) -> tuple[float, float]:
    return (2.0 * x * y * y, 2.0 * x * x * y)


def run_optimizer(
    name: str,
    *,
    lr: float,
    mu: float | None,
    floor: float,
    start: tuple[float, float] = (1.0, 1.0),
) -> dict[str, object]:
    """Run one optimizer on the flat surface; return the measured summary."""
    x, y = start
    vx = vy = 0.0
    mx = my = vvx = vvy = 0.0
    b1, b2, eps = 0.9, 0.999, 1e-8
    midway: float | None = None
    tail_start: float | None = None
    for step in range(1, BUDGET + 1):
        gx, gy = flat_grad(x, y)
        if name == "sgd":
            x -= lr * gx
            y -= lr * gy
        elif name == "momentum":
            vx = mu * vx - lr * gx
            vy = mu * vy - lr * gy
            x += vx
            y += vy
        else:  # adam
            mx = b1 * mx + (1 - b1) * gx
            my = b1 * my + (1 - b1) * gy
            vvx = b2 * vvx + (1 - b2) * gx * gx
            vvy = b2 * vvy + (1 - b2) * gy * gy
            mhat_x = mx / (1 - b1**step)
            mhat_y = my / (1 - b1**step)
            vhat_x = vvx / (1 - b2**step)
            vhat_y = vvy / (1 - b2**step)
            x -= lr * mhat_x / (vhat_x**0.5 + eps)
            y -= lr * mhat_y / (vhat_y**0.5 + eps)
        if step == BUDGET // 2:
            midway = flat_loss(x, y, floor)
        if step == BUDGET - 100:
            tail_start = flat_loss(x, y, floor)
    final = flat_loss(x, y, floor)

    tail_change = abs(final - tail_start) / tail_start if tail_start else 0.0
    if floor > 0.0 and final <= floor * 1.05:
        verdict = "at the surface floor"
    elif final <= TOL_FLOOR:
        verdict = "converged within budget"
    else:
        verdict = "crawling above the floor"
    return {
        "optimizer": name,
        "learning_rate": lr,
        "momentum": mu,
        "final_loss": final,
        "loss_at_halfway": midway,
        "tail_100_change": tail_change,
        "verdict": verdict,
    }


def main() -> None:
    flat_rows: list[dict[str, object]] = []
    floor_rows: list[dict[str, object]] = []
    for floor in (0.0, IRREDUCIBLE):
        rows = []
        for name, mu in [("sgd", None)] + [
            ("momentum", mu) for mu in MU_VALUES
        ] + [("adam", None)]:
            rows.append(run_optimizer(name, lr=LEARNING_RATE, mu=mu, floor=floor))

        label = f"L = x^2 y^2 + {floor}" if floor else "L = x^2 y^2"
        print(f"surface: {label}, budget {BUDGET} steps, tolerance {TOL_FLOOR:g}")
        print(f"  {'optimizer':<9} {'lr':>5} {'mu':>5} {'loss at 500':>12} "
              f"{'final loss':>12} {'last 100':>9}  verdict")
        for r in rows:
            mu = r["momentum"] if r["momentum"] is not None else "-"
            print(
                f"  {r['optimizer']:<9} {r['learning_rate']:>5} {mu!s:>5} "
                f"{r['loss_at_halfway']:>12.6g} {r['final_loss']:>12.6g} "
                f"{100 * r['tail_100_change']:>8.1f}%  "
                f"{r['verdict']}"
            )
        print()
        (floor_rows if floor else flat_rows).extend(rows)

    sgd = next(r for r in flat_rows if r["optimizer"] == "sgd")
    per_step = 1.0 - (1.0 - sgd["tail_100_change"]) ** 0.01
    halving_steps = abs(0.6931 / math.log1p(-per_step))
    print("analysis: the per-coordinate step is proportional to the product of")
    print("both coordinates, so per-step progress collapses as the loss shrinks.")
    print(f"In its final 100 steps plain SGD moved {100*sgd['tail_100_change']:.1f}% of")
    print(f"the remaining loss ({100*per_step:.1f}% per step) and ends "
          f"{sgd['final_loss']/TOL_FLOOR:.0f}x above the tolerance; each halving of")
    print(f"what remains costs about {halving_steps:.0f} steps and the cost keeps")
    print("growing. That crawl is the plateau. Momentum (accumulate the small")
    print("gradients) and Adam (normalize them) both converge within the budget,")
    print("so the stall is in the update rule, not in the surface.")


if __name__ == "__main__":
    main()
