"""The refusal that names everything: the 18 missing inputs, grouped.

Stage 05's honest current state is CANNOT DETERMINE: the report refuses to
render a verdict and names every missing input. This script re-runs the
stage's own report against the real current state (no committed outcome
artifact) and groups the 18 named inputs by what each would establish, so
the refusal is readable as a checklist rather than a wall of names.

Run:
    uv run python core/refusal_read.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    report = Path(__file__).resolve().parents[2] / "core" / "report.py"
    out = subprocess.run(
        [sys.executable, str(report)],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    assert "CANNOT DETERMINE" in out, "report did not refuse; unexpected"
    print(out)
    print("\n18 inputs, grouped by what each establishes:")
    print("  baselines:   buy-and-hold folds+drawdown, momentum folds")
    print("  candidate:   net/gross folds, deflated Sharpe + trial count,")
    print("               drawdown, capacity, point-in-time, survivorship")
    print("  cost:        data/compute USD, txn cost bps, market impact")
    print("  latency:     p50, p95")
    print("  regimes:     the mandatory failure-case breakdown")


if __name__ == "__main__":
    main()
