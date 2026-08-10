"""The wear-exploration audit: greedy crowns the stale winner.

Stage 26 selects the creative an ad shows. The audit asks the
case-finding question: what happens to selection when the creative
that wins on history is wearing out? It serves 20,000 placements
(fixed seed) to two creatives — a mature one whose lifetime CTR is
0.06 but whose true rate has decayed toward 0.025, and a new one whose
true rate is 0.04 — under four selection policies. Each policy sees
its own Bernoulli click stream, and the creatives wear as they are
served.

Run:
    uv run python core/wear_exploration.py
"""

from __future__ import annotations

import random

N = 20_000

# Mature creative: lifetime log says 0.06 (200k impressions). Its true
# rate wears with cumulative served impressions from 0.06 toward 0.025.
def true_rate_a(served_a: int) -> float:
    return 0.025 + 0.035 * (2.71828 ** (-served_a / 3000))


TRUE_RATE_B = 0.04

# Lifetime-average priors: huge history for A, thin cold-start prior for B.
A_LIFETIME = (12_000, 200_000)  # (clicks, impressions)
B_COLD = (3, 100)

# Recency-aware window: half-life ~1400 placements.
LAMBDA = 1 / 2000
A_WINDOW = (120, 1880)  # (clicks, impressions) at 0.06
B_WINDOW = (60, 1940)  # (clicks, impressions) at 0.03


def run_policy(
    rng: random.Random,
    mode: str,
    epsilon: float = 0.0,
) -> tuple[int, int, int]:
    """Serve N placements; return (clicks, served_a, served_b)."""
    clicks = 0
    served_a = 0
    served_b = 0

    if mode in ("lifetime", "epsilon"):
        # Lifetime average estimator, greedy or epsilon-greedy.
        la_clicks, la_imps = A_LIFETIME
        lb_clicks, lb_imps = B_COLD
        for _ in range(N):
            if mode == "epsilon" and rng.random() < epsilon:
                choose_a = rng.random() < 0.5
            else:
                est_a = la_clicks / la_imps
                est_b = lb_clicks / lb_imps
                choose_a = est_a >= est_b
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

    elif mode == "ewma":
        # Recency-weighted estimate, greedy (no exploration).
        est_a = A_WINDOW[0] / sum(A_WINDOW)
        est_b = B_WINDOW[0] / sum(B_WINDOW)
        for _ in range(N):
            choose_a = est_a >= est_b
            if choose_a:
                served_a += 1
                click = int(rng.random() < true_rate_a(served_a))
                est_a = (1 - LAMBDA) * est_a + LAMBDA * click
            else:
                served_b += 1
                click = int(rng.random() < TRUE_RATE_B)
                est_b = (1 - LAMBDA) * est_b + LAMBDA * click
            clicks += click

    elif mode == "thompson":
        # Beta posteriors whose counts decay, so the estimate forgets
        # the creative's old peak and tracks wear.
        alpha_a, beta_a = A_WINDOW
        alpha_b, beta_b = B_WINDOW
        for _ in range(N):
            theta_a = rng.betavariate(alpha_a, beta_a)
            theta_b = rng.betavariate(alpha_b, beta_b)
            if theta_a >= theta_b:
                served_a += 1
                click = int(rng.random() < true_rate_a(served_a))
                alpha_a += click
                beta_a += 1 - click
            else:
                served_b += 1
                click = int(rng.random() < TRUE_RATE_B)
                alpha_b += click
                beta_b += 1 - click
            # Decay the counts: old evidence is worth less than new.
            decay = 1 - LAMBDA
            alpha_a, beta_a = alpha_a * decay, beta_a * decay
            alpha_b, beta_b = alpha_b * decay, beta_b * decay
            clicks += click

    return clicks, served_a, served_b


def main() -> None:
    print("wear-exploration audit: 20,000 placements, fixed seed")
    print("creative A: lifetime CTR 0.06, true rate decays 0.06 -> 0.025")
    print("creative B: true rate 0.04, cold-start prior 0.03\n")
    print(f"  {'policy':>28} {'clicks':>8} {'served A':>9} {'served B':>9} "
          f"{'clicks/imp':>10}")
    policies = [
        ("greedy, lifetime CTR", "lifetime", 0.0),
        ("epsilon-greedy 0.10, lifetime", "epsilon", 0.10),
        ("greedy, recency-weighted (EWMA)", "ewma", 0.0),
        ("Thompson, decaying counts", "thompson", 0.0),
    ]
    for label, mode, eps in policies:
        rng = random.Random(20260808)
        clicks, served_a, served_b = run_policy(rng, mode, eps)
        print(f"  {label:>28} {clicks:>8} {served_a:>9} {served_b:>9} "
              f"{clicks / N:>10.4f}")

    print("\nreading: greedy on lifetime CTR crowns the stale winner — A's")
    print("0.06 history hides the decay to 0.025, so the policy keeps serving")
    print("it and never estimates B. Exploration alone barely helps: the")
    print("greedy arm still reads the same sticky average. The fix is the")
    print("estimator, not the policy: a recency-weighted estimate or a")
    print("decaying Bayesian posterior lets selection see the wear and")
    print("switch to the creative that is actually better.")


if __name__ == "__main__":
    main()
