"""The SR-MMP verdict, read: the baseline that refused to lose.

Mission 09's report compared the descriptor baseline against the trained
SMILES model on the scaffold-checked split. This script tabulates the
recorded means and spreads and reads the verdict structure: the gap (0.083)
is beyond the larger spread, so this is a decisive descriptor win, not a
near-tie.

The numbers are the recorded report's, cited and tabulated.

Run:
    uv run python core/baseline_report.py
"""

from __future__ import annotations


def main() -> None:
    print("mission 09 SR-MMP outcome report (recorded 2026-08-01)")
    print("  descriptor baseline: 0.8142 +- 0.0010")
    print("  trained model:       0.7312 +- 0.0159")
    print("  gap (descriptor - model): +0.0830 vs larger spread 0.0159")
    print("  -> model beats baseline: False")
    print("  reading: the gap is beyond either spread, so the baseline wins")
    print("  decisively — not a near-tie, and the scaffold-checked split")
    print("  means the win is not a leakage artifact.")


if __name__ == "__main__":
    main()
