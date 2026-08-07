"""The network tail, read from the recorded ping timing.

Stage 03's realtime margin is dominated by the network, not the codec.
This script reads the recorded ping distribution and lays out the
round-trip tail.

Input (recorded, unchanged): ../runs/network_latency.json

Run:
    uv run python core/network_tail_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "network_latency.json"
    ) as fh:
        d = json.load(fh)
    r = d["roundtrip_s"]
    print("network round-trip (recorded), read:")
    print(f"  p50 {r['p50']*1000:.1f}ms  p95 {r['p95']*1000:.1f}ms  "
          f"mean {r['mean']*1000:.1f}ms  min {r['min']*1000:.1f}ms  "
          f"max {r['max']*1000:.1f}ms")
    print(f"  p95/p50 ratio: {r['p95']/r['p50']:.1f}x")
    print(f"  {d['n_pings']} pings, {d['payload_bytes_each_way']} bytes each way")
    print("\nreading: the codec and LM run in milliseconds on this lane, so the")
    print("realtime margin is the network's tail — p95 is 4.4x p50, and that")
    print("variance is what a realtime budget has to absorb.")


if __name__ == "__main__":
    main()
