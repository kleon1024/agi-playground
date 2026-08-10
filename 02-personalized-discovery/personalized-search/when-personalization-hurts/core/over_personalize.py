"""Over-personalization, read: the echo chamber in a search box.

Stage 23 personalizes results. This script reads the downside: history
that narrows a query the user wants broad.

Run:
    uv run python core/over_personalize.py
"""

from __future__ import annotations


def main() -> None:
    query = "shoes"
    history = ["running shoes reviews", "trail running"]
    broad = ["running shoes", "dress shoes", "hiking boots", "slippers"]
    narrow = ["trail runners", "running shoes", "trail shoes", "trail boots"]
    print("over-personalization, read:")
    print(f"  history:                   {history}")
    print(f"  broad result for '{query}': {broad}")
    print(f"  personalized:              {narrow}")
    print("\nreading: the history pushes the result set toward trail running,")
    print("shrinking coverage from four categories to one. When the user's")
    print("intent is broader than their history, personalization hides")
    print("relevant results — the query's own signal has to win sometimes.")


if __name__ == "__main__":
    main()
