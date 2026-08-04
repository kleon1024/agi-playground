"""Shard placement: naive modulo hashing vs. consistent hashing, measured by
how much data actually has to move when the storage-node count changes.

This is not an abstract exercise: this repository's own checkpoint shards
(the optimizer-state slices of foundations/04-distributed-training/) are exactly this kind of key -> node
assignment. Adding or removing a storage node is routine; how much data
moves in response is a real, measurable cost, not a theoretical one.

Every number below comes from a real run: real files written to real local
disk, real os.urandom payloads, real shutil.move calls timed with
time.perf_counter.
"""

import argparse
import bisect
import hashlib
import os
import shutil
import tempfile
import time


def _hash(key: str) -> int:
    return int(hashlib.sha256(key.encode()).hexdigest(), 16)


def modulo_placement(keys, num_nodes):
    return {k: _hash(k) % num_nodes for k in keys}


def build_consistent_ring(num_nodes, virtual_nodes):
    ring = {}
    for node in range(num_nodes):
        for v in range(virtual_nodes):
            point = _hash(f"node-{node}-v{v}")
            ring[point] = node
    return ring


def consistent_placement(keys, num_nodes, virtual_nodes):
    ring = build_consistent_ring(num_nodes, virtual_nodes)
    sorted_points = sorted(ring.keys())
    placement = {}
    for k in keys:
        h = _hash(k)
        idx = bisect.bisect_left(sorted_points, h)
        if idx == len(sorted_points):
            idx = 0
        placement[k] = ring[sorted_points[idx]]
    return placement


def remap_fraction(old_placement, new_placement):
    moved = sum(1 for k in old_placement if old_placement[k] != new_placement[k])
    return moved / len(old_placement)


def measure_real_disk_remap(keys, old_placement, new_placement, shard_bytes, base_dir):
    """Actually write shards under the old placement, then actually move the
    ones whose target node changed under the new placement, on real disk."""
    for node in set(old_placement.values()):
        os.makedirs(os.path.join(base_dir, f"node-{node}"), exist_ok=True)
    payload = os.urandom(shard_bytes)
    for k in keys:
        path = os.path.join(base_dir, f"node-{old_placement[k]}", k)
        with open(path, "wb") as f:
            f.write(payload)

    to_move = [k for k in keys if old_placement[k] != new_placement[k]]
    for node in set(new_placement.values()):
        os.makedirs(os.path.join(base_dir, f"node-{node}"), exist_ok=True)

    t0 = time.perf_counter()
    total_bytes = 0
    for k in to_move:
        src = os.path.join(base_dir, f"node-{old_placement[k]}", k)
        dst = os.path.join(base_dir, f"node-{new_placement[k]}", k)
        shutil.move(src, dst)
        total_bytes += os.path.getsize(dst)
    elapsed = time.perf_counter() - t0
    return elapsed, total_bytes, len(to_move)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--num-keys", type=int, default=2000)
    ap.add_argument("--old-nodes", type=int, default=4)
    ap.add_argument("--new-nodes", type=int, default=5)
    ap.add_argument("--virtual-nodes", type=int, default=100)
    ap.add_argument("--shard-bytes", type=int, default=65536)
    args = ap.parse_args()

    keys = [f"shard-{i:05d}" for i in range(args.num_keys)]

    modulo_old = modulo_placement(keys, args.old_nodes)
    modulo_new = modulo_placement(keys, args.new_nodes)
    modulo_frac = remap_fraction(modulo_old, modulo_new)

    consistent_old = consistent_placement(keys, args.old_nodes, args.virtual_nodes)
    consistent_new = consistent_placement(keys, args.new_nodes, args.virtual_nodes)
    consistent_frac = remap_fraction(consistent_old, consistent_new)

    print(f"keys={args.num_keys} old_nodes={args.old_nodes} new_nodes={args.new_nodes}")
    print(f"{'scheme':>12} {'remap_frac':>12} {'ideal_frac':>12}")
    ideal = 1 - args.old_nodes / args.new_nodes  # min data that MUST move
    print(f"{'modulo':>12} {modulo_frac:>12.4f} {ideal:>12.4f}")
    print(f"{'consistent':>12} {consistent_frac:>12.4f} {ideal:>12.4f}")

    print()
    print("Real disk remap (write under old placement, move to new placement):")
    print(f"{'scheme':>12} {'moved':>8} {'bytes':>12} {'elapsed_s':>10} {'MB/s':>8}")
    for name, old_p, new_p in [
        ("modulo", modulo_old, modulo_new),
        ("consistent", consistent_old, consistent_new),
    ]:
        with tempfile.TemporaryDirectory() as tmp:
            elapsed, total_bytes, moved = measure_real_disk_remap(
                keys, old_p, new_p, args.shard_bytes, tmp
            )
            mb_s = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else float("inf")
            print(f"{name:>12} {moved:>8} {total_bytes:>12} {elapsed:>10.4f} {mb_s:>8.1f}")


if __name__ == "__main__":
    main()
