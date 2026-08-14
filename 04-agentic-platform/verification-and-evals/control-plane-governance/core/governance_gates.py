"""What a governed agent would have caught, read from recorded mission-04 runs.

The chapter's question: which gates stop the failures that actually happen?
This script reads the recorded arms and prints three measured facts: (1) how
many blind calls a reconciliation-style verification gate would have rejected
before delivery, and what those undelivered attempts cost; (2) the tampering
and regression record across all 42 real attempts; (3) the cost of the gate
itself, read as the harness's per-delivered cost versus the blind call's.

Input (recorded, unchanged):
  01-no-harness/runs/no-harness-results.jsonl
  03-cheap-or-expensive/runs/2026-07-29-results.jsonl
  00-task-set/runs/public-haiku-3runs.jsonl
  06-closing-the-loop/runs/closing-the-loop-results.jsonl

Run:
    uv run python core/governance_gates.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(rel: str) -> list[dict]:
    path = ROOT / rel
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


FILES = [
    "04-agentic-platform/no-harness/runs/no-harness-results.jsonl",
    "04-agentic-platform/cheap-or-expensive/runs/2026-07-29-results.jsonl",
    "04-agentic-platform/task-set/runs/public-haiku-3runs.jsonl",
    "04-agentic-platform/closing-the-loop/runs/closing-the-loop-results.jsonl",
]


def main() -> None:
    all_rows = [r for rel in FILES for r in load(rel)]
    nh = load(FILES[0])
    harness = load(FILES[1])

    n = len(all_rows)
    tampered = sum(1 for r in all_rows if r.get("tampered"))
    regressed = sum(1 for r in all_rows if r.get("regressions"))

    gate_catch = [r for r in nh if not r["resolved"]]
    catch_cost = sum(r["cost_usd"] for r in gate_catch)
    catch_wall = sum(r["wall_clock_s"] for r in gate_catch)

    nh_cost = sum(r["cost_usd"] for r in nh)
    nh_delivered = sum(1 for r in nh if r["resolved"])
    h_cost = sum(r["cost_usd"] for r in harness)
    h_delivered = sum(1 for r in harness if r["resolved"])

    print("reconciliation gate, read from the recorded runs:\n")
    print(f"blind calls the gate would reject before delivery: "
          f"{len(gate_catch)}/18")
    print(f"cost of those undelivered attempts: ${catch_cost:.3f}, "
          f"{catch_wall:.0f}s wall-clock")
    print(f"tampering across {n} real attempts: {tampered}")
    print(f"regressions across {n} real attempts: {regressed}")
    print("\ngate cost, read as the verification the harness already runs:")
    print(f"  blind call: ${nh_cost:.3f} total, "
          f"${nh_cost/nh_delivered:.4f}/delivered ({nh_delivered}/18)")
    print(f"  harness:    ${h_cost:.3f} total, "
          f"${h_cost/h_delivered:.4f}/delivered ({h_delivered}/18)")
    print("\nreading: the gate is the scored verification step, and it is")
    print("cheap relative to what it catches -- the blind call's own failures")
    print(f"cost ${catch_cost:.3f} before the gate would have rejected them.")


if __name__ == "__main__":
    main()
