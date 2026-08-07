"""Frequency capping, read: exposure count decides the ad's value.

Stage 25 caps how often an ad can show to one user. This script reads
the click curve over exposures and where the cap should sit.

Run:
    uv run python core/frequency_cap.py
"""

from __future__ import annotations


def main() -> None:
    # CTR by exposure number for one user.
    ctrs = [0.05, 0.04, 0.03, 0.02, 0.01, 0.005, 0.002]
    print("frequency cap, read (CTR by exposure count):")
    for i, ctr in enumerate(ctrs, 1):
        print(f"  exposure {i}: ctr {ctr:.3f}")
    print("\nreading: CTR decays from 0.05 to 0.002 across seven exposures.")
    print("A cap at 3 keeps the high-value exposures; uncapped, the ad")
    print("keeps burning impressions at near-zero click value and annoys")
    print("the user. The cap is a value decision, not a rule of thumb.")


if __name__ == "__main__":
    main()
