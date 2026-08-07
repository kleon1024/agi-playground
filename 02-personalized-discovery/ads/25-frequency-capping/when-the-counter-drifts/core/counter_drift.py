"""The counter-drift detour: the cap reads a counter that lies.

Stage 25 caps by exposure count. The cap is only as good as the
counter that feeds it, and the counter is an identity object: a cookie,
an app install id, a logged-in user id. When identity fails — cookie
cleared, browser switched, second device — the counter resets to zero
and the cap starts over, so the same human is served past the useful
exposure range. This script simulates 10,000 users whose counter
resets at a random true exposure (25% once, 5% twice) and compares the
campaign the cap sees against the fatigue the user actually has.

Run:
    uv run python core/counter_drift.py
"""

from __future__ import annotations

import random

# The stage's decay curve: CTR by true exposure count (1..7).
CTR = [0.050, 0.040, 0.030, 0.020, 0.010, 0.005, 0.002]

CAP = 3
N_USERS = 10_000
RESET_ONCE = 0.25
RESET_TWICE = 0.05
DEAD_CTR = 0.005


def main() -> None:
    rng = random.Random(20260808)

    correct_impressions = 0
    correct_clicks = 0.0
    drift_impressions = 0
    drift_clicks = 0.0
    drift_dead = 0

    for _ in range(N_USERS):
        # Correct counter: exactly CAP impressions at exposures 1..CAP.
        correct_impressions += CAP
        correct_clicks += sum(CTR[:CAP])

        # Drifting counter: the user's identity object resets at a
        # random true exposure, so the cap restarts and the user is
        # served again. Reset times are drawn from the exposures the
        # cap would still serve (1..CAP).
        reset_times: set[int] = set()
        rolls = rng.random()
        if rolls < RESET_TWICE:
            reset_times = {rng.randint(1, CAP), rng.randint(1, CAP)}
        elif rolls < RESET_ONCE + RESET_TWICE:
            reset_times = {rng.randint(1, CAP)}

        counter = 0
        true_exposure = 0
        while counter < CAP:
            true_exposure += 1
            counter += 1
            if true_exposure <= len(CTR):
                drift_clicks += CTR[true_exposure - 1]
                if CTR[true_exposure - 1] <= DEAD_CTR:
                    drift_dead += 1
            drift_impressions += 1
            if true_exposure in reset_times:
                counter = 0

    print("counter-drift audit: 10,000 users, fixed seed")
    print("cap 3; 25% of users lose their counter once, 5% twice\n")
    print(f"  {'campaign':>10} {'impressions':>12} {'exp. clicks':>12} "
          f"{'clicks/imp':>10} {'dead share':>11}")
    print(f"  {'correct':>10} {correct_impressions:>12} {correct_clicks:>12.1f} "
          f"{correct_clicks / correct_impressions:>10.4f} "
          f"{sum(1 for c in CTR[:CAP] if c <= DEAD_CTR) / CAP:>11.1%}")
    print(f"  {'counter drift':>10} {drift_impressions:>12} {drift_clicks:>12.1f} "
          f"{drift_clicks / drift_impressions:>10.4f} "
          f"{drift_dead / drift_impressions:>11.1%}")
    extra = drift_impressions - correct_impressions
    print(f"\nextra impressions served: {extra}")
    print(
        f"extra expected clicks: {drift_clicks - correct_clicks:+.1f} "
        f"({(drift_clicks - correct_clicks) / correct_clicks:+.1%})"
    )

    print("\nreading: the cap reads the counter, not the human. When the")
    print("counter resets, the cap restarts and the user is served past")
    print("the useful exposure range at one-third of the click value.")
    print("The fix is identity reconciliation (device graph, login") 
    print("bridge) or a cap that treats the missing history as censored")
    print("exposure instead of zero.")


if __name__ == "__main__":
    main()
