---
status: draft
---

# How do you find candidates without scoring everything?

**Goal:** generate a candidate set from a full catalogue using several cheap
retrieval methods running in parallel, and show — on a catalogue small enough
to score exhaustively — that turning off any one of them leaves a hole
nothing else fills.

**Why this is the one stage nothing downstream repairs.** A fine-ranker can be
arbitrarily good and it changes nothing for an item recall never retrieved:
the ranker never sees it, so it can never rank it, however well it would have
scored. Every later stage in this mission's funnel — pre-rank, fine-rank, the
value tree, mixing — operates strictly on the set recall hands it. If that set
is missing the item a user would actually have wanted, no later sophistication
buys it back. That asymmetry is the whole reason this stage exists, and the
rest of this README exists to make it concrete rather than merely assert it.

## Why one retrieval method is not enough

A single retrieval method has a single blind spot, and the blind spots do not
overlap. An embedding model built for semantic similarity is good at "more
like this in meaning" and structurally bad at exact-match: it has no way to
privilege a rare shared keyword over a vaguely related topic. Lexical search
is the mirror image — it will find the keyword and miss the paraphrase.
Item-to-item retrieval covers "more like what you just engaged with," which is
a different question from "what does this user want overall," and can miss
something the user would love if it does not resemble any single thing they
have already touched. Freshness and business queues exist because neither of
the above two has any way to represent "this just launched" or "this is a
contractual placement" — those are not statistical properties of an
interaction log at all. Production systems run all of these in parallel and
union the results for exactly this reason: not because any one queue is weak,
but because each is precise about something the others cannot see.

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

`two_tower_recall` scores every item by `dot(user.embedding, item.embedding)`
and nothing else — the two vectors are never combined, concatenated, or
cross-attended before that single dot product. This is not a simplification;
it is the constraint that makes retrieval possible at all. If the item tower
were allowed to see the user vector before scoring — the way a fine-ranker's
cross-attention or concatenated MLP can — item embeddings could no longer be
computed once and reused across every user. They would have to be
recalculated per query, which is exactly the cost this stage exists to avoid.
The two-tower architecture trades away some model expressiveness (it cannot
represent interactions between user and item features the way a joint model
can) in exchange for the one property that makes candidate generation over a
huge catalogue tractable at all: item vectors are precomputed once, indexed
once, and searched cheaply many times.

## Recall is lost twice, not once

`core/recall.py` scores the two-tower queue exhaustively, in a Python loop
over every item, because the catalogue is small enough that doing so is
cheap. `prod/faiss_recall.py` replaces that loop with a real vector index —
FAISS's exact `IndexFlatIP` and its approximate `IndexHNSWFlat` — built over
identical vectors, and measures the approximate index's recall against the
exact one. The exact index is itself exhaustive scoring, just done fast; the
approximate index trades some of that recall for search speed, and how much
is a tunable knob (`efSearch`, graph connectivity) rather than a fixed cost.
The lesson this comparison teaches is that recall loss compounds: a queue can
have a real structural blind spot (the subject of the widget above), and
separately, an approximate index can fail to find items that are genuinely
within that queue's reach. Both losses are measurable here only because the
catalogue is still small enough to also compute the exact answer — which
stops being true at production scale, and is the reason `08-serving`, later
in this mission, has to budget for it rather than assume it away.

## Evidence boundary

Nothing in this stage is a claim about the mission's real catalogue or real
users. The five-queue catalogue is synthetic and built to have a known
answer; the FAISS comparison runs on synthetic vectors chosen to make the
exact-vs-approximate gap visible, not to characterize any particular
production workload. What this stage does establish, mechanically: a
retrieval method's blind spot is not a matter of degree that more training
fixes, and an approximate index's recall is a parameter you set, not a
property you discover afterward. Stage `01`, content understanding, is what
will eventually replace these synthetic item vectors with real embeddings
learned from interaction and content data; until it exists, two-tower's inputs
here are illustrative placeholders for that pipeline.

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
