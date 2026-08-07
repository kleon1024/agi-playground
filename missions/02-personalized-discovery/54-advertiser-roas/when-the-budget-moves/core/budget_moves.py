"""Budget moves, read: the advertiser's exit is the platform's loss.

Stage 54 detour: the advertiser spends across two channels and moves
budget toward the one with the higher ROAS. The platform's revenue
falls with the shift, and the auction cannot bid the advertiser back
once their measured return says leave.

Run:
    uv run python core/budget_moves.py
"""

from __future__ import annotations

TOTAL_BUDGET = 2000.0
PLATFORM_ROAS = 3.1
RIVAL_ROAS = 4.6


def main() -> None:
    print("budget moves, read (advertiser splits $2000 by measured roas):")
    for platform_share in (1.0, 0.75, 0.5, 0.25):
        platform_spend = TOTAL_BUDGET * platform_share
        print(f"  platform share {platform_share:.0%}: platform revenue "
              f"${platform_spend:.0f}")
    print("\nreading: the platform's revenue is the advertiser's spend,")
    print("and the advertiser allocates by measured ROAS. When the")
    print("rival channel returns 4.6x and the platform 3.1x, the share")
    print("moves and platform revenue falls by half. The auction prices")
    print("a slot; it cannot price the advertiser's overall return -")
    print("that is a product decision about relevance and placement.")


if __name__ == "__main__":
    main()
