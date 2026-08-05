"""The no-harness failure surface, measured from this mission's own records.

Stage 04's recorded taxonomy read both result logs once and printed the
category table. This script reads the same two logs and makes a second,
complementary cut: not *what category* each attempt fell into, but *what the
failure cost* — how many blind calls produced a patch that could not even be
applied, how much time and money the failures spent, which model resolved
what, and which target tests the failures left failing. The harness arm is
the control: the same table against its 18 attempts.

Inputs (recorded, unchanged):
- ../../01-no-harness/runs/no-harness-results.jsonl
- ../../03-cheap-or-expensive/runs/2026-07-29-results.jsonl

Run:
    uv run python core/no_harness_failures.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def load(path: Path) -> list[dict]:
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def summarize(name: str, rows: list[dict]) -> None:
    n = len(rows)
    verdicts = Counter(r.get("verdict") for r in rows)
    applied = sum(1 for r in rows if r.get("patch_applied"))
    resolved = sum(1 for r in rows if r.get("resolved"))
    by_model = Counter(r.get("model") for r in rows)
    resolved_by_model = Counter(r.get("model") for r in rows if r.get("resolved"))
    costs = [r.get("cost_usd", 0.0) for r in rows]
    times = [r.get("wall_clock_s", 0.0) for r in rows]
    failing_tests: Counter[str] = Counter()
    for r in rows:
        for t in r.get("target_failing_after", []) or []:
            failing_tests[t] += 1

    print(f"\n== {name} ({n} attempts) ==")
    print(f"  verdicts: {dict(verdicts)}")
    print(f"  patch applied: {applied}/{n}; resolved: {resolved}/{n}")
    print(f"  by model: {dict(by_model)}; resolved by model: {dict(resolved_by_model)}")
    if costs:
        print(f"  cost: total ${sum(costs):.3f}, mean ${sum(costs)/n:.4f}")
        print(f"  wall-clock: total {sum(times):.0f}s, mean {sum(times)/n:.0f}s")
    if failing_tests:
        top = failing_tests.most_common(4)
        print(f"  most-repeated failing target: {top}")


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    no_harness = load(root / "01-no-harness" / "runs" / "no-harness-results.jsonl")
    harness = load(root / "03-cheap-or-expensive" / "runs" / "2026-07-29-results.jsonl")
    print(f"no-harness rows: {len(no_harness)}, harness rows: {len(harness)}")
    summarize("no-harness (stage 01: one blind call)", no_harness)
    summarize("harness (stage 03: full tool loop)", harness)


if __name__ == "__main__":
    main()
