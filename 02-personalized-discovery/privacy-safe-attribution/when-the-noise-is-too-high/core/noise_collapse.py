"""Noise collapse, read: epsilon too small erases the decision.

Stage 40 adds DP noise to attribution. This script reads the collapse
point where the noise reorders the channel ranking the budget follows.

Run:
    uv run python core/noise_collapse.py
"""
def main() -> None:
    true = {"search": 480, "display": 310, "email": 260}
    true_rank = [k for k, _ in sorted(true.items(), key=lambda x: -x[1])]
    # One fixed draw per epsilon so the collapse point is reproducible:
    # the same unlucky sample that leaves the order intact at 5.0 breaks it
    # at 0.5, where the noise scale is four times larger.
    draws = {
        5.0: {"search": 5, "display": -2, "email": 3},
        2.0: {"search": -10, "display": 20, "email": 5},
        0.5: {"search": -30, "display": -80, "email": 90},
    }
    print("noise collapse, read:")
    for epsilon in (5.0, 2.0, 0.5):
        noisy = {k: v + draws[epsilon][k] for k, v in true.items()}
        rank = [k for k, _ in sorted(noisy.items(), key=lambda x: -x[1])]
        preserved = rank == true_rank
        print(f"  epsilon {epsilon}: noisy {list(noisy.values())}, rank {rank}, order preserved {preserved}")
    print("\nreading: at epsilon 5 the order survives; at 0.5 it collapses.")
    print("The privacy guarantee and the decision accuracy are the same")
    print("dial — epsilon is chosen so the noisiest plausible draw still")
    print("keeps the budget decision intact.")


if __name__ == "__main__":
    main()
