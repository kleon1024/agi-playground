"""Show a proxy metric and the true objective it stands in for diverge.

Two functions share one genuine-quality term and differ in how they treat a
second knob that is cheap to move and easy to fake:

    true_objective(i, p)  = 10*sqrt(i) - 0.6*p
    proxy_metric(i, p)    = 10*sqrt(i) + 0.4*p

`i` (informativeness) is capped at 50 and has diminishing returns in both
functions. `p` (padding) is a real cost to the true objective but a reward to
the proxy — the proxy's stand-in for "an automated grader that treats length
as evidence of thoroughness," modeled on the length-reward-hacking finding in
Singhal et al. 2023 (arXiv:2310.03716). A hill-climber that only ever sees the
proxy has no way to know p is hurting anything.

Two runs, same starting point, same step budget:

  - `proxy_hillclimb`: accepts a move only if it raises the proxy. This is
    the only optimizer that never observes the true objective.
  - `true_hillclimb`: accepts a move only if it raises the true objective.
    A control showing what optimizing the real thing looks like.

Usage:
    python goodhart.py --steps 2000 --seed 0 --out ../runs/goodhart-run.json
"""

from __future__ import annotations

import argparse
import json
import math
import random

I_CAP = 50.0
P_CAP = 1.0e6


def true_objective(i: float, p: float) -> float:
    return 10.0 * math.sqrt(i) - 0.6 * p


def proxy_metric(i: float, p: float) -> float:
    return 10.0 * math.sqrt(i) + 0.4 * p


def hillclimb(rng: random.Random, steps: int, objective) -> list[dict]:
    i, p = 0.0, 0.0
    trace = []
    for step in range(steps):
        if rng.random() < 0.5:
            cand_i = min(I_CAP, max(0.0, i + rng.uniform(-2.0, 2.0)))
            cand_p = p
        else:
            cand_i = i
            cand_p = min(P_CAP, max(0.0, p + rng.uniform(-3.0, 3.0)))
        if objective(cand_i, cand_p) > objective(i, p):
            i, p = cand_i, cand_p
        trace.append(
            {
                "step": step,
                "i": i,
                "p": p,
                "proxy": proxy_metric(i, p),
                "true": true_objective(i, p),
            }
        )
    return trace


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return float("nan")
    return cov / math.sqrt(vx * vy)


def windowed_correlation(trace: list[dict], window: int) -> list[dict]:
    out = []
    for start in range(0, len(trace) - window + 1, window):
        chunk = trace[start : start + window]
        proxies = [r["proxy"] for r in chunk]
        trues = [r["true"] for r in chunk]
        out.append(
            {
                "start_step": start,
                "end_step": start + window - 1,
                "correlation": pearson(proxies, trues),
                "mean_i": sum(r["i"] for r in chunk) / window,
                "mean_p": sum(r["p"] for r in chunk) / window,
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--window", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    rng_proxy = random.Random(args.seed)
    rng_true = random.Random(args.seed)

    proxy_trace = hillclimb(rng_proxy, args.steps, proxy_metric)
    true_trace = hillclimb(rng_true, args.steps, true_objective)

    windows = windowed_correlation(proxy_trace, args.window)

    result = {
        "steps": args.steps,
        "window": args.window,
        "seed": args.seed,
        "i_cap": I_CAP,
        "p_cap": P_CAP,
        "proxy_optimizer_final": proxy_trace[-1],
        "true_optimizer_final": true_trace[-1],
        "proxy_optimizer_windowed_correlation": windows,
        "first_window_correlation": windows[0]["correlation"],
        "last_window_correlation": windows[-1]["correlation"],
    }

    text = json.dumps(result, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
