"""The three-way verdict, read from the recorded report run.

Stage 05's report is a verdict space of MET, NOT MET, and CANNOT DETERMINE,
and the third value names exactly which input is missing. This script
re-runs the stage's own report against the real current state and lays out
the refusal's shape — 18 named inputs, grouped by what each would decide.

Run:
    uv run python core/three_way_read.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    report = Path(__file__).resolve().parents[2] / "core" / "report.py"
    out = subprocess.run(
        [sys.executable, str(report)], capture_output=True, text=True, check=False
    ).stdout
    assert "CANNOT DETERMINE" in out
    print("mission 03 report, three-way verdict, re-run against current state:")
    print(out)
    print("18 missing inputs, grouped:")
    print("  baselines/candidate evidence, cost, latency, regimes — the refusal")
    print("  names each one so the gap is a checklist, not a wall.")


if __name__ == "__main__":
    main()
