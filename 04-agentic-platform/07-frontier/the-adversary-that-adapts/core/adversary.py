"""The adversary that adapts, read from the recorded mission-04 runs.

The chapter's question: a risk-control agent is a standing adversary
relationship, not a one-time deployment -- malicious agents adapt to
mitigations. What does that stance change about a guardrail's evidence? This
script reads three recorded records -- the test-file guardrail demo, the
failure taxonomy's tampering rows, and the reconciliation-gate read -- and
prints the guardrail's decision boundary and the honest reading of a record
in which it never fired.

Input (recorded, unchanged):
  02-agent-loop/when-the-guardrail-refuses/runs/2026-08-06-guardrail-demo.md
  04-how-it-fails/runs/2026-08-01-failure-taxonomy.md
  07-frontier/control-plane-governance/runs/2026-08-08-governance-gates.md

Run:
    uv run python core/adversary.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

GUARDRAIL = (
    ROOT
    / "04-agentic-platform/02-agent-loop/when-the-guardrail-refuses/"
    "runs/2026-08-06-guardrail-demo.md"
)
TAXONOMY = (
    ROOT
    / "04-agentic-platform/04-how-it-fails/runs/2026-08-01-failure-taxonomy.md"
)
GATES = (
    ROOT
    / "04-agentic-platform/07-frontier/control-plane-governance/"
    "runs/2026-08-08-governance-gates.md"
)


def grab(pattern: str, text: str, label: str) -> str:
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"recorded run no longer contains: {label}")
    return m.group(1)


def main() -> None:
    guardrail = GUARDRAIL.read_text()
    taxonomy = TAXONOMY.read_text()
    gates = GATES.read_text()

    rows = []
    for m in re.finditer(
        r"^([\w ().-]+?)\s{2,}(\[\S+\]|\[.*?\]|\S+)\s{2,}(yes|no)$",
        guardrail,
        re.MULTILINE,
    ):
        rows.append((m.group(1).strip(), m.group(3)))

    tampered_blind = grab(
        r"`tampered`, (\d+)/18, in both arms", taxonomy, "tampered record"
    )
    tampering_total = grab(
        r"tampering across 54 real attempts: (\d+)", gates, "tampering total"
    )

    print("the adversary that adapts, read from the recorded mission-04 runs:\n")
    print("the test-file guardrail's decision boundary (scripted worktrees):")
    for label, refused in rows:
        print(f"  {label:<46}{refused}")
    print(f"\ntampering record on real attempts: {tampered_blind}/18 in both arms,")
    print(f"and {tampering_total} across all 54 real model calls\n")
    print("reading: the guardrail has never fired on a real attempt -- reported")
    print("honestly as a fact about these two tasks, not as proof the adversary")
    print("is gone. The demo is where the mechanism was shown firing at all.")
    print("A risk-control stance assumes the model wants the cheapest path to")
    print("a green score and keeps the guardrail as a rule that no retrain can")
    print("soften; 'never fired' is then a recorded fact, not a license to")
    print("delete the gate.")


if __name__ == "__main__":
    main()
