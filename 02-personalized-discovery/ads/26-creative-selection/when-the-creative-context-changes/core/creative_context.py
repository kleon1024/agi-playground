"""Creative context changes, read: the winning look is placement-specific.

Stage 26 selects creatives by context. This script reads the same
creative scoring differently across two placements.

Run:
    uv run python core/creative_context.py
"""

from __future__ import annotations


def main() -> None:
    # (creative, ctr in feed, ctr on search results)
    creatives = [
        ("rich card", 0.08, 0.02),
        ("compact", 0.03, 0.06),
    ]
    print("creative context, read:")
    for name, feed, search in creatives:
        print(f"  {name}: feed {feed:.2f}, search {search:.2f}")
    print("\nreading: the rich card wins in the feed where users browse;")
    print("the compact creative wins on search where users scan. A single")
    print("global creative rank would pick the rich card everywhere and")
    print("leave search clicks on the table — context is a feature of the")
    print("selection model, not a label on top of it.")


if __name__ == "__main__":
    main()
