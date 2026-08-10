---
status: verified
level: applied
base: none
label: When you lose a queue
verified: 2026-08-06
---

# The queue you disable is the target you lose

**Question:** [stage 02](../) runs four recall queues in parallel and unions
the results, because each queue has a blind spot. How deep are the blind
spots, and how much do the other queues recover when one is gone?

**Before this:** [stage 02's multi-queue recall](../), including the
provenance assignment that names each target's owner.

## The sweep, measured

The run ([record](runs/2026-08-06-queue-disable-sweep.md)) disables each
queue in turn on the stage's synthetic catalogue:

| disabled queue | coverage | its targets found | recovered by others |
|---|---:|---:|---:|
| two_tower | 0.84 | 8/20 | 12 |
| lexical | 0.80 | 4/20 | 16 |
| item_to_item | 0.95 | 16/20 | 4 |
| freshness | 0.84 | 7/20 | 13 |

Baseline coverage with all queues: 1.00.

## Two readings

**No queue's loss is fully recovered.** Every disabled queue drops aggregate
coverage (5-20 points), and the other queues recover only 4-16 of its 20
targets — by incidental overlap, not by design. The union is not
interchangeable parts; each queue owns targets no other queue reaches.

**item_to_item's blind spot is the deepest.** Only 4 of its 20 targets are
recovered elsewhere. The stage's design makes i2i the slow, heavy-tailed
queue (a graph traversal over history), and the sweep shows its targets are
also the least replaceable — the queue with the worst latency profile
carries the least redundant coverage, which is precisely why it cannot be
dropped for speed.

That is the stage's central claim, now a table: recall is the one stage
downstream ranking cannot repair, because the candidates a missing queue
would have found are simply absent, and no perfect ranker ranks an item that
was never retrieved.

## The fix and its trade

The fix is to run the queues in parallel and union their outputs, and to
treat each queue as non-replaceable — the measured sweep is the evidence.
Disabling any one queue drops aggregate coverage 5-20 points (two_tower
0.84, lexical 0.80, item_to_item 0.95, freshness 0.84 against 1.00), and
the other queues recover only 4-16 of the disabled queue's 20 targets, by
incidental overlap rather than by design.

The trade, named: the union is not interchangeable parts, and the deepest
case is item_to_item — only 4 of its 20 targets are recovered elsewhere,
while it is also the slowest queue (a graph traversal over history). The
queue with the worst latency profile carries the least redundant coverage,
which is precisely why it cannot be dropped for speed; dropping it saves
latency and permanently removes the items only it can find. The fix pays
the latency of every queue, including the slow one, because the alternative
is a recall hole that no perfect ranker downstream can repair.

## Who owns the loop

- **The retrieval team** owns each queue's provenance assignment and the
  coverage-by-queue read — the sweep is its regression test that no queue
  has been silently removed.
- **The serving team** owns the union latency, including the slow tail of
  item_to_item: a timeout that drops the slow queue must record the smaller
  union as degraded, never as full recall.
- **The evaluation team** owns the non-recoverability metric — the number
  that says how many of a disabled queue's targets the others absorb, which
  is what turns "we can drop it for speed" into a falsifiable claim.

## Evidence boundary

One synthetic catalogue, one seed, 20 users; the queues and provenance
assignment are the stage's own. It shows the blind-spot depth and
non-recoverability on this synthetic design; it does not claim real
catalogue blind spots have the same magnitudes, and it does not measure the
real recall-quality cost of a missing queue.

## Check your mental model

Answer each before opening it.

**1. Why doesn't the union of the other three queues cover a disabled
queue's targets?**

<details>
<summary>Answer</summary>

Because each target is assigned a provenance — the one queue whose logic can
reach it — and the other queues find it only when their candidate sets
incidentally overlap. The union recovers 4-16 of 20 targets, never all:
the overlap is statistical, not a designed backstop, which is why recall is
the stage where a missing method shows up as permanently missing items.

</details>

**2. item_to_item loses the least coverage (0.95) but recovers the fewest
targets (4/20). What does that combination say?**

<details>
<summary>Answer</summary>

That i2i's targets overlap least with the other queues: its own coverage
stays high because most targets are still found, but the few it uniquely
owns are almost never reachable elsewhere. The queue's blind spot is the
deepest, and because it is also the slowest queue, the design tension is
real: it carries unique coverage and the worst latency at once.

</details>

## Next

Back to [stage 02's recall](../), or forward to
[stage 03's pre-rank](../../03-pre-rank/) where the union's candidates get
cut from ~1,000 to ~100 before the expensive ranker.
