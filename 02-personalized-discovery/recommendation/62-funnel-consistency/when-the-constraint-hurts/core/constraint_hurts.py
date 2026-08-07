"""When the constraint hurts: clamping p(order) <= p(click) is only
correct if the click estimate is calibrated; a badly miscalibrated
click probability drags the whole chain down.

Run:
    uv run python core/constraint_hurts.py
"""

from __future__ import annotations


def main() -> None:
    # true p(click)=0.4; the click model reports 0.9 (overconfident);
    # true p(order|click)=0.3. Independent order model is calibrated (0.12).
    pc_true = 0.4
    pc_bad = 0.9
    poc = 0.3
    po_ind = 0.12
    chained_bad = pc_bad * poc
    chained_good = pc_true * poc
    print("when the constraint hurts, read (chain inherits the click error):")
    print(f"  independent order model          p(order) {po_ind:.2f}  (calibrated)")
    print(f"  chained, bad click model         p(order) {chained_bad:.2f}  (2.25x too high)")
    print(f"  chained, calibrated click model  p(order) {chained_good:.2f}  (correct)")
    print()
    print("reading: the chain is only as honest as its inputs. enforcing the")
    print("funnel on top of an overconfident click head manufactures a worse")
    print("order estimate than the independent one. the ordering is a good")
    print("constraint, but it is applied after calibration, not instead of it;")
    print("the two fixes are the same fix: make each conditional honest first.")


if __name__ == "__main__":
    main()
