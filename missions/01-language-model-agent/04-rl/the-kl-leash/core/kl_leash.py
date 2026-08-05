"""The KL leash, as arithmetic on the new-vs-reference divergence.

GRPO's objective couples two terms per token: the clipped surrogate (which
pushes toward higher-reward completions) and a KL toll against the frozen
reference policy (which keeps the update close to the model it started
from). The leash uses Schulman's k3 estimator — `kl = exp(-d) + d - 1` with
d = new_logp - ref_logp — for two reasons this script measures: it is always
non-negative (the naive `d` itself can go negative and add noisy
sign-flipping gradient), and it is asymmetric (reducing probability mass
relative to the reference costs more than increasing it).

Run:
    uv run python core/kl_leash.py
"""

from __future__ import annotations

import math

KL_BETA = 0.04  # the repo's default


def main() -> None:
    print(f"k3: kl = exp(-d) - (-d) - 1, d = new_logp - ref_logp, beta = {KL_BETA}")
    print(f"{'new/ref':>8} {'d':>8} {'naive d':>9} {'k3 kl':>8} {'toll':>8}")
    for r in (0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 5.0):
        d = math.log(r)
        naive = d
        k3 = math.exp(-d) + d - 1
        print(f"{r:>8.1f} {d:>+8.3f} {naive:>+9.3f} {k3:>8.4f} {KL_BETA * k3:>8.4f}")
    print("\nreading: k3 is always >= 0 — reducing probability mass (new/ref < 1)")
    print("costs more than increasing it (new/ref > 1); the naive d goes negative,")
    print("which is the sign-flipping gradient the k3 estimator exists to remove.")


if __name__ == "__main__":
    main()
