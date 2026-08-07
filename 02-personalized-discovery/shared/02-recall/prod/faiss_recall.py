"""The same multi-queue union as `core/recall.py`, with a real vector index.

Requires: pip install faiss-cpu numpy

`core/recall.py` scores the two-tower queue exhaustively: dot the user vector
against every item vector, in a Python loop, because the catalogue is small
enough that "score everything" is cheap. That is a demonstration property, not
a production one -- a real catalogue has millions of items, and exhaustive
scoring is not something you can wait for at request time.

This file does not reimplement all five queues -- a real system would also
swap the lexical queue for something like Elasticsearch or OpenSearch, and the
item-to-item queue for the same ANN index used here. The point of this file is
narrower and specific to the constraint the mission calls out: replace the
two-tower queue's search with a real vector index, in two configurations built
over the identical vectors:

* `IndexFlatIP` -- exact inner-product search. This is exhaustive scoring
  again, just done fast, and it is the ground truth the approximate index
  below is measured against.
* `IndexHNSWFlat` -- approximate nearest-neighbour search. Production systems
  use this (or IVF, or a managed service) because exact search does not scale,
  but "approximate" means recall is no longer 1.0 even for queries the exact
  index would answer perfectly.

Recall is therefore lost twice in a real system: once by a queue's structural
blind spot (the subject of `core/recall.py`), and again by the ANN index's own
approximation of that queue. Both losses are measured the same way here --
against an exhaustively-computable ground truth -- because the catalogue is
still small enough to afford it. That stops being true at production scale,
which is exactly why this comparison belongs in a lesson and not in a runbook.

Run:  python faiss_recall.py --catalogue-size 5000 --ef-search 16
"""

from __future__ import annotations

import argparse
import time

import faiss
import numpy as np

EMBED_DIM = 32
QUERIES_PER_CATEGORY = 20


def build_synthetic_embeddings(n_items: int, n_categories: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Noisy item clusters, and several queries drawn near each cluster center.

    Illustrative fixture data only -- the point is the index comparison, not
    the vectors themselves. The noise level is chosen so that an approximate
    index has genuine, but not overwhelming, work to do: too little noise and
    every configuration hits recall 1.0, which teaches nothing about the
    trade-off this file exists to show.
    """
    rng = np.random.default_rng(seed)
    centers = rng.uniform(-1.0, 1.0, size=(n_categories, EMBED_DIM)).astype("float32")
    categories = rng.integers(0, n_categories, size=n_items)
    noise = rng.normal(0.0, 0.6, size=(n_items, EMBED_DIM)).astype("float32")
    items = centers[categories] + noise
    query_categories = np.repeat(np.arange(n_categories), QUERIES_PER_CATEGORY)
    query_noise = rng.normal(0.0, 0.3, size=(len(query_categories), EMBED_DIM)).astype("float32")
    queries = centers[query_categories] + query_noise
    return items.astype("float32"), queries.astype("float32")


def exact_index(items: np.ndarray) -> faiss.Index:
    index = faiss.IndexFlatIP(items.shape[1])
    index.add(items)
    return index


def approximate_index(
    items: np.ndarray, m: int = 8, ef_construction: int = 40, ef_search: int = 16
) -> faiss.Index:
    """HNSW approximate search, matched to the exact index's metric.

    Two easy ways to make this comparison meaningless, both left in as
    comments because both were mistakes made while writing this file:

    - `IndexHNSWFlat` defaults to L2 distance. `IndexFlatIP` above ranks by
      inner product. Comparing "nearest by L2" against "nearest by dot
      product" measures two different notions of nearest, not one queue's
      exact-vs-approximate gap -- the metric must match, via
      `faiss.METRIC_INNER_PRODUCT`.
    - `efSearch` below k silently returns fewer real neighbours than asked
      for rather than searching harder, which looks identical to a recall
      bug. Set it explicitly, above the k you query with.

    The defaults here were chosen by search so that recall lands in a partial
    regime rather than at a degenerate 1.0 or 0.0 -- an index that never misses
    teaches nothing about approximation, and one that always misses teaches
    nothing either. Read the printed recall as a property of these parameters
    on this synthetic catalogue, not of HNSW. Raising `--ef-search` trades
    latency for recall and is the knob worth sweeping yourself; the point is
    that the trade exists and is measurable against the exact index, not that
    any particular number came out.
    """
    index = faiss.IndexHNSWFlat(items.shape[1], m, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = ef_construction
    index.add(items)
    index.hnsw.efSearch = ef_search
    return index


def recall_at_k(exact_ids: np.ndarray, approx_ids: np.ndarray, k: int) -> float:
    """Fraction of the exact top-k that the approximate index also returned."""
    hits = 0
    total = 0
    for exact_row, approx_row in zip(exact_ids, approx_ids):
        exact_set = set(exact_row[:k].tolist())
        approx_set = set(approx_row[:k].tolist())
        hits += len(exact_set & approx_set)
        total += k
    return hits / total if total else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--catalogue-size", type=int, default=5000)
    parser.add_argument("--categories", type=int, default=8)
    parser.add_argument("--k", type=int, default=25)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--m", type=int, default=8, help="HNSW graph connectivity")
    parser.add_argument("--ef-search", type=int, default=16, help="HNSW search-time candidate width")
    args = parser.parse_args()

    items, queries = build_synthetic_embeddings(args.catalogue_size, args.categories, args.seed)
    print(f"catalogue: {args.catalogue_size} items, {EMBED_DIM}-dim vectors (synthetic, illustrative only)")

    flat = exact_index(items)
    hnsw = approximate_index(items, m=args.m, ef_search=args.ef_search)

    start = time.perf_counter()
    _, exact_ids = flat.search(queries, args.k)
    exact_seconds = time.perf_counter() - start

    start = time.perf_counter()
    _, approx_ids = hnsw.search(queries, args.k)
    approx_seconds = time.perf_counter() - start

    recall = recall_at_k(exact_ids, approx_ids, args.k)

    print(f"\nexact  (IndexFlatIP)   {exact_seconds * 1000:.3f} ms for {len(queries)} queries")
    print(f"approx (IndexHNSWFlat) {approx_seconds * 1000:.3f} ms for {len(queries)} queries")
    print(f"\napprox recall@{args.k} against the exact index: {recall:.3f}")
    print("\nThese numbers are from this run, on synthetic vectors, on whatever")
    print("machine executed it. They are not a claim about production latency or")
    print("recall -- only a demonstration that the two are traded against each")
    print("other, and that the trade is measurable because the catalogue here is")
    print("small enough to also compute the exact answer.")


if __name__ == "__main__":
    main()
