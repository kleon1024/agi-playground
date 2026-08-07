"""Incrementality, read: the ad's clicks minus what would have happened.

Stage 30 measures whether ads cause outcomes. This script reads a simple
incrementality split: exposed versus control groups.

Run:
    uv run python core/incrementality.py
"""

from __future__ import annotations


def main() -> None:
    # Conversion rate in exposed vs control (holdout) groups.
    exposed_cvr = 0.032
    control_cvr = 0.028
    lift = (exposed_cvr - control_cvr) / control_cvr
    print("incrementality, read:")
    print(f"  exposed: {exposed_cvr:.3f} conversion rate")
    print(f"  control: {control_cvr:.3f}")
    print(f"  lift:    {lift:.1%}")
    print("\nreading: the ad's raw clicks overstate its effect — 0.028 of")
    print("the exposed users would have converted anyway. The increment is")
    print("0.4 points, the part the ad actually caused. Attribution that")
    print("ignores the control group credits the ad with the baseline.")


if __name__ == "__main__":
    main()
