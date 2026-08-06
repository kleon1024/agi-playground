"""When pCTR moves the rank, read on the stage's ads.

ECPM ranking turns on the pCTR estimate: a small change in click
probability can flip which ad wins. This script sweeps one ad's pCTR
against the others and shows the rank flip.

Run:
    uv run python core/pctr_read.py
"""

from __future__ import annotations


def ecpm(bid: float, pctr: float) -> float:
    return bid * pctr * 1000


def main() -> None:
    ad_a = (2.00, 0.05)
    ad_b = (0.50, 0.30)
    print("pCTR sweep on Ad A (bid 2.00), read:")
    print(f"  {'Ad A pCTR':>9} {'Ad A eCPM':>9} {'Ad B eCPM':>9} {'winner':>6}")
    for pctr in (0.03, 0.05, 0.07, 0.09, 0.11):
        a = ecpm(*ad_a[:1], pctr) if False else ecpm(ad_a[0], pctr)
        b = ecpm(*ad_b)
        winner = "A" if a > b else "B"
        print(f"  {pctr:>9.2f} {a:>9.2f} {b:>9.2f} {winner:>6}")
    print("\nreading: Ad B (eCPM 150) wins while Ad A's pCTR is below 0.075;")
    print("above it Ad A's high bid takes over. The ranking is a knife-edge")
    print("on the click estimate — which is why calibration (stage 16) is")
    print("the precondition, not a polish step.")


if __name__ == "__main__":
    main()
