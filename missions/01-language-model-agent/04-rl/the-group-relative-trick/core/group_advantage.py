"""The group-relative trick, as arithmetic on reward groups.

GRPO replaces PPO's learned critic with a group statistic. For one prompt,
the policy samples G completions, the verifier scores them, and the advantage
of member i is:

    A_i = (r_i - mean(r)) / (std(r) + 1e-4)

with std computed over the group (unbiased=False, matching core/grpo.py). The
clipped surrogate then bounds the update: with ratio = exp(new_logp -
old_logp) and clip_eps = 0.2, the objective uses min(ratio*A, clip(ratio, 0.8,
1.2)*A), so a positive-advantage member cannot be pushed past 1.2x its old
probability in one step.

This script runs that arithmetic on three reward groups, no model involved:
the all-zeros group that produced mission 01's 200/200 null, a sparse
grid-world-style group with two wins in eight, and a healthy spread. The
degenerate case is the one worth seeing first: std < 1e-6 means A is 0/0 and
the whole group contributes no gradient.

Run:
    uv run python core/group_advantage.py
"""

from __future__ import annotations

import math

EPS = 0.2


def analyze(rewards: list[float], label: str) -> None:
    g = len(rewards)
    mean = sum(rewards) / g
    variance = sum((r - mean) ** 2 for r in rewards) / g
    std = math.sqrt(variance)

    print(f"\n== {label} ==")
    print(f"  rewards: {rewards}")
    print(f"  mean={mean:.4f}  std={std:.6f}")
    if std < 1e-6:
        print("  degenerate: std < 1e-6, advantage is 0/0, group contributes no gradient")
        return

    advantages = [(r - mean) / (std + 1e-4) for r in rewards]
    print(f"  advantages: {[f'{a:+.3f}' for a in advantages]}")
    up = sum(1 for a in advantages if a > 0)
    down = sum(1 for a in advantages if a < 0)
    print(f"  members pushed up: {up}, pushed down: {down}, zero: {g - up - down}")

    ratio = 1.5
    clipped = min(ratio, 1 + EPS)
    print(f"  with ratio={ratio}, eps={EPS}: positive side capped at "
          f"{clipped:.2f}*A, negative side uses full {ratio:.2f}*A")


def main() -> None:
    analyze([0.0] * 8, "mission 01 null: every group member scores exactly 0.0")
    analyze(
        [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        "grid-world-style: two wins in eight, sparse verifier reward",
    )
    analyze(
        [0.2, 0.5, 0.8, 1.0, 0.3, 0.6, 0.4, 0.9],
        "healthy spread: format credit plus correctness variance",
    )


if __name__ == "__main__":
    main()
