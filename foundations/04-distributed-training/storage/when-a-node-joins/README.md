---
status: verified
level: applied
base: scratch
label: When a node joins
verified: 2026-08-06
---

# The remap that adding one node costs

**Question:** [the storage chapter](../) placed 2,000 keys over 4 nodes,
added a 5th, and measured the real disk remap. This chapter reads the
recorded run and asks what 0.802 versus 0.180 actually means.

**Before this:** [the storage chapter](../) and its recorded shard-placement
run.

## The comparison, read

The run ([record](runs/2026-08-06-remap-read.md)) reads the recorded
placement and disk move:

| scheme | remap fraction | ideal | keys moved | bytes moved |
|---|---:|---:|---:|---:|
| modulo | 0.802 | 0.200 | 1,604 | 105 MB |
| consistent | 0.180 | 0.200 | 360 | 24 MB |

## Two readings

**Modulo remaps ~4x the ideal share.** When a 5th node joins, the ideal is
for ~1/5 of the keys (0.200) to move to it. Modulo rehashes every key —
0.802 moved, four times the ideal — because each key's node depends on the
total node count. Consistent hashing moves only the keys the new node
actually takes (0.180, essentially the ideal 0.200).

**The bytes are the real cost, and they confirm the fractions.** 105 MB
moved under modulo versus 24 MB under consistent — a 4.4x difference on
2,000 small shards. At corpus scale, that multiple is the difference
between a node-join that costs minutes of I/O and one that costs a fraction
of it. The placement fraction and the disk cost are the same story measured
two ways.

## The fix and its trade

The fix is reading the placement choice off the recorded run: modulo's 0.802
remap is not a bug in the numbers, it is the mechanism — `hash(key) %
n_nodes` depends on the total node count, so changing 4 to 5 rehashes every
key, and 1,604 keys (105 MB) must move. Consistent hashing moves 360 keys
(24 MB) because the hash-ring positions of the new node's virtual points
only supersede the nearest existing points; 0.180 is sampling noise around
the 0.200 ideal, and the scheme's defining property is that a node change
moves only the new node's share. The trade is the knob and the boundary:
the virtual-node count is a load-balance tuning parameter this chapter does
not sweep, and the run is local SSD placement only — it says nothing about
replica-aware or rack-aware schemes, which the chapter's landscape covers
(the scheme's origin: Karger et al., "Consistent Hashing and Random Trees,"
STOC, 1997). What the fix does establish is that the fraction and the byte
cost are the same decision measured twice, so a checkpoint format that
expects world-size changes can price a node-join in advance.

## Who owns the loop

- **The storage team** owns the placement rule: the recorded 0.802-versus-
  0.180 gap is their regression test for any node-count change, and the
  remap fraction at a declared delta is the acceptance metric.
- **The checkpoint-format owner** owns the shard-to-file assignment: the
  sharded optimizer state this chapter's parent produces is placed under
  this same rule, and modulo placement there means a world-size change
  re-shards nearly everything.
- **The training engineer** owns the cost in advance: resuming a job at a
  different shard count triggers the remap, and the placement rule decides
  whether that is 105 MB or 24 MB of I/O.

## Evidence boundary

The recorded placement + real-disk-remap run (2,000 keys, 4->5 nodes, 64KB
shards, local SSD). It reads that artifact; it does not re-run the remap
and does not extend the finding to replica-aware or rack-aware schemes,
which the chapter's landscape discusses.

## Check your mental model

Answer each before opening it.

**1. Why does adding one node to modulo rehash every key instead of one in
five?**

<details>
<summary>Answer</summary>

Because modulo placement is `hash(key) % n_nodes` — the node depends on the
total node count, so changing 4 to 5 changes the assignment of every key,
not just the new node's share. The recorded 0.802 is what that looks like:
~80% of keys land on a different node than before, and each one must move.

</details>

**2. Consistent hashing moves only 0.180 — why not exactly the ideal
0.200?**

<details>
<summary>Answer</summary>

Because the hash-ring positions of the 2,000 keys and the 5 node markers
are random; the new node's ring segment covers whatever fraction of keys
its position happens to own. 0.180 is sampling noise around the ideal
0.200 — the scheme's defining property is that a node change moves *only*
that node's share, not that the share lands exactly at the expectation.

</details>

## Next

Back to [the storage chapter](../), or to
[the distributed-training chapter](../../)
which produces the sharded checkpoints that live on this storage.
