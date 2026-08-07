"""User history helps, read: past intent disambiguates the query.

Stage 23 personalizes search. This script reads a disambiguation case:
the query alone is ambiguous, the history is not.

Run:
    uv run python core/history_helps.py
"""

from __future__ import annotations


def main() -> None:
    query = "apple"
    history = ["iphone battery", "iphone cases"]
    intents = {
        "fruit recipes": 0.4,
        "apple store support": 0.9,
        "apple pie recipe": 0.3,
    }
    print("history helps, read:")
    print(f"  query '{query}', history {history}")
    for intent, score in sorted(intents.items(), key=lambda kv: -kv[1]):
        print(f"  {intent}: {score:.1f}")
    print("\nreading: 'apple' alone could be fruit or phone; the phone-heavy")
    print("history lifts the support intent. History is a prior over the")
    print("query's meaning, and the prior is what personalization adds.")


if __name__ == "__main__":
    main()
