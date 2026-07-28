"""The same funnel-composition question as `core/latency_pipeline.py`, timed
with real concurrency, a real ANN index, and real per-stage compute instead
of sampled distributions.

Requires: pip install faiss-cpu numpy

Three things are real here that `core/` only simulated:

1. **The two-tower recall queue** runs an actual `faiss.IndexHNSWFlat` search
   over synthetic item vectors -- the same approximate index `02-recall`'s
   `prod/faiss_recall.py` introduces for the recall-versus-latency trade. This
   file does not repeat that trade (see that file for the recall-vs-speed
   comparison); it only reuses "a real ANN search is one real cost among
   several" as the recall queue's actual latency, instead of a sampled number.
2. **The fan-out is a real thread pool**, waited on with a real timeout via
   `concurrent.futures.wait(..., timeout=...)`, not a `max()` over four
   pre-drawn numbers. The other three recall queues (lexical, item-to-item,
   freshness) are not implemented for real here -- in production they are
   separate services reached over the network, so they are stood in for with
   `time.sleep` calls at the queue's typical latency, submitted to the same
   thread pool as the ANN query. That is an honest concurrency model for I/O-
   bound network calls: a Python thread blocked in `time.sleep` or in a real
   socket read behaves the same way from the scheduler's point of view, both
   release the GIL while waiting. It would *not* be honest for CPU-bound work
   -- if all four queues were doing heavy Python-level computation instead of
   waiting on I/O, the GIL would serialize them and a thread pool would not
   help, which is exactly why the one queue that does real local CPU work
   here (the ANN search) is measured for real rather than also stood in for.
3. **Downstream stages are real NumPy compute**, not sampled latencies: linear
   scoring for pre-rank, a small two-layer transform for fine-rank (heavier
   per candidate, on purpose -- that gap is the entire justification for
   having two ranking stages instead of one), a weighted sum for the value
   tree, a greedy top-k with a similarity penalty for mixing, and a boolean
   mask for the rule engine. Their cost is whatever NumPy actually takes to do
   that work at the given candidate-set size, not a chosen distribution.

The end-to-end latency distribution is measured with `numpy.percentile` over
many repeated pipeline runs -- explicit quantile estimation over the full
sample, no histogram bucketing or approximation library involved.

Run:  python serving_harness.py --trials 300 --recall-timeout-ms 20
"""

from __future__ import annotations

import argparse
import random
import time
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass

import faiss
import numpy as np

EMBED_DIM = 32
FINE_RANK_HIDDEN = 128


# --- 1. synthetic catalogue and a real ANN index -----------------------------


def build_catalogue(n_items: int, n_categories: int, seed: int) -> np.ndarray:
    """Noisy category clusters -- same construction as `02-recall`'s fixtures,
    reused here only as filler vectors for the ANN index and the downstream
    NumPy stages to have something real to compute over."""
    rng = np.random.default_rng(seed)
    centers = rng.uniform(-1.0, 1.0, size=(n_categories, EMBED_DIM)).astype("float32")
    categories = rng.integers(0, n_categories, size=n_items)
    noise = rng.normal(0.0, 0.6, size=(n_items, EMBED_DIM)).astype("float32")
    return (centers[categories] + noise).astype("float32")


