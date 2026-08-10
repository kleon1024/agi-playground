"""The reward you had to design is the reward that gets exploited, measured.

The reward-went-up chapter names the inverted U (Gao et al. 2023) and the
three hacks a reward function makes available; this script executes the
case-finding audit those claims point at. A policy walks a one-dimensional
verbosity parameter theta under gradient ascent on a proxy reward whose
peak sits past the true quality peak -- the reward model's blind spot:
it over-weights verbosity. True quality and the proxy agree while the
policy is below the true optimum, then diverge: the proxy keeps rising,
the true quality peaks and falls.

The audit tracks three signals every optimization step: the proxy, the
held-out true quality, and the KL cost from the reference policy. It also
samples the policy's output distribution at checkpoints -- mean response
length and the rate of a spurious keyword the proxy rewards -- because
the distribution drift is the case-finding step that fires before the
held-out eval fully collapses.

Run:
    uv run python core/gaming_audit.py
"""

from __future__ import annotations

import random

THETA_REF = 0.6      # reference policy: too terse for the proxy's taste
TRUE_PEAK = 1.0      # where true quality actually peaks
PROXY_PEAK = 1.5     # where the proxy thinks quality peaks (blind spot)
STEP = 0.01
N_STEPS = 80
CHECKPOINTS = (0, 10, 20, 30, 40, 60, 80)
N_SAMPLES = 500
SEED = 7


def true_quality(theta: float) -> float:
    """Held-out quality: peaks at TRUE_PEAK, symmetric falloff."""
    return 1.0 - (theta - TRUE_PEAK) ** 2


def proxy_reward(theta: float) -> float:
    """The learned reward: peaks at PROXY_PEAK, over-weighting verbosity."""
    return 1.0 - (theta - PROXY_PEAK) ** 2


def kl(theta: float) -> float:
    """KL from the reference policy, quadratic in the parameter walk."""
    return 0.5 * (theta - THETA_REF) ** 2


def keyword_rate(theta: float) -> float:
    """P(the proxy's spurious keyword appears), rising with verbosity."""
    frac = (theta - THETA_REF) / (PROXY_PEAK - THETA_REF)
    return 0.05 + 0.45 * max(0.0, min(1.0, frac))


def main() -> None:
    rng = random.Random(SEED)
    theta = THETA_REF
    walk: list[float] = []
    for _ in range(N_STEPS):
        walk.append(theta)
        grad = 2.0 * (PROXY_PEAK - theta)
        theta += STEP * grad
    walk.append(theta)

    divergence = None
    for t in range(N_STEPS):
        r_now = true_quality(walk[t])
        r_next = true_quality(walk[t + 1])
        p_now = proxy_reward(walk[t])
        p_next = proxy_reward(walk[t + 1])
        if r_next < r_now and p_next > p_now:
            divergence = t + 1
            break

    print(
        "one-dimensional policy walk: reference theta 0.6, true peak 1.0, "
        "proxy peak 1.5"
    )
    print(
        "gradient ascent on the proxy only; true quality and KL read as "
        "held-out signals"
    )
    print()
    print(
        "step  theta  proxy  true   KL      proxy/KL  true/KL"
    )
    prev = None
    for t in CHECKPOINTS:
        th = walk[t]
        p = proxy_reward(th)
        r = true_quality(th)
        k = kl(th)
        if prev is not None:
            dp = p - proxy_reward(prev)
            dr = r - true_quality(prev)
            dk = k - kl(prev)
            p_per_k = dp / dk if dk > 1e-9 else float("inf")
            r_per_k = dr / dk if dk > 1e-9 else float("inf")
            p_per_k_s = f"{p_per_k:8.2f}"
            r_per_k_s = f"{r_per_k:8.2f}"
        else:
            p_per_k_s = "     inf"
            r_per_k_s = "     inf"
        marker = "  <-- true quality peaks here" if t == divergence else ""
        print(f"{t:4d}  {th:5.3f}  {p:5.3f}  {r:5.3f}  {k:5.3f}  "
              f"{p_per_k_s}  {r_per_k_s}{marker}")
        prev = th

    print()
    print("distribution check: 500 responses sampled per checkpoint")
    print("  step  theta  mean length  keyword rate  true quality")
    for t in CHECKPOINTS:
        th = walk[t]
        lengths = [max(1.0, rng.gauss(100.0 * th, 15.0)) for _ in range(N_SAMPLES)]
        mean_len = sum(lengths) / len(lengths)
        rate = sum(
            1 for _ in range(N_SAMPLES) if rng.random() < keyword_rate(th)
        ) / N_SAMPLES
        print(
            f"  {t:4d}  {th:5.3f}  {mean_len:10.1f}  {rate:12.1%}  "
            f"{true_quality(th):12.3f}"
        )

    end_th = walk[N_STEPS]
    print()
    print(
        f"verdict: the proxy rises monotonically "
        f"({proxy_reward(THETA_REF):.2f} -> {proxy_reward(end_th):.2f}) -- by "
        "itself the run looks like success. The held-out"
    )
    print(
        f"quality peaks at step {divergence} (theta {walk[divergence]:.2f}) "
        f"then falls to {true_quality(end_th):.2f}, so the divergence point "
        "is the case-finding"
    )
    print(
        "moment. The distribution check fires at the same place: the "
        "spurious keyword rate and mean length keep"
    )
    print(
        "rising monotonically toward the proxy's blind spot, and the KL tell "
        "shows why -- proxy gain per KL unit"
    )
    print(
        "collapses while true quality per KL unit goes negative, i.e. the "
        "last KL is bought at negative quality."
    )


if __name__ == "__main__":
    main()
