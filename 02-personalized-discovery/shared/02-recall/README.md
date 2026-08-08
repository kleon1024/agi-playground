---
status: verified
level: foundation
verified: 2026-07-30
---

# How do you find candidates without scoring everything?

**Goal:** generate a candidate set from a full catalogue using several cheap
retrieval methods running in parallel, and show — on a catalogue small enough
to score exhaustively — that turning off any one of them leaves a hole
nothing else fills.

**Before this:** [stage 00's split](../00-interactions/) supplies the
behavioural log these queues learn from, and
[stage 01's content labels](../01-content-understanding/) stand in for the
real item embeddings the two-tower and freshness queues eventually need.

**Why this is the one stage nothing downstream repairs.** A fine-ranker can be
arbitrarily good and it changes nothing for an item recall never retrieved:
the ranker never sees it, so it can never rank it, however well it would have
scored. Every later stage in this mission's funnel — pre-rank, fine-rank, the
value tree, mixing — operates strictly on the set recall hands it. If that set
is missing the item a user would actually have wanted, no later sophistication
buys it back. That asymmetry is the whole reason this stage exists, and the
rest of this README exists to make it concrete rather than merely assert it.

## Why one retrieval method is not enough

Run just one retrieval method and you get exactly one blind spot — and the
blind spots do not overlap. Reach for an embedding model tuned for semantic
similarity and you get "more like this in meaning," structurally bad at
exact-match: it has no way to privilege a rare shared keyword over a
vaguely related topic. Reach for lexical search instead and you get the
mirror image — it finds the keyword and misses the paraphrase. Item-to-item
retrieval answers "more like what you just engaged with," a different
question from "what does this user want overall," and misses anything that
does not resemble a single thing already touched. Freshness and business
queues exist because neither of the above can represent "just launched" or
"a contractual placement" — not statistical properties of an interaction log
at all. Run all of these in parallel and union the results, not because any
one queue is weak, but because each sees something the others cannot.

## What you build

`core/recall.py` — five retrieval queues, each implemented from scratch over
plain Python lists, no third-party dependency:

| Queue | Retrieves by | Structurally blind to |
|---|---|---|
| Two-tower | Dot product of user and item embeddings | Exact keyword matches; anything a noisy or cold embedding misrepresents |
| Lexical | Term-overlap, weighted by rarity (a from-scratch TF-IDF) | Semantic similarity expressed in different words |
| Item-to-item | Nearest neighbours of specific history items | Anything not close to any single seed item, even if close to the user's overall taste |
| Freshness | Most recent items above a popularity floor | Personalization — it is a global queue by design |
| Business | Popularity among editorially boosted items | Everything not on the boost list; it carries policy, not statistics |

`union_queues` merges their outputs; `target_coverage` measures, exactly, what
fraction of a known target set the union contains.

## A catalogue small enough to know the right answer

`core/recall.py` builds a small synthetic catalogue — a few hundred items
across a handful of categories — and, for each synthetic user, four target
items constructed with a known, distinct provenance: one is close to the
user's averaged interest but shares no keyword with their query (findable only
by the two-tower queue); one shares an exact rare keyword but sits far away in
embedding space (findable only by lexical search); one is the specific nearest
neighbour of one history item, not of the user's overall profile (findable
only by item-to-item); one is brand-new with a still-unreliable embedding
(findable only by the freshness queue). This is illustrative fixture data, not
a measurement of any real platform — but because every target's provenance is
known by construction, coverage of it can be scored exactly rather than
estimated. That is what "exhaustive scoring" buys: on a real catalogue of
millions of items you cannot know the true relevant set to check against; on
one this size, you can, and every approximation downstream is measurable
against it.

## See a blind spot appear

Before touching the control below, predict what happens to the union's
coverage of the target set if you disable the lexical queue. Then toggle it.

<!-- interactive: RecallQueues -->

