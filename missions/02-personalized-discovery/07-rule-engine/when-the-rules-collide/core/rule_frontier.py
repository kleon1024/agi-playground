"""The rule engine's frontier: which region x cap combos empty the set.

Stage 07's demo shows one empty-set case (region=EU). The empty set is a
property of the rule x context grid, not a single request: this script
sweeps region and the per-creator cap across the stage's own DEFAULT_RULES
and items, so the boundary — where the rules stop producing candidates —
is a table. It also prints one decision's audit record, because the
"why was this shown" answer is what makes a rule engine auditable.

Everything is imported from the stage's core.

Run:
    uv run python core/rule_frontier.py
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from rule_engine import DEFAULT_RULES, apply_rules, build_items, detect_empty_set


def main() -> None:
    items = build_items()
    print(f"{'region':>8} {'cap':>4} {'kept':>5} {'empty':>6}")
    for region in ("US", "EU"):
        for cap in (1, 2, 3, 4):
            rules = [replace(r, param=cap) if r.rule_id == "per_creator_cap" else r for r in DEFAULT_RULES]
            decisions, _ = apply_rules(items, rules, {"region": region})
            kept = sum(1 for d in decisions if d.status == "kept")
            empty = detect_empty_set(items, rules, {"region": region}) is not None
            print(f"{region:>8} {cap:>4} {kept:>5} {empty!s:>6}")

    print("\naudit sample (region=US, cap=1) — one capped decision's record:")
    rules = [replace(r, param=1) if r.rule_id == "per_creator_cap" else r for r in DEFAULT_RULES]
    decisions, _ = apply_rules(items, rules, {"region": "US"})
    capped = next(d for d in decisions if d.status == "capped")
    print(f"  {capped.item_id}: status={capped.status}, fired={capped.fired}")
    print(f"  explanation: {capped.explanation}")


if __name__ == "__main__":
    main()
