"""The reserve interacting with eCPM, read.

Stage 14's reserve floors the auction; stage 15's eCPM ranks the ads. The
two interact: a reserve above an ad's eCPM removes it from contention.
This script combines them and shows the combined decision.

Run:
    uv run python core/reserve_ecpm.py
"""

from __future__ import annotations


def ecpm(bid: float, pctr: float) -> float:
    return bid * pctr * 1000


def main() -> None:
    ads = [("Ad A", 2.00, 0.05), ("Ad B", 0.50, 0.30), ("Ad C", 1.00, 0.12)]
    print("reserve x eCPM interaction, read:")
    for reserve in (0.0, 100.0, 125.0, 160.0):
        eligible = [(n, b, p, ecpm(b, p)) for n, b, p in ads if ecpm(b, p) >= reserve]
        print(f"  reserve {reserve:.0f}: eligible " +
              (", ".join(f"{n} ({e:.0f})" for n, _, _, e in eligible) or "none"))
    print("\nreading: the reserve filters the eCPM ranking — at reserve 125")
    print("only Ad B (150) clears it; at 160 nothing does. The reserve and")
    print("the ranking are one decision: what the platform refuses to show,")
    print("and in what order.")


if __name__ == "__main__":
    main()
