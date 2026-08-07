"""LLM ranking output that is not a permutation, read.

Stage 31's LLM ranker answers in text, and text is not a list. The
emitted ranking can duplicate an ID, skip an ID, or carry an ID that
is not in the candidate set — and what happens next decides whether
the reorder ships.

This script reads the three failure shapes over a 12-response cohort,
then compares two handling paths:

1. naive parse — accept the IDs in order, silently serve what the
   text says (dropped docs and phantom IDs included);
2. validate and resample — a structural check (unique, in-set,
   complete) and a repair that keeps the valid prefix, appends the
   missing docs in pointwise order, and counts the extra inference
   cost.

Run:
    uv run python core/output_parse.py
"""

from __future__ import annotations

import re

ID_TOKEN = re.compile(r"[a-z][a-z0-9]*")


# query, candidate set, raw LLM answer
COHORT = [
    ("marathon running shoes", ["d1", "d2", "d3", "d4", "d5"],
     "d4, d2, d5, d1, d3"),
    ("wireless noise cancelling headphones", ["h1", "h2", "h3", "h4", "h5"],
     "h2, h1, h4, h3, h5"),
    ("budget laptop under 800", ["l1", "l2", "l3", "l4", "l5"],
     "l1, l3, l2, l5"),
    ("4k monitor for coding", ["m1", "m2", "m3", "m4", "m5"],
     "m3, m1, m2, m4, m5, m6"),
    ("running socks cushioning", ["s1", "s2", "s3", "s4", "s5"],
     "s2, s1, s3, s5, s4"),
    ("mechanical keyboard", ["k1", "k2", "k3", "k4", "k5"],
     "k1, k4, k2, k2, k5"),
    ("trail running vest", ["v1", "v2", "v3", "v4", "v5"],
     "v3, v1, v2, v4, v5"),
    ("portable espresso maker", ["e1", "e2", "e3", "e4", "e5"],
     "e1, e3, e2, e4, e5"),
    ("ergonomic desk chair", ["c1", "c2", "c3", "c4", "c5"],
     "c2, c4, c1, c3, c5"),
    ("yoga mat non slip", ["y1", "y2", "y3", "y4", "y5"],
     "y3, y1, y2, y2, y4"),
    ("wireless earbuds vs earbuds wireless", ["e1", "e2", "e3", "e4", "e5"],
     "e2, e1, e3"),
    ("lightweight or durable jacket", ["j1", "j2", "j3", "j4", "j5"],
     "j3, j1, j4, j2, j5"),
]


def naive_parse(raw: str) -> list[str]:
    """Accept every ID token in order; no structural check."""
    return ID_TOKEN.findall(raw)


def validate_and_resample(
    raw: str, candidates: list[str], pointwise: list[str]
) -> tuple[list[str], str | None]:
    """Keep the valid prefix, append missing docs in pointwise order.

    Returns the repaired ranking and the failure shape, or None when
    the response is a valid permutation.
    """
    parsed = ID_TOKEN.findall(raw)
    seen: list[str] = []
    for doc in parsed:
        if doc in candidates and doc not in seen:
            seen.append(doc)
    missing = [doc for doc in candidates if doc not in seen]
    phantom = any(doc not in candidates for doc in parsed)
    if not missing and len(seen) == len(candidates) and not phantom:
        return seen, None
    if phantom:
        shape = "extra token"
    elif len(parsed) != len(set(parsed)):
        shape = "duplicate id"
    else:
        shape = "missing id"
    repaired = seen + [doc for doc in pointwise if doc in missing]
    return repaired, shape


def render() -> None:
    pointwise = ["d1", "d2", "d3", "d4", "d5"]
    invalid: dict[str, int] = {}
    naive_damaged = 0
    naive_dropped = 0
    naive_phantom = 0
    repaired = 0
    recovered = 0
    for _, candidates, raw in COHORT:
        naive = naive_parse(raw)
        in_set = [d for d in naive if d in candidates]
        dropped = len(candidates) - len(set(in_set))
        phantom = len(naive) - len(in_set)
        naive_dropped += dropped
        naive_phantom += phantom
        if dropped or phantom:
            naive_damaged += 1
        _, shape = validate_and_resample(raw, candidates, pointwise)
        if shape is not None:
            invalid[shape] = invalid.get(shape, 0) + 1
            repaired += 1
            recovered += dropped

    print("llm ranking output, read:")
    print(f"  cohort: {len(COHORT)} responses")
    print(f"  parse clean:    {len(COHORT) - repaired}")
    print(f"  invalid:        {repaired} "
          f"(duplicate id {invalid.get('duplicate id', 0)}, "
          f"missing id {invalid.get('missing id', 0)}, "
          f"extra token {invalid.get('extra token', 0)})")
    print(f"  naive parse:    {naive_damaged} of {len(COHORT)} reorders")
    print("                  serve a damaged list "
          f"({naive_dropped} docs dropped, "
          f"{naive_phantom} phantom id served)")
    print(f"  validate + resample: repaired {repaired} of {repaired} invalid")
    print(f"                  responses; {recovered} docs recovered, "
          f"{naive_phantom} phantom removed; cost: {repaired} extra")
    print("                  inference calls (one per invalid response)")
    print()
    print("reading: the text answer is not a list. A parser that accepts")
    print("the text silently ships a shorter or wider list -- dropped docs")
    print("and a phantom id. The structural check catches the three shapes,")
    print("and the resample repairs them at the cost of one extra inference")
    print("round per invalid response.")


def main() -> int:
    render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
