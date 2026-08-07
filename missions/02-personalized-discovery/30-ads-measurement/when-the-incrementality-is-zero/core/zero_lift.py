"""Zero incrementality, read: the ad moved nothing.

Stage 30 measures incrementality. This script reads the honest verdict
when the exposed and control groups convert identically.

Run:
    uv run python core/zero_lift.py
"""

from __future__ import annotations


def main() -> None:
    exposed = 0.030
    control = 0.030
    lift = (exposed - control) / control
    print("zero incrementality, read:")
    print(f"  exposed {exposed:.3f} vs control {control:.3f}")
    print(f"  lift {lift:+.1%}")
    print("\nreading: the campaign delivered millions of impressions and")
    print("changed nothing — every click it got would have happened without")
    print("it. Zero lift is the null result measurement exists to find; a")
    print("report that hides it is crediting spend with no effect.")


if __name__ == "__main__":
    main()
