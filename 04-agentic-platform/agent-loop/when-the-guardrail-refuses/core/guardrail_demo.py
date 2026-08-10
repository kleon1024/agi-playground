"""The test-file guardrail's decision boundary, demonstrated on worktrees.

Stage 02's scorer refuses a patch that touches a test file, because a
tampered patch's remaining evidence is worthless. The guardrail reads the
worktree (`git status --porcelain`, which also sees untracked files — the
way a new test file would otherwise slip through). This script builds five
miniature git worktrees with the scenario's files, runs the guardrail's own
`changed_paths` and `is_test_path`, and shows which scenarios are refused,
so the boundary is the code's decision, not a prose claim.

Everything is imported from the stage's core.

Run:
    uv run python core/guardrail_demo.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from scoring import changed_paths, is_test_path

SCENARIOS = {
    "agent edited a test file (tamper)": ["tests/test_parser.py"],
    "agent edited a source file (legit)": ["parser.py"],
    "agent created a new test file": ["tests/test_noop.py"],
    "agent created a new source file": ["parser2.py"],
    "agent did not touch anything": [],
}


def main() -> None:
    print(f"{'scenario':<42} {'test paths found':>18} {'refused':>8}")
    for label, files in SCENARIOS.items():
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=work, check=True)
            for f in files:
                path = work / f
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("placeholder\n")
            paths = changed_paths(work)
            test_hits = [p for p in paths if is_test_path(p)]
            refused = "yes" if test_hits else "no"
            print(f"{label:<42} {test_hits!s:>18} {refused:>8}")
    print("\nreading: any test path in the diff refuses the patch — the")
    print("guardrail checks the diff, not the model's intent.")


if __name__ == "__main__":
    main()
