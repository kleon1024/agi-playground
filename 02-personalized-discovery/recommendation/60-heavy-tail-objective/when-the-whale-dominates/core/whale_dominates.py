"""When the whale dominates: one big order is a whole batch of
gradient. The run shows the gradient share of the top 1% orders under
raw MSE and under the log transform on the amount distribution.

Run:
    uv run python core/whale_dominates.py
"""

from __future__ import annotations

import math
import random


def main() -> None:
    rng = random.Random(59)
    n = 50000
    amounts = [math.exp(rng.gauss(6.0, 2.0)) for _ in range(n)]
    m_raw = sum(amounts) / n
    grad_raw = [abs(a - m_raw) for a in amounts]
    logs = [math.log(a) for a in amounts]
    m_log = sum(logs) / n
    grad_log = [abs(v - m_log) for v in logs]

    def share_of_top(grad: list[float], top_frac: float = 0.01) -> float:
        by_amt = sorted(range(len(amounts)), key=lambda i: amounts[i])
        top = set(by_amt[-int(len(amounts) * top_frac):])
        return sum(grad[i] for i in top) / sum(grad)

    print("when the whale dominates, read (gradient share):")
    print(f"  raw mse      top 1% of orders own {share_of_top(grad_raw):.1%} of the gradient")
    print(f"  log amount   top 1% of orders own {share_of_top(grad_log):.1%} of the gradient")
    print()
    print("reading: under raw MSE the top 1% of orders own a quarter of the")
    print("gradient — twenty-five times their fair share — so the model fits")
    print("whales and treats the 99% as noise. the log transform compresses")
    print("the tail to 3%; a whale is still worth more, but it no longer is")
    print("the whole argument.")


if __name__ == "__main__":
    main()
