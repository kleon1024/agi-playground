"""When the ad is relevant, read: displacement is not always a loss.

Stage 18 shows ads displacing organic value. The subtlety: a highly
relevant ad may be *worth more* to the user than the organic item it
displaces — the externality is negative only when the ad is worse than
what it pushes out. This script quantifies the sign flip.

Run:
    uv run python core/relevant_ad.py
"""

from __future__ import annotations


def main() -> None:
    # The displaced organic item's value, and the ad's value to the user.
    displaced = 0.7
    print("relevant vs irrelevant ad, read (displaced organic value 0.7):")
    for ad_user_value in (0.2, 0.7, 1.4):
        net = ad_user_value - displaced
        label = "net loss" if net < 0 else ("neutral" if net == 0 else "net gain")
        print(f"  ad user value {ad_user_value:.1f} -> net {net:+.1f} ({label})")
    print("\nreading: an irrelevant ad (0.2) displacing a 0.7 organic item")
    print("is a 0.5 loss; a relevant ad (1.4) is a 0.7 gain. The externality")
    print("is not 'ads are bad' — it is the difference between the ad's")
    print("user value and the organic value it replaced, which is why the")
    print("value tree prices the combination rather than banning ads.")


if __name__ == "__main__":
    main()