The numbers in that control are illustrative and synthetic, generated the same
way `core/recall.py` generates its demo catalogue — not a measured result. The
behaviour it demonstrates is the real point: disabling a queue does not lower
coverage evenly across all targets. It removes almost exactly the targets that
queue alone could reach, while the others barely move, because the remaining
queues were never looking in that part of the space to begin with. A small
amount of incidental overlap between queues is normal — an item-to-item
neighbour occasionally happens to also be the semantic nearest neighbour —
but it is luck, not coverage, and it does not scale with catalogue size the
way a queue's designed coverage does.

## The two-tower constraint

Read `two_tower_recall` and you find it scores every item by
`dot(user.embedding, item.embedding)` and nothing else — the two vectors are
never combined, concatenated, or cross-attended before that dot product. That
is not a simplification; it is the constraint that makes retrieval possible
at all. Let the item tower see the user vector before scoring — the way a
fine-ranker's cross-attention or concatenated MLP can — and item embeddings
can no longer be computed once and reused across every user; they have to be
recalculated per query, exactly the cost this stage exists to avoid. The
trade: less expressiveness (no user-item feature interaction) for the one
property that makes candidate generation over a huge catalogue tractable —
item vectors precomputed once, indexed once, searched cheaply many times.

## Recall is lost twice, not once

`core/recall.py` scores the two-tower queue exhaustively, in a Python loop
over every item, because the catalogue is small enough that doing so is
cheap. `prod/faiss_recall.py` replaces that loop with a real vector index —
FAISS's exact `IndexFlatIP` and its approximate `IndexHNSWFlat` — built over
identical vectors, and measures the approximate index's recall against the
exact one. The exact index is itself exhaustive scoring, just done fast; the
approximate index trades some of that recall for search speed, and how much
is a tunable knob (`efSearch`), not a fixed cost. Recall loss compounds: a
queue can have a real structural blind spot (the widget above), and
separately, an approximate index can fail to find items genuinely within
that queue's reach. Both losses are measurable here only because the
catalogue is still small enough to also compute the exact answer — which
stops being true at production scale, and is the reason `08-serving`, later
in this mission, has to budget for it rather than assume it away.

## The fix and its trade

The fix is the multi-queue union, and the recorded run prices why no single
queue can do the job: disabling one queue drops aggregate coverage 5-20
points (two_tower 0.84, lexical 0.80, item_to_item 0.95, freshness 0.84
against a 1.00 baseline), and the other queues recover only 4-16 of the
disabled queue's 20 targets — by incidental overlap, not by design. The
union is not interchangeable parts; each queue owns targets no other queue
reaches, and item_to_item, the slowest queue, carries the least redundant
coverage (4/20 recoverable), which is why it cannot be dropped for speed.

