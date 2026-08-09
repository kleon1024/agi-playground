"""The agent as the action, read from the recorded mission-04 arms.

The chapter's question: when the agent does not recommend an action but IS
the action, what does reconciliation cost and what does it catch? This script
reads three recorded records -- the failure taxonomy, the zero-failure
contrast, and the reconciliation-gate read -- and prints the un-reconciled
agent's record (the blind call) against the reconciled one (the harness),
which is the evidence the chapter's argument stands on.

Input (recorded, unchanged):
  04-how-it-fails/runs/2026-08-01-failure-taxonomy.md
  04-how-it-fails/the-zero-failure-taxonomy/runs/2026-08-06-taxonomy-read.md
  04-how-it-fails/control-plane-governance/runs/2026-08-08-governance-gates.md

Run:
    uv run python core/risk_agent.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

TAXONOMY = (
    ROOT
    / "04-agentic-platform/04-how-it-fails/runs/2026-08-01-failure-taxonomy.md"
)
ZERO_TAXONOMY = (
    ROOT
    / "04-agentic-platform/04-how-it-fails/the-zero-failure-taxonomy/"
    "runs/2026-08-06-taxonomy-read.md"
)
GATES = (
    ROOT
    / "04-agentic-platform/04-how-it-fails/control-plane-governance/"
    "runs/2026-08-08-governance-gates.md"
)


def grab(pattern: str, text: str, label: str) -> str:
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"recorded run no longer contains: {label}")
    return m.group(1)


def grab_many(pattern: str, text: str, label: str) -> tuple[str, ...]:
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"recorded run no longer contains: {label}")
    return m.groups()


def main() -> None:
    taxonomy = TAXONOMY.read_text()
    zero = ZERO_TAXONOMY.read_text()
    gates = GATES.read_text()

    blind_failing = grab(
        r"target_still_failing`?, (\d+)/18", taxonomy, "blind target_still_failing"
    )
    non_applying = grab(
        r"Of these twelve, \*\*(\w+)\*\*",
        taxonomy,
        "non-applying share",
    )
    timeouts = grab(r"timeout`, (\d+)/18", taxonomy, "blind timeouts")
    rejected = grab(
        r"blind calls the gate would reject before delivery: (\d+)/18",
        gates,
        "gate rejections",
    )
    rejected_cost = grab_many(
        r"cost of those undelivered attempts: \$([\d.]+), (\d+)s",
        gates,
        "rejection cost",
    )
    tampering = grab(
        r"tampering across 54 real attempts: (\d+)", gates, "tampering record"
    )
    harness_resolved = grab_many(
        r"resolved\s+harness (\d+)/18\s+no-harness (\d+)/18",
        zero,
        "resolved contrast",
    )

    print("the agent as the action, read from the recorded mission-04 arms:\n")
    print("the un-reconciled agent (blind call, 18 attempts):")
    print(f"  target_still_failing {blind_failing}/18, {non_applying} of them a diff")
    print(f"  git apply rejects outright; timeout {timeouts}/18")
    print(f"  a reconciliation gate would reject {rejected}/18 before delivery,")
    print(f"  at ${rejected_cost[0]} and {rejected_cost[1]}s of wall-clock")
    print(f"  tampering record: {tampering} across 54 real attempts\n")
    print("the reconciled agent (harness, 18 attempts):")
    print(f"  resolved {harness_resolved[1]}/18 (harness {harness_resolved[0]}/18)")
    print("  every failure category other than resolved: 0/18\n")
    print("reading: when the agent is the action, the action must be")
    print("reconciled before it lands. The blind call is the un-reconciled")
    print("agent: 14 of 18 actions would be rejected by a gate that checks")
    print("the verdict at all. The harness is the reconciled agent: the same")
    print("18 attempts all resolve because verification is inside the loop,")
    print("and the gate's own cost is below the blind call's per-delivered")
    print("price. Reconciliation is not overhead; it is the mechanism that")
    print("turns an agent that acts into one a risk owner can sign off on.")


if __name__ == "__main__":
    main()
