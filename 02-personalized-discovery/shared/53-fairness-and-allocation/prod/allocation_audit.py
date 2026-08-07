"""Production allocation audit over the emitted floor-level rows.

Stage 53's read shows the floor moving the tail from 1% to a real
share. The failure mode this path exists for is the declared floor that
does not bind: a fairness constraint stated as "10% per category" is not
the same as the exposure the protected group actually receives, because
renormalising after flooring the other categories re-dilutes the group
the floor was meant to protect. This path reads the envelope the core
script emits (`core/allocation.py --emit-log /tmp/allocation-envelope.json`)
and compares each floor level's declared floor against the protected
group's measured exposure, the way a marketplace or fairness team reads
allocation telemetry.

The check answers the case-finding question of the stage: before you
declare the allocation fair, measure the protected group's exposure, not
the floor you configured.

Requires: pandas

Run:
    python allocation_audit.py /tmp/allocation-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = envelope["floors"]  # type: ignore[arg-type]
    protected = str(envelope["protected"])
    frame = pd.DataFrame(rows)
    frame["group_exposure"] = frame[protected]
    frame["gap"] = frame["floor"] - frame["group_exposure"]
    return frame


def render(frame: pd.DataFrame) -> None:
    print("allocation audit (protected-group exposure per floor level):")
    print(f"  {'floor':>6} {'group exposure':>15} {'gap':>8} "
          f"{'aggregate ctr':>14}")
    for _, row in frame.iterrows():
        print(
            f"  {row['floor']:>6.0%} {row['group_exposure']:>15.1%} "
            f"{row['gap']:>+8.1%} {row['aggregate_ctr']:>14.4f}"
        )
    print()
    worst = frame.sort_values("gap", ascending=False).iloc[0]
    if float(worst["gap"]) <= 0.001:
        print("verdict: FLOOR BINDS -- the protected group's exposure")
        print("meets the declared floor at every level; the allocation is")
        print("holding as configured.")
        return
    print(f"verdict: GROUP GAP -- at a {worst['floor']:.0%} declared floor,")
    print(f"the protected group receives {worst['group_exposure']:.1%} of")
    print(f"exposure, a {worst['gap']:.1%} shortfall. Renormalising after")
    print("flooring the other categories re-dilutes the group the floor")
    print("was meant to protect, so the configured constraint is not the")
    print("served allocation. Measure per-group exposure, not the declared")
    print("floor, and fix the allocation by solving the constrained")
    print("problem with the floor as a binding constraint, not by")
    print("max-then-renormalise.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: allocation_audit.py <allocation-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