The trade, named: the fix pays in recall-bought-back cost at two levels.
Running more queues costs serving latency — parallel recall at the slowest
wait, with a timeout that returns a smaller union instead of failing the
request (stage 08's read). And the approximate index that makes candidate
generation affordable trades a bounded recall loss for latency: the
recorded FAISS comparison shows 0.913 recall at 0.576 ms and 0.984 at 0.714
ms against the exact index's 1.133-0.911 ms, and the gap to exact never
fully closes. Recall is the one stage nothing downstream repairs, so both
costs are paid once, at the funnel's entry, deliberately.

## Who owns the loop

- **The retrieval team** owns the queues and their provenance: each queue's
  structural blind spot is a designed property, and the disable-sweep
  coverage is its regression test.
- **The serving team** owns the union's latency: fan-out, timeouts, and the
  approximate-index settings (ef-search) that trade recall for speed are
  serving decisions made against the stage 08 budget.
- **The evaluation team** owns the coverage-by-provenance read — the number
  that says a missing queue is a permanently missing class of items, not a
  small overlap the others will absorb.
- **The content team** (stage 01) owns the inputs the two-tower queue
  depends on until real embeddings exist — a placeholder the stage names
  explicitly rather than hiding.

## Evidence boundary

Nothing in this stage is a claim about the mission's real catalogue or real
users. The five-queue catalogue is synthetic and built to have a known
answer; the FAISS comparison runs on synthetic vectors chosen to make the
exact-vs-approximate gap visible, not to characterize a production workload.
What this stage does establish, mechanically: a retrieval method's blind spot
is not a matter of degree that more training fixes, and an approximate
index's recall is a parameter you set, not a property you discover
afterward. Stage `01`, content understanding, will eventually replace these
synthetic item vectors with real embeddings; until it exists, two-tower's
inputs here are illustrative placeholders.

## What the numbers actually look like, on a real run

Run the five queues against the 400-item synthetic catalogue and disable each
in turn:

```
(none disabled)        mean coverage 1.00
disable two_tower       mean coverage 0.84   two_tower's own row: 8/20 (0.40)
disable lexical         mean coverage 0.80   lexical's own row:   4/20 (0.20)
disable item_to_item    mean coverage 0.95   item_to_item's own row: 16/20 (0.80)
disable freshness       mean coverage 0.84   freshness's own row: 7/20 (0.35)
```

Every disable drops that queue's own target row to somewhere between 0.20 and
0.80, while the other three queues stay at or near 20/20 — the widget's claim
holds on the actual script output, not only in the illustrative animation.

The FAISS comparison over a 5,000-item catalogue tells the same recall-versus-
speed story with real numbers: at the default search width, the approximate
`IndexHNSWFlat` index answers in 0.576 ms against the exact index's 1.133 ms
but only reaches 0.913 recall@25; widening `--ef-search` to 64 pushes recall
to 0.984 while also narrowing the speed gap (0.714 ms vs. 0.911 ms). Recall
bought back at a measured latency cost, on this machine, this run — full
output in
[`runs/2026-07-30-multi-queue-coverage.md`](runs/2026-07-30-multi-queue-coverage.md).

## Reproducing

```bash
# the five queues, from scratch, on a synthetic catalogue
python core/recall.py --catalogue-size 400 --seed 0

# disable one queue and watch which targets stop being found
python core/recall.py --disable lexical

# exact vs. approximate search over a real vector index
pip install faiss-cpu numpy
python prod/faiss_recall.py --catalogue-size 5000
python prod/faiss_recall.py --catalogue-size 5000 --ef-search 64
```

## Exercises

1. **Find the exact hole.** Run `core/recall.py --disable item_to_item` and
   identify, from the per-provenance breakdown, exactly which target category
   loses coverage. Confirm the other three barely move.
2. **Break the metric match.** In `prod/faiss_recall.py`, build the HNSW index
   without `faiss.METRIC_INNER_PRODUCT` and rerun. The recall number that
   results is not a weaker approximation — it is comparing two different
   notions of "nearest," and the file's own docstring explains why that
   happened while writing it.
3. **Trade recall for speed on purpose.** Sweep `--ef-search` from 8 to 128 in
   `prod/faiss_recall.py` and plot recall against query latency. Identify the
   point past which more search time stops buying meaningful recall.
4. **Widen the union.** Increase `--k` in `core/recall.py` for every queue and
   observe that the union's target coverage rises even with a queue disabled —
   then check what that costs the next stage, which has to score every extra
   candidate.

## Next

`03-pre-rank` takes this union — hundreds of candidates instead of millions —
and narrows it further with a lightweight scorer cheap enough to run on all of
them, before the expensive fine-ranker ever sees a candidate. It is not yet
built.

A detour from here: [the queue you disable is the target you
lose](when-you-lose-a-queue/) — the disable sweep across all four queues:
no loss is fully recovered, and item_to_item's blind spot is the deepest
(only 4/20 targets recovered elsewhere).

Another detour: [recall bought back at a measured latency
cost](the-price-of-approximate/) — the recorded exact-vs-approximate run:
ef-search 64 lifts recall 0.913 -> 0.984 at a real latency price, and the
gap to exact never fully closes.

A third detour: [the tail that the index forgets](when-the-tail-goes-cold/) — the executed power-law read: the top 100 items hold 69.3% of demand and a 200-item pass keeps only 100 of 900 tail items, so tail coverage is a deliberate trade.
