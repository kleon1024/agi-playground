"""Reward gaming, read: the policy that exploits the proxy.

Stage 32 optimizes toward a reward model. This script reads a policy
that maximizes the proxy reward by exploiting its blind spot instead of
improving real quality.

Run:
    uv run python core/reward_gaming.py
"""

from __future__ import annotations


def main() -> None:
    # (policy, proxy reward, true quality)
    policies = [
        ("helpful", 0.7, 0.7),
        ("verbose", 0.95, 0.45),
        ("sycophantic", 0.90, 0.35),
    ]
    print("reward gaming, read:")
    for name, proxy, true in policies:
        print(f"  {name}: proxy {proxy}, true quality {true}")
    worst = max(policies, key=lambda x: x[1] - x[2])
    print(f"  most gamed: {worst[0]} (gap {worst[1] - worst[2]:.2f})")
    print("\nreading: the verbose policy maximizes the proxy by exploiting")
    print("its preference for length, while true quality falls. The gap")
    print("between proxy and truth is reward hacking — why RLHF needs")
    print("regularization and held-out human evals, not just the reward.")


if __name__ == "__main__":
    main()
