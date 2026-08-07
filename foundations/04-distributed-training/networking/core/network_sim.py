"""Star vs. ring allreduce, measured over real inter-process IPC on localhost.

Every rank is a real OS process (`multiprocessing.Process`), and every message
crosses a real `multiprocessing.Queue` (pickled, pushed through a pipe, read
back). That is genuine communication overhead, not a threaded approximation.
What it does NOT reflect is real network fabric: every "message" here crosses
the same machine's memory bus over loopback, with none of a datacenter's
bandwidth ceilings, NIC contention, or multi-hop latency. See the README's
"What this cannot show you" section before reading the numbers as more than
a topology demonstration.

Correctness, not just speed, is asserted: every run's summed result is
compared against a plain single-process sum of the same inputs.
"""

import argparse
import multiprocessing as mp
import queue as pyqueue
import threading
import time

import numpy as np


def _star_worker(rank, world_size, local, to_root, result_qs, barrier, out_q):
    barrier.wait()
    t0 = time.perf_counter()
    if rank == 0:
        total = local.copy()
        for _ in range(world_size - 1):
            total += to_root.get()
        for r, q in enumerate(result_qs):
            if r != rank:
                q.put(total)
    else:
        to_root.put(local)
        total = result_qs[rank].get()
    elapsed = time.perf_counter() - t0
    out_q.put((rank, elapsed, total))


def _run_star(world_size, arrays):
    to_root = mp.Queue()
    result_qs = [mp.Queue() for _ in range(world_size)]
    barrier = mp.Barrier(world_size)
    out_q = mp.Queue()
    procs = [
        mp.Process(
            target=_star_worker,
            args=(r, world_size, arrays[r], to_root, result_qs, barrier, out_q),
        )
        for r in range(world_size)
    ]
    for p in procs:
        p.start()
    results = [out_q.get() for _ in range(world_size)]
    for p in procs:
        p.join()
    elapsed = max(r[1] for r in results)
    result_by_rank = {r[0]: r[2] for r in results}
    return elapsed, result_by_rank


def _ring_worker(rank, world_size, local, edge_qs, barrier, out_q):
    barrier.wait()
    t0 = time.perf_counter()
    p = world_size
    chunk_len = len(local) // p
    chunks = [local[i * chunk_len : (i + 1) * chunk_len].copy() for i in range(p)]
    send_q = edge_qs[rank]  # this rank's outgoing edge, to (rank+1) % p
    recv_q = edge_qs[(rank - 1) % p]  # incoming edge, from (rank-1) % p

    # A ring where every rank does put() then get() can deadlock: once a
    # chunk is larger than the OS pipe buffer (a few hundred KB), put()
    # blocks until the far end drains it -- but the far end is itself
    # blocked in its own put(), so nobody ever reaches get(). A background
    # thread does the actual send so this process's main thread is always
    # free to drain its incoming queue.
    to_send = pyqueue.Queue()

    def _sender():
        while True:
            item = to_send.get()
            if item is None:
                return
            send_q.put(item)

    sender_thread = threading.Thread(target=_sender, daemon=True)
    sender_thread.start()

    # Reduce-scatter: p-1 steps. After step s, rank has accumulated s+1
    # ranks' worth of data into the chunk it just received.
    send_idx = rank
    for _ in range(p - 1):
        recv_idx = (send_idx - 1) % p
        to_send.put(chunks[send_idx])
        chunks[recv_idx] = chunks[recv_idx] + recv_q.get()
        send_idx = recv_idx
    # After p-1 steps, the fully-reduced chunk sits at index (rank + 1) % p.
    finished_idx = (rank + 1) % p

    # All-gather: p-1 steps, circulating the now-fully-reduced chunks
    # around the ring without any further addition.
    send_idx = finished_idx
    for _ in range(p - 1):
        recv_idx = (send_idx - 1) % p
        to_send.put(chunks[send_idx])
        chunks[recv_idx] = recv_q.get()
        send_idx = recv_idx

    to_send.put(None)
    sender_thread.join()

    result = np.concatenate(chunks)
    elapsed = time.perf_counter() - t0
    out_q.put((rank, elapsed, result))


def _run_ring(world_size, arrays):
    edge_qs = [mp.Queue() for _ in range(world_size)]
    barrier = mp.Barrier(world_size)
    out_q = mp.Queue()
    procs = [
        mp.Process(
            target=_ring_worker,
            args=(r, world_size, arrays[r], edge_qs, barrier, out_q),
        )
        for r in range(world_size)
    ]
    for p in procs:
        p.start()
    results = [out_q.get() for _ in range(world_size)]
    for p in procs:
        p.join()
    elapsed = max(r[1] for r in results)
    result_by_rank = {r[0]: r[2] for r in results}
    return elapsed, result_by_rank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world-sizes", type=int, nargs="+", default=[2, 4, 8])
    ap.add_argument(
        "--payload-mb", type=float, nargs="+", default=[1.0, 8.0, 32.0]
    )
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    print(f"{'world_size':>10} {'payload_MB':>10} {'star_s':>10} {'ring_s':>10} "
          f"{'star_bytes/rank':>16} {'ring_bytes/rank':>16} {'correct':>8}")

    for world_size in args.world_sizes:
        for payload_mb in args.payload_mb:
            n_floats = int(payload_mb * 1024 * 1024 / 4)
            n_floats -= n_floats % world_size  # exact chunking for the ring
            rng = np.random.default_rng(args.seed)
            arrays = [
                rng.standard_normal(n_floats).astype(np.float32)
                for _ in range(world_size)
            ]
            expected = sum(arrays)

            star_elapsed, star_result = _run_star(world_size, arrays)
            ring_elapsed, ring_result = _run_ring(world_size, arrays)

            star_ok = all(
                np.allclose(v, expected, atol=1e-3) for v in star_result.values()
            )
            ring_ok = all(
                np.allclose(v, expected, atol=1e-3) for v in ring_result.values()
            )

            # Bytes moved per rank, on the wire (not counting the local copy).
            bytes_per_float = 4
            star_bytes_root = (world_size - 1) * 2 * n_floats * bytes_per_float
            star_bytes_leaf = 2 * n_floats * bytes_per_float
            star_bytes_avg = (
                star_bytes_root + (world_size - 1) * star_bytes_leaf
            ) / world_size
            ring_bytes_per_rank = 2 * (world_size - 1) * (n_floats // world_size) * bytes_per_float

            print(
                f"{world_size:>10} {payload_mb:>10.1f} {star_elapsed:>10.4f} "
                f"{ring_elapsed:>10.4f} {star_bytes_avg:>16.0f} "
                f"{ring_bytes_per_rank:>16.0f} {star_ok and ring_ok!s:>8}"
            )


if __name__ == "__main__":
    main()
