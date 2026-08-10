"""When the slot is scarce, read: displacement grows as the slate shrinks.

Stage 18's displacement depends on how many slots there are: with more
slots, an ad displaces less; with fewer, each ad costs more organic
value. This script sweeps the slate length and shows the displacement
curve.

Run:
    uv run python core/scarcity_read.py
"""

from __future__ import annotations


def main() -> None:
    organic = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
    print("displacement vs slate length, read:")
    print(f"  {'slots':>5} {'1 ad displaces':>15} {'share of slate':>14}")
    for n_slots in (4, 6, 8):
        last = organic[:n_slots][-1]
        print(f"  {n_slots:>5} {last:>15.2f} {last/sum(organic[:n_slots]):>13.1%}")
    print("\nreading: the same ad displaces 0.60 of value in a 4-slot slate")
    print("but only 0.20 in an 8-slot one — scarcity amplifies the")
    print("externality. Slot count is part of the ad decision, not a fixed")
    print("constant, which is why the value tree prices displacement per")
    print("slate, not per ad.")


if __name__ == "__main__":
    main()