def build_ann_index(items: np.ndarray, m: int = 8, ef_construction: int = 40, ef_search: int = 16) -> faiss.Index:
    index = faiss.IndexHNSWFlat(items.shape[1], m, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = ef_construction
    index.add(items)
    index.hnsw.efSearch = ef_search
    return index


# --- 2. the four recall queues, fanned out on a real thread pool ------------


@dataclass(frozen=True)
class QueueTiming:
    name: str
    median_s: float  # network-call stand-in latency, seconds


# Same three network-bound queues as `core/`'s RECALL_QUEUES, minus two_tower
# (which is real below) -- median latencies carried over so the two files are
# comparable, not because these particular numbers were measured anywhere.
NETWORK_QUEUES: tuple[QueueTiming, ...] = (
    QueueTiming("lexical", median_s=0.007),
    QueueTiming("item_to_item", median_s=0.014),
    QueueTiming("freshness", median_s=0.005),
)


def two_tower_query(index: faiss.Index, query: np.ndarray, k: int) -> tuple[str, float, np.ndarray]:
    start = time.perf_counter()
    _, ids = index.search(query.reshape(1, -1), k)
    elapsed = time.perf_counter() - start
    return "two_tower", elapsed, ids[0]


def network_queue_call(name: str, median_s: float, rng: random.Random, k: int) -> tuple[str, float, np.ndarray]:
    """Stands in for an RPC to a separate recall service -- see module
    docstring point 2. `time.sleep` genuinely blocks this thread while
    releasing the GIL, which is the property that makes it a fair stand-in
    for a blocking network read inside a real thread-pool fan-out."""
    latency = rng.lognormvariate(np.log(median_s), 0.35)
    start = time.perf_counter()
    time.sleep(latency)
    elapsed = time.perf_counter() - start
    ids = np.arange(k)  # placeholder result set; this file does not score recall quality
    return name, elapsed, ids


def fan_out_recall(
    index: faiss.Index, query: np.ndarray, k: int, timeout_ms: float, rng: random.Random
) -> tuple[float, int, int]:
    """Real thread pool, real `wait(timeout=...)`. Returns (latency_s,
    queues_completed, queues_dropped). A queue still running when the timeout
    fires is not cancelled -- its thread finishes on its own time, same as a
    production client that stops waiting on a straggler without necessarily
    tearing down the in-flight call -- but its result is excluded from the
    union, which is what "the slate degrades instead of the request failing"
    means in code."""
    with ThreadPoolExecutor(max_workers=4) as pool:
        start = time.perf_counter()
        futures = [pool.submit(two_tower_query, index, query, k)]
        for q in NETWORK_QUEUES:
            futures.append(pool.submit(network_queue_call, q.name, q.median_s, rng, k))
        done, not_done = wait(futures, timeout=timeout_ms / 1000.0)
        elapsed = time.perf_counter() - start
    return elapsed, len(done), len(not_done)


# --- 3. downstream stages: real NumPy compute, not sampled latency ---------


def pre_rank(rng: np.random.Generator, candidates: np.ndarray, out_k: int) -> tuple[float, np.ndarray]:
    """Linear scorer: one dot product per candidate against a random weight
    vector. Cheap on purpose -- this is the stage that has to touch every
    candidate recall handed it."""
    w = rng.normal(size=candidates.shape[1]).astype("float32")
    start = time.perf_counter()
    scores = candidates @ w
    top = np.argsort(-scores)[:out_k]
    elapsed = time.perf_counter() - start
    return elapsed, top


def fine_rank(rng: np.random.Generator, candidates: np.ndarray, out_k: int) -> tuple[float, np.ndarray]:
    """A small two-layer transform standing in for a heavier model: one
    matmul into a hidden layer, a ReLU, one matmul back down to a score. Not
    a trained model -- random weights -- but the FLOP shape (and therefore
    the relative cost against `pre_rank`) is real, which is the property
    this stage exists to demonstrate."""
    w1 = rng.normal(size=(candidates.shape[1], FINE_RANK_HIDDEN)).astype("float32")
    w2 = rng.normal(size=FINE_RANK_HIDDEN).astype("float32")
    start = time.perf_counter()
    hidden = np.maximum(candidates @ w1, 0.0)
    scores = hidden @ w2
    top = np.argsort(-scores)[:out_k]
    elapsed = time.perf_counter() - start
    return elapsed, top


def value_tree(rng: np.random.Generator, n_items: int) -> float:
    """Weighted sum over a synthetic prediction vector per item -- see
    `05-value-tree`'s `combine_additive` for the version of this that reads
    as a lesson rather than a timing stand-in."""
    preds = rng.uniform(0.0, 1.0, size=(n_items, 4)).astype("float32")
    weights = np.array([0.4, 0.3, 0.2, 0.1], dtype="float32")
    start = time.perf_counter()
    _ = preds @ weights
    return time.perf_counter() - start


def mixing(rng: np.random.Generator, embeddings: np.ndarray, out_k: int) -> float:
    """Greedy top-k with a diversity penalty: pick the best-scoring item,
    then repeatedly pick the best remaining item after subtracting a penalty
    proportional to its similarity to items already chosen. This is a real,
    if small, instance of the "slate value is not the sum of item scores"
    problem `06-mixing` names -- a full beam search over permutations is the
    production version; a greedy pass is the cheapest thing that still has
    to look at pairwise similarity, which is the FLOP shape worth timing."""
    n = embeddings.shape[0]
    base_scores = rng.uniform(0.0, 1.0, size=n).astype("float32")
    start = time.perf_counter()
    chosen: list[int] = []
    remaining = set(range(n))
    penalty = np.zeros(n, dtype="float32")
    for _ in range(min(out_k, n)):
        adjusted = base_scores - penalty
        for idx in chosen:
            adjusted[idx] = -np.inf
        pick = int(np.argmax(adjusted))
        chosen.append(pick)
        remaining.discard(pick)
        sims = embeddings @ embeddings[pick]
        penalty += 0.15 * np.clip(sims, 0.0, None)
    return time.perf_counter() - start


def rules(rng: np.random.Generator, n_items: int) -> float:
    """A boolean mask over declarative constraints -- policy facts, not
    learned scores, applied last so they always have the final word."""
    flags = rng.integers(0, 2, size=(n_items, 3)).astype(bool)
    start = time.perf_counter()
    _ = flags.all(axis=1)
    return time.perf_counter() - start


# --- 4. one full request, and the harness over many of them ------------------


@dataclass
class RealFunnelConfig:
    recall_timeout_ms: float = 25.0
    recall_k_per_queue: int = 750
    prerank_out: int = 300
    finerank_out: int = 50
    catalogue_size: int = 20000
    categories: int = 12


def run_real_request(
    index: faiss.Index, catalogue: np.ndarray, cfg: RealFunnelConfig, np_rng: np.random.Generator, py_rng: random.Random
) -> dict[str, float]:
    query = np_rng.normal(size=EMBED_DIM).astype("float32")
    recall_s, completed, dropped = fan_out_recall(index, query, cfg.recall_k_per_queue, cfg.recall_timeout_ms, py_rng)

    recall_candidates = catalogue[np_rng.integers(0, catalogue.shape[0], size=cfg.recall_k_per_queue * max(completed, 1))]
    prerank_s, prerank_ids = pre_rank(np_rng, recall_candidates, cfg.prerank_out)
    finerank_s, finerank_ids = fine_rank(np_rng, recall_candidates[prerank_ids], cfg.finerank_out)
    value_tree_s = value_tree(np_rng, cfg.finerank_out)
    mixing_s = mixing(np_rng, recall_candidates[prerank_ids][finerank_ids], min(10, cfg.finerank_out))
    rules_s = rules(np_rng, cfg.finerank_out)

    stage_ms = {
        "recall": recall_s * 1000,
        "pre_rank": prerank_s * 1000,
        "fine_rank": finerank_s * 1000,
        "value_tree": value_tree_s * 1000,
        "mixing": mixing_s * 1000,
        "rules": rules_s * 1000,
    }
    stage_ms["_queues_dropped"] = dropped
    return stage_ms


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trials", type=int, default=300)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--recall-timeout-ms", type=float, default=25.0)
    parser.add_argument("--recall-k-per-queue", type=int, default=750)
    parser.add_argument("--prerank-out", type=int, default=300)
    parser.add_argument("--finerank-out", type=int, default=50)
    parser.add_argument("--catalogue-size", type=int, default=20000)
    args = parser.parse_args()

    cfg = RealFunnelConfig(
        recall_timeout_ms=args.recall_timeout_ms,
        recall_k_per_queue=args.recall_k_per_queue,
        prerank_out=args.prerank_out,
        finerank_out=args.finerank_out,
        catalogue_size=args.catalogue_size,
    )

    np_rng = np.random.default_rng(args.seed)
    py_rng = random.Random(args.seed)
    catalogue = build_catalogue(cfg.catalogue_size, cfg.categories, args.seed)
    index = build_ann_index(catalogue)

    print(f"catalogue: {cfg.catalogue_size} items, {EMBED_DIM}-dim vectors (synthetic, illustrative only)")
    print(f"recall timeout: {cfg.recall_timeout_ms} ms, {args.trials} trials\n")

    totals: list[float] = []
    per_stage: dict[str, list[float]] = {}
    total_dropped = 0

    harness_start = time.perf_counter()
    for _ in range(args.trials):
        stage_ms = run_real_request(index, catalogue, cfg, np_rng, py_rng)
        total_dropped += stage_ms.pop("_queues_dropped")
        totals.append(sum(stage_ms.values()))
        for name, ms in stage_ms.items():
            per_stage.setdefault(name, []).append(ms)
    harness_wall_s = time.perf_counter() - harness_start

    totals_arr = np.array(totals)
    stage_p95 = {name: float(np.percentile(vals, 95)) for name, vals in per_stage.items()}
    stage_mean = {name: float(np.mean(vals)) for name, vals in per_stage.items()}

    print(f"end-to-end mean : {totals_arr.mean():7.2f} ms")
    print(f"end-to-end p50  : {np.percentile(totals_arr, 50):7.2f} ms")
    print(f"end-to-end p95  : {np.percentile(totals_arr, 95):7.2f} ms")
    print(f"end-to-end p99  : {np.percentile(totals_arr, 99):7.2f} ms")
    print(f"naive sum of per-stage means : {sum(stage_mean.values()):7.2f} ms")
    print(f"naive sum of per-stage p95s  : {sum(stage_p95.values()):7.2f} ms")
    print(f"avg recall queues dropped to timeout per request: {total_dropped / args.trials:.3f}")
    print("\nper-stage mean / p95 (ms):")
    for name in per_stage:
        print(f"  {name:12s} mean {stage_mean[name]:7.3f}  p95 {stage_p95[name]:7.3f}")
    print(f"\nharness wall-clock for {args.trials} trials: {harness_wall_s:.2f} s")


if __name__ == "__main__":
    main()
