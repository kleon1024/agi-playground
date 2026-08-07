"""Production capacity audit over the emitted load scan.

Stage 49's read shows the tail at three loads. The failure mode this
path exists for is capacity that is found by the wrong instrument: a
team that sizes to the mean service time (roughly 59 req/s here) is
spending its budget failing the slow queries the mean never saw. This
path reads the envelope the core script emits (`core/capacity.py
--emit-log /tmp/capacity-envelope.json`) and reads the load at which
p95 crosses the deadline, the way a capacity team reads a load test.

The check answers the case-finding question of the stage: capacity is
throughput times deadline, and the deadline crossing is the number you
plan against — not the mean-service throughput.

Requires: pandas

Run:
    python capacity_audit.py /tmp/capacity-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    frame = pd.DataFrame(envelope["loads"])  # type: ignore[arg-type]
    return frame


def render(frame: pd.DataFrame, envelope: dict[str, object]) -> None:
    deadline = float(envelope["deadline_ms"])
    mean_service = float(envelope["mean_service_ms"])
    tail_service = float(envelope["tail_service_ms"])
    mean_capacity = 1000.0 / mean_service
    print(f"capacity audit (deadline {deadline:.0f}ms, mean service "
          f"{mean_service:.0f}ms, 5% at {tail_service:.0f}ms):")
    print(f"  {'load':>4} {'util':>5}  {'p50':>5} {'p95':>5} {'p99':>5} "
          f"{'over deadline':>13}")
    for _, row in frame.iterrows():
        print(
            f"  {int(row['load']):>4} {row['utilization']:>5.0%}  "
            f"{row['p50']:.0f} {row['p95']:.0f} {row['p99']:.0f} "
            f"{row['over_deadline']:>13.1%}"
        )
    print()
    first = frame.iloc[0]
    if float(first["p95"]) > deadline:
        print("verdict: DEADLINE UNACHIEVABLE -- p95 of the service mix")
        print(f"({float(first['p95']):.0f}ms) exceeds the {deadline:.0f}ms")
        print("deadline at every load, because the 5% slow service")
        print(f"({tail_service:.0f}ms) is itself over the deadline. No")
        print("machine count satisfies a p95 deadline tighter than the")
        print("service tail; the mean capacity")
        print(f"({mean_capacity:.0f} req/s) is the divergence load, not a")
        print("serving answer. The fix is cutting the service tail -")
        print("hedge, timeout, parallel shards - before adding machines.")
        return
    crossed = frame[frame["p95"] > deadline]
    if len(crossed) == 0:
        print("verdict: HEADROOM OK -- p95 stays under the deadline across")
        print("the scanned loads; capacity is not the binding constraint.")
        return
    first = crossed.iloc[0]
    last_ok = frame[frame["p95"] <= deadline]
    ok_load = int(last_ok.iloc[-1]["load"]) if len(last_ok) else 0
    print(f"verdict: CAPACITY CROSSED -- p95 exceeds the {deadline:.0f}ms "
          f"deadline at {int(first['load'])} req/s")
    print(f"(utilization {first['utilization']:.0%}); the last load that "
          f"clears it is {ok_load} req/s.")
    print(f"The mean-service throughput is {mean_capacity:.0f} req/s - the")
    print("number the average would size against. The gap between that and")
    print(f"the {ok_load} req/s deadline crossing is the cost of the tail:")
    print("capacity is found by load-testing with a deadline, not by the")
    print("mean service time.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: capacity_audit.py <capacity-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame, envelope)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
