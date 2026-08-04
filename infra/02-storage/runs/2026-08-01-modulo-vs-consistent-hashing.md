# Modulo vs. consistent-hash shard placement, real disk remap

**Command:**

```bash
cd infra/02-storage/core
python3 shard_placement.py --num-keys 2000 --old-nodes 4 --new-nodes 5 --shard-bytes 65536
```

**Hardware:** MacBookPro18,3 (Apple Silicon, arm64), 10 CPU cores, macOS
15.6.1, local SSD.
**Software:** Python 3.11.14, stdlib only (`hashlib`, `bisect`, `shutil`).
**Wall-clock:** under 1s total.
**Cost:** \$0 (local lane, local disk only).

**Metrics (real output, unedited):**

```
keys=2000 old_nodes=4 new_nodes=5
      scheme   remap_frac   ideal_frac
      modulo       0.8020       0.2000
  consistent       0.1800       0.2000

Real disk remap (write under old placement, move to new placement):
      scheme    moved        bytes  elapsed_s     MB/s
      modulo     1604    105119744     0.1581    634.0
  consistent      360     23592960     0.0398    565.0
```

**Notes:**

- `ideal_frac` is the theoretical minimum fraction of keys that *must* move
  when going from 4 to 5 nodes (`1 - old_nodes/new_nodes = 0.20`) -- no
  placement scheme can do better than this without foreknowledge, since the
  new node needs to end up owning roughly `1/new_nodes` of the keys from
  somewhere.
- Naive modulo hashing (`hash(key) % num_nodes`) remapped **80.2%** of keys
  for a one-node change -- four times the theoretical minimum, because
  changing the modulus changes almost every key's remainder, not just the
  ones that logically belong to the new node.
- Consistent hashing (100 virtual nodes per physical node, ring lookup)
  remapped **18.0%** of keys -- within 2 percentage points of the theoretical
  ideal, because adding one node's virtual points to the ring only steals
  keys from the ring segments immediately preceding those new points; every
  other key's nearest ring point is unchanged.
- The real disk measurement makes this concrete rather than abstract: moving
  the actually-displaced 64KB shards took 0.158s for modulo (105MB moved)
  versus 0.040s for consistent hashing (24MB moved) -- roughly 4.5x less
  data moved, roughly 4x less wall-clock, from the same node-count change on
  the same 2000 shards.
- Consistent hashing's disk throughput (565 MB/s) is slightly lower than
  modulo's (634 MB/s) despite moving less data -- both are well within normal
  variance for `shutil.move` on this SSD moving many small (64KB) files, and
  the file count (360 vs. 1604) dominates wall-clock more than any per-file
  throughput difference does.
