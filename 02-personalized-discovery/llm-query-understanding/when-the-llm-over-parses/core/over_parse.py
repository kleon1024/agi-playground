"""Over-parsing, read: the slot the query never stated.

Stage 37 parses queries with an LLM. This script reads the failure
where the parser invents a slot value the query did not contain.

Run:
    uv run python core/over_parse.py
"""

from __future__ import annotations


def main() -> None:
    parsed = [
        ("flights to tokyo", {"dest": "tokyo", "max_price": "cheap"}),
        ("flights to tokyo", {"dest": "tokyo", "max_price": None}),
    ]
    print("over-parse, read:")
    print("  query: 'flights to tokyo'")
    print(f"  over-parsed: {parsed[0][1]}  (max_price invented)")
    print(f"  honest:      {parsed[1][1]}  (max_price absent)")
    print("\nreading: the over-parsed version invents 'cheap' and would")
    print("filter the index by a constraint the user never stated. LLM")
    print("parsing needs a confidence floor per slot — an invented slot")
    print("silently shrinks recall exactly like an over-eager rule.")


if __name__ == "__main__":
    main()
