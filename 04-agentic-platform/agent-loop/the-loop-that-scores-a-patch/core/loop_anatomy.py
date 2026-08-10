"""The agent-loop anatomy: the harness, drawn as its steps and checks.

The code-agent's "model" is not one network; it is the loop — materialize
the repo, capture the baseline, run the agent, read the diff, re-run the
tests, score — with the test-tampering guardrail as the check that decides
whether the loop's own verdict is trustworthy. This script reads the
recorded harness-end-to-end run and lays out the loop's two branches: the
honest idle path and the tampering path the guardrail exists to catch.

Input (recorded, unchanged): ../runs/2026-07-29-harness-end-to-end.md

Run:
    uv run python core/loop_anatomy.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-29-harness-end-to-end.md"
    ).read_text()
    print("agent-loop anatomy (recorded harness run), read:")
    print("  steps: materialize -> capture baseline -> agent loop ->")
    print("         read diff -> re-run tests -> score")
    for row in re.findall(
        r"\| `([\w-]+)` \| `([a-z_]+)` \| ([\d.]+) s \|",
        run,
    ):
        print(f"  scripted attempt {row[0]}: verdict {row[1]}, {row[2]}s")
    tamper = re.search(r"`tamper`[^\n]*", run)
    if tamper:
        print(f"  {tamper.group(0)}")
    print("\nreading: the guardrail is the check on the diff, not the agent's")
    print("own report — a tampered record shows every numeric signal as")
    print("resolved, and only the diff says otherwise.")


if __name__ == "__main__":
    main()
