"""The cold-start detour: exploration learns, the estimator decides.

Stage 26's audit shows greedy on lifetime CTR crowns the stale winner
and that the fix is a recency-aware estimator. This detour asks the
exploration side of the same question: a new creative has no history,
so how much traffic does it take to correct its cold-start prior — and
does exploration alone fix selection? It sweeps epsilon over 0.00 to
0.20 with the naive lifetime-average estimator: a mature creative
(lifetime 0.06, true rate 0.025) versus a new creative (true rate
0.04, pessimistic cold-start prior 0.02) over 20,000 placements.

Run:
    uv run python core/cold_start.py
"""

from __future__ import annotations

import random

N = 20_000


def true_rate_a(served_a: int) -> float:
    return 0.025 + 0.035 * (2.71828 ** (-served_a / 3000))


TRUE_RATE_B = 0.04

# Lifetime-average priors: huge history for A, thin pessimistic prior
# for the new creative.
A_LIFETIME = (12_000, 200_000)
B_COLD = (2, 100)  # 0.02 with only 100 impressions of evidence


def run_epsilon(rng: random.Random, epsilon: float) -> tuple[int, int, float]:
    clicks = 0
    served_a = 0
    served_b = 0
    la_clicks, la_imps = A_LIFETIME
    lb_clicks, lb_imps = B_COLD
    for _ in range(N):
        if rng.random() < epsilon:
            choose_a = rng.random() < 0.5
        else:
            choose_a = la_clicks / la_imps >= lb_clicks / lb_imps
        if choose_a:
            served_a += 1
            click = int(rng.random() < true_rate_a(served_a))
            la_clicks += click
            la_imps += 1
        else:
            served_b += 1
            click = int(rng.random() < TRUE_RATE_B)
            lb_clicks += click
            lb_imps += 1
        clicks += click
    return clicks, served_b, lb_clicks / lb_imps


def main() -> None:
    print("cold-start audit: 20,000 placements, fixed seed")
    print("creative A: lifetime CTR 0.06, true rate decays 0.06 -> 0.025")
    print("creative B: true rate 0.04, pessimistic prior 0.02 (thin)\n")
    print(f"  {'epsilon':>8} {'served B':>9} {'B estimate':>11} "
          f"{'clicks':>8} {'clicks/imp':>10}")
    for eps in (0.00, 0.05, 0.10, 0.20):
        rng = random.Random(20260808)
        clicks, served_b, est_b = run_epsilon(rng, eps)
        print(f"  {eps:>8.2f} {served_b:>9} {est_b:>11.4f} "
              f"{clicks:>8} {clicks / N:>10.4f}")

    print("\nreading: raising epsilon corrects B's estimate (0.02 toward")
    print("0.04) but clicks barely move. The corrected estimate loses to A's")
    print("sticky 0.06 lifetime average, so the greedy arm still serves the")
    print("stale winner. Exploration learns the truth; the estimator decides")
    print("whether selection can use it — pair cold-start traffic with a")
    print("recency-aware estimate or the correction is wasted.")


if __name__ == "__main__":
    main()
