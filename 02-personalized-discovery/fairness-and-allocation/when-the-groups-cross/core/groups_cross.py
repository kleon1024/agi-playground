"""Groups cross, read: the fairness verdict flips with the definition.

Stage 53 detour: the same served allocation can look fair or unfair
depending on how the protected group is defined. Across the whole
catalogue the tail category clears its 10% exposure floor; split the
same allocation by segment and the majority segment leaves the tail at
8%, below the floor. Neither number is wrong - they answer different
questions - but the definition decides the verdict, so the group
definition is a policy decision, not a reporting detail.

Run:
    uv run python core/groups_cross.py
"""

from __future__ import annotations

FLOOR = 0.10

# Segment rows: traffic share and the tail category's exposure within it.
# Across the catalogue the tail clears the floor; inside mobile, the
# majority segment, it does not.
SEGMENTS = [
    {"segment": "mobile", "traffic": 0.70, "tail_exposure": 0.08},
    {"segment": "desktop", "traffic": 0.30, "tail_exposure": 0.15},
]


def render() -> None:
    aggregate = sum(s["traffic"] * s["tail_exposure"] for s in SEGMENTS)
    print("groups cross, read (tail-category exposure, 10% floor):")
    print(f"  {'definition':<18} {'tail exposure':>14} {'vs floor':>9}")
    for segment in SEGMENTS:
        print(
            f"  {segment['segment']:<18} {segment['tail_exposure']:>14.0%} "
            f"{segment['tail_exposure'] - FLOOR:>+9.0%}"
        )
    print(f"  {'catalogue-wide':<18} {aggregate:>14.1%} "
          f"{aggregate - FLOOR:>+9.1%}")
    print("\nreading: across the whole catalogue the tail clears the")
    print("floor (10.1% vs 10%), so the allocation looks fair. Split the")
    print("same allocation by segment and the mobile segment - 70% of")
    print("traffic - leaves the tail at 8%, below the floor. The verdict")
    print("flips with the definition: group choice is a policy decision,")
    print("and the fair-looking aggregate hides the majority segment that")
    print("is below the bar. Define the group before measuring fairness,")
    print("and report both views, not the one that clears the bar.")


if __name__ == "__main__":
    render()
