"""Real network round-trip latency, to sit beside the in-process
KV-cache-vs-naive latency `streaming_decode.py` already measures.

That existing measurement is entirely local: one process, one clock, no
network in the loop. A realtime voice agent that serves inference from a
different machine than the one capturing audio pays a network round trip on
top of that per-step decode cost, and that cost is invisible to a local-only
benchmark. This script measures it directly, on this repository's own
documented Tailscale link (`reference/local-4090.md`), using a payload sized like
one streaming step's worth of audio-LM traffic: a handful of int64 token ids
each way, not a full model call -- the point is to isolate network RTT, not
to re-run inference remotely.

Deliberately stdlib-only (`socket`, no torch) so it runs unmodified against
the remote host's bare `python3`, without needing that host's project
`.venv` or its uncommitted local changes to be touched in any way.

Run:
    # on the remote host:
    python3 network_latency.py --role server --port 8765

    # on this machine:
    python3 network_latency.py --role client --host <tailscale-ip> --port 8765 \
        --n-pings 200 --payload-tokens 8
"""

from __future__ import annotations

import argparse
import json
import socket
import statistics
import time
from pathlib import Path

HEADER_BYTES = 4  # fixed-width big-endian length prefix


def _send_frame(sock: socket.socket, payload: bytes) -> None:
    sock.sendall(len(payload).to_bytes(HEADER_BYTES, "big") + payload)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("peer closed mid-frame")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_frame(sock: socket.socket) -> bytes:
    length = int.from_bytes(_recv_exact(sock, HEADER_BYTES), "big")
    return _recv_exact(sock, length)


def run_echo_server(host: str, port: int) -> None:
    """Accepts one connection, echoes every length-prefixed frame back
    unchanged, until the client disconnects. One connection is all this
    measurement needs -- no concurrency, no state, nothing to clean up beyond
    the process itself.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen(1)
        print(f"listening on {host}:{port}", flush=True)
        conn, addr = listener.accept()
        print(f"accepted connection from {addr}", flush=True)
        with conn:
            while True:
                try:
                    frame = _recv_frame(conn)
                except ConnectionError:
                    break
                _send_frame(conn, frame)
        print("client disconnected, exiting", flush=True)


def measure_roundtrip(host: str, port: int, n_pings: int, payload_bytes: int, n_warmup: int = 10) -> list[float]:
    """Opens one TCP connection (mirrors a realtime session: connect once,
    stream many small frames), sends `n_warmup` throwaway frames to let TCP
    slow-start and the Tailscale/DERP path settle, then times `n_pings` real
    round trips.
    """
    payload = bytes(payload_bytes)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        for _ in range(n_warmup):
            _send_frame(sock, payload)
            _recv_frame(sock)
        times = []
        for _ in range(n_pings):
            t0 = time.perf_counter()
            _send_frame(sock, payload)
            _recv_frame(sock)
            times.append(time.perf_counter() - t0)
    return times


def percentiles(values: list[float]) -> dict[str, float]:
    s = sorted(values)
    return {
        "p50": s[len(s) // 2],
        "p95": s[int(len(s) * 0.95)] if len(s) > 1 else s[0],
        "mean": statistics.mean(s),
        "min": s[0],
        "max": s[-1],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", choices=["server", "client"], required=True)
    ap.add_argument("--host", type=str, default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--n-pings", type=int, default=200)
    ap.add_argument("--payload-tokens", type=int, default=8, help="int64 token ids per frame, each way")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if args.role == "server":
        run_echo_server(args.host, args.port)
        return

    payload_bytes = args.payload_tokens * 8  # int64 per token id
    times = measure_roundtrip(args.host, args.port, args.n_pings, payload_bytes)
    result = {
        "host": args.host,
        "port": args.port,
        "n_pings": args.n_pings,
        "payload_tokens": args.payload_tokens,
        "payload_bytes_each_way": payload_bytes,
        "roundtrip_s": percentiles(times),
    }
    print(json.dumps(result, indent=2))
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
