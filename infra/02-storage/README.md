---
status: verified
level: reference
verified: 2026-08-01
label: Storage
---

# When a storage node is added, how much data actually has to move?

**Question:** a checkpoint or a data shard is assigned to a storage node by
some placement rule. When the node count changes -- one more node added,
one lost -- how much of the existing data does that placement rule force to
move?

**The artifact this chapter follows** is a real, measured remap: 2000
shard-sized files, placed by two different rules, moved on real local disk
when the node count changes from 4 to 5.

**Before this:** [distributed training, without a cluster](../../foundations/04-distributed-training/)
-- that chapter measures what ZeRO's parameter sharding does to per-rank
memory. This chapter asks the adjacent question: once shards are assigned to
nodes, what does *changing the number of nodes* cost.

## The mechanism: two ways to assign a key to a node

**Modulo hashing:** `node = hash(key) % num_nodes`. Simple, uniform when
`num_nodes` is fixed -- and completely rebuilt when `num_nodes` changes,
because the modulus itself changed, so almost every key's remainder changes
along with it.

**Consistent hashing:** place many "virtual node" points per physical node
around a hash ring (this chapter uses 100 virtual points per node). A key is
assigned to the first virtual point clockwise from its own hash. Adding a
node only inserts new points into the ring; it does not move any existing
point. A key only moves if the *nearest* ring point to it changed -- which
only happens for keys whose old nearest point got superseded by one of the
new node's virtual points.

[`core/shard_placement.py`](core/shard_placement.py) implements both
placement rules and then does something a description cannot: it actually
writes 2000 64KB files under the old placement, computes the new placement,
and *actually moves on disk* every file whose target node changed, timing
the whole thing.

## What actually moved

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

Going from 4 to 5 nodes can never move less than 20% of the keys — the new
node has to end up owning roughly a fifth of the data from *somewhere*. That
20% is `ideal_frac`. Modulo hashing moved 80.2% — four times the unavoidable
minimum, because the modulus itself changed, and a key's remainder under
`% 4` bears no relationship to its remainder under `% 5`. Consistent hashing
moved 18.0%, within two points of the theoretical floor. On real disk, that
difference is 105MB moved versus 24MB — a concrete, measured cost, not a
hypothetical one.

Full run: [`runs/2026-08-01-modulo-vs-consistent-hashing.md`](runs/2026-08-01-modulo-vs-consistent-hashing.md).

## Why this is not an abstract exercise

This repository's own checkpoint shards -- the per-rank optimizer-state
slices measured in
[`foundations/04-distributed-training/`](../../foundations/04-distributed-training/) --
are exactly this kind of key. If a training job's world size changes between
runs (more or fewer ranks, or a checkpoint saved at one shard count and
resumed at another), whatever rule assigned optimizer-state shards to files
faces exactly this same remap question. A naive `shard_id % world_size`
assignment would force nearly a full re-shard on almost any world-size
change; the ring-based alternative is why production checkpoint formats
(and production key-value stores) do not use modulo placement once the node
count is expected to change.

## What this cannot show you

**Real distributed storage systems.** This chapter moves files on one
machine's local SSD. It says nothing about network-attached storage,
replication consistency, partial-failure semantics during a rebalance, or
the throughput ceiling of a real multi-node storage cluster -- all of which
dominate a real system's behavior far more than the placement rule does.

**Load skew from real key distributions.** This run used uniformly
distributed synthetic keys (`shard-00000` through `shard-01999`). Real
workloads have hot keys; consistent hashing's virtual-node count is itself a
tuning knob for load balance that this chapter does not explore.

## A brief history

Consistent hashing predates distributed storage entirely.

<!-- interactive: ConsistentHashLineage -->

## Exercises

1. Re-run with `--virtual-nodes 10` and `--virtual-nodes 1000`. Does the
   remap fraction move closer to or further from the ideal as virtual nodes
   increase? Why would a real system not simply set this number as high as
   possible?
2. Change `--new-nodes` to simulate removing a node (`--old-nodes 5
   --new-nodes 4`) instead of adding one. Does the remap-fraction gap
   between the two schemes hold in the same direction?
3. The real disk throughput numbers (634 MB/s vs. 565 MB/s) went the
   *opposite* direction from the byte-count savings. Explain why total bytes
   moved is the number that matters for wall-clock here, not per-file
   throughput.

## Run it

```bash
cd infra/02-storage/core
python3 shard_placement.py --num-keys 2000 --old-nodes 4 --new-nodes 5 --shard-bytes 65536
```

CPU + local disk only, under 1s wall-clock, \$0. Full trace:
[`runs/2026-08-01-modulo-vs-consistent-hashing.md`](runs/2026-08-01-modulo-vs-consistent-hashing.md).
