"""The click that is a query, read: sessions reveal the follow-up.

Stage 24 measures search from logs. This script reads a session: the
first query fails, the user reformulates, and the second query is the
real intent.

Run:
    uv run python core/query_sessions.py
"""

from __future__ import annotations


def main() -> None:
    session = [
        ("heaphones", "no click"),
        ("headphones", "click on d2"),
    ]
    print("session, read:")
    for query, outcome in session:
        print(f"  '{query}' -> {outcome}")
    print("\nreading: judged alone, the first query is a failure. Judged as")
    print("a session, it is the intent that the second query satisfied. The")
    print("reformulation is the correction signal — session metrics catch")
    print("the recovery that per-query metrics call a miss.")


if __name__ == "__main__":
    main()
