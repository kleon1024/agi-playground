"""Trust erodes, read: a false explanation is a lie the user can
check.

Stage 52 detour: explanations are cheap to generate and expensive to
get wrong. When the platform says 'because you viewed' on an item the
user never viewed, the user has evidence against the claim - and
opt-outs rise with the share of false explanations.

Run:
    uv run python core/trust_erodes.py
"""

from __future__ import annotations

# (false explanation share, opt-out rate)
ROWS = [
    (0.00, 0.010),
    (0.05, 0.018),
    (0.20, 0.052),
    (0.50, 0.130),
]


def main() -> None:
    print("trust erodes, read (opt-out rate vs false explanation share):")
    for share, opt_out in ROWS:
        print(f"  false explanations {share:.0%}: opt-out rate {opt_out:.1%}")
    print("\nreading: even a 5% false rate nearly doubles opt-outs;")
    print("at 20% a twentieth of users leave. The explanation feature")
    print("was meant to build trust, and a wrong one burns it faster")
    print("than a missing one - the user can check 'because you")
    print("viewed' against their own history, and the check fails.")


if __name__ == "__main__":
    main()
