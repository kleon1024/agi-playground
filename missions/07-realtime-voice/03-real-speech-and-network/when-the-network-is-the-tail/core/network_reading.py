"""The real network, read: the round trip against the decode budget.

Stage 03 measured a real Tailscale round trip (Mac -> DERP-relayed ->
remote host, 200 pings) alongside the KV-cache correctness on real-speech
tokens. This script reads the recorded round-trip JSON and lays it beside
the decode budget (the cached path's ~1.5ms/token from stage 01), so the
realtime contract's two terms — decode and network — are one table.

Input (recorded, unchanged): ../runs/network_latency.json

Run:
    uv run python core/network_reading.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(Path(__file__).resolve().parents[2] / "runs" / "network_latency.json") as fh:
        d = json.load(fh)
    rt = d["roundtrip_s"]
    print(f"real Tailscale round trip ({d['n_pings']} pings, {d['payload_bytes_each_way']}B each way):")
    print(f"  p50 {rt['p50']*1000:.2f}ms | p95 {rt['p95']*1000:.2f}ms | "
          f"mean {rt['mean']*1000:.2f}ms | max {rt['max']*1000:.2f}ms")
    print("\nvs the decode budget (cached path, ~1.5ms/token from stage 01):")
    print("  a 48-token completion decodes in ~72ms; the network p50 adds")
    print("  ~10ms, but the p95 (42ms) and max (85ms) round trips are a")
    print("  significant fraction of the budget — the tail is where the")
    print("  realtime contract lives.")


if __name__ == "__main__":
    main()
