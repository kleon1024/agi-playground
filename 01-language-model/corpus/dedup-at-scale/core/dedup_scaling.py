"""GPU-accelerated dedup at scale: why bucket verification, not hashing,
becomes the bottleneck as corpus size grows.

Mirrors 01-language-model/corpus/core/pipeline.py's
MinHashDeduper (same shingle -> signature -> LSH-band mechanism) and adds one
step that chapter's own dedup loop skips: an explicit exact-Jaccard
verification pass over every pair of documents that land in the same LSH
band. Real corpus-dedup pipelines (Lee et al. 2022; RefinedWeb; NeMo Curator)
run exactly this verification step to throw out the false-positive band
collisions LSH itself does not rule out. It is the step NeMo Curator moves
onto GPU (batched Jaccard over candidate pairs via RAPIDS cuDF, followed by
cuGraph connected components) — never reproduced here; this script only
times the CPU-side cost that verification step imposes as corpus size grows.

Every number below comes from a real run: real synthetic documents, real
Python set operations, timed with time.perf_counter. No GPU is used, and no
GPU speedup is measured -- only the CPU-side bottleneck shift that motivates
reaching for one.
"""

import argparse
import itertools
import random
import time
from collections import defaultdict

_MERSENNE = (1 << 61) - 1
_VOCAB = [f"tok{i}" for i in range(4000)]
_TEMPLATE_LEN = 120
_UNIQUE_LEN = 120
_NGRAM = 5


def shingles(words: list) -> set:
    if len(words) < _NGRAM:
        return {hash(" ".join(words))}
    return {
        hash(" ".join(words[i : i + _NGRAM])) for i in range(len(words) - _NGRAM + 1)
    }


def make_corpus(n: int, cluster_frac: float, rng: random.Random):
    """cluster_frac of the corpus is near-duplicate variants of one fixed
    template (a handful of words swapped -- simulating boilerplate with a
    different header/timestamp); the rest are independent random documents
    with low mutual overlap. The hot cluster's size scales with n, which is
    exactly what makes its bucket's verification cost scale worse than n."""
    template = rng.sample(_VOCAB, _TEMPLATE_LEN)
    n_dupe = int(n * cluster_frac)
    docs = []
    for _ in range(n_dupe):
        words = list(template)
        for _ in range(4):  # small, bounded number of word swaps per variant
            words[rng.randrange(len(words))] = rng.choice(_VOCAB)
        docs.append(words)
    for _ in range(n - n_dupe):
        docs.append(rng.sample(_VOCAB, _UNIQUE_LEN))
    rng.shuffle(docs)
    return docs


class Signer:
    def __init__(self, num_perm: int, bands: int, seed: int):
        assert num_perm % bands == 0
        self.num_perm, self.bands = num_perm, bands
        self.rows = num_perm // bands
        rng = random.Random(seed)
        self.a = [rng.randrange(1, _MERSENNE) for _ in range(num_perm)]
        self.b = [rng.randrange(0, _MERSENNE) for _ in range(num_perm)]

    def signature(self, sh: set) -> tuple:
        return tuple(
            min(((a * h + b) % _MERSENNE) for h in sh) for a, b in zip(self.a, self.b)
        )

    def bands_of(self, sig: tuple):
        for band in range(self.bands):
            yield band, sig[band * self.rows : (band + 1) * self.rows]


def jaccard(a: set, b: set) -> float:
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


def run_once(n: int, cluster_frac: float, num_perm: int, bands: int, seed: int, threshold: float):
    rng = random.Random(seed)
    docs = make_corpus(n, cluster_frac, rng)

    t0 = time.perf_counter()
    shingle_sets = [shingles(d) for d in docs]
    signer = Signer(num_perm, bands, seed)
    signatures = [signer.signature(sh) for sh in shingle_sets]
    hash_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    buckets = defaultdict(list)
    for doc_id, sig in enumerate(signatures):
        for band, key in signer.bands_of(sig):
            buckets[(band, key)].append(doc_id)
    index_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    pairs_compared = 0
    true_near_dupes = 0
    seen_pairs = set()
    max_bucket = 0
    for members in buckets.values():
        k = len(members)
        max_bucket = max(max_bucket, k)
        if k < 2:
            continue
        for i in range(k):
            for j in range(i + 1, k):
                p = (members[i], members[j]) if members[i] < members[j] else (members[j], members[i])
                if p in seen_pairs:
                    continue
                seen_pairs.add(p)
                pairs_compared += 1
                if jaccard(shingle_sets[p[0]], shingle_sets[p[1]]) >= threshold:
                    true_near_dupes += 1
    verify_time = time.perf_counter() - t0

    return {
        "n": n,
        "hash_time": hash_time,
        "index_time": index_time,
        "verify_time": verify_time,
        "pairs_compared": pairs_compared,
        "true_near_dupes": true_near_dupes,
        "max_bucket": max_bucket,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=str, default="1000,4000,16000")
    ap.add_argument("--cluster-frac", type=float, default=0.10)
    ap.add_argument("--num-perm", type=int, default=64)
    ap.add_argument("--bands", type=int, default=16)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    sizes = [int(s) for s in args.sizes.split(",")]
    print(f"cluster_frac={args.cluster_frac} num_perm={args.num_perm} bands={args.bands}")
    print(
        f"{'n':>8} {'hash_s':>9} {'hash_us/doc':>12} {'verify_s':>10} "
        f"{'pairs':>10} {'max_bucket':>11} {'near_dupes':>11}"
    )
    rows = []
    for n in sizes:
        r = run_once(n, args.cluster_frac, args.num_perm, args.bands, args.seed, args.threshold)
        rows.append(r)
        print(
            f"{r['n']:>8} {r['hash_time']:>9.4f} "
            f"{r['hash_time'] / r['n'] * 1e6:>12.2f} {r['verify_time']:>10.4f} "
            f"{r['pairs_compared']:>10} {r['max_bucket']:>11} {r['true_near_dupes']:>11}"
        )

    print()
    print("ratio of consecutive sizes (n growth vs verify_time growth):")
    for prev, cur in itertools.pairwise(rows):
        n_ratio = cur["n"] / prev["n"]
        v_ratio = cur["verify_time"] / prev["verify_time"] if prev["verify_time"] > 0 else float("inf")
        h_ratio = cur["hash_time"] / prev["hash_time"] if prev["hash_time"] > 0 else float("inf")
        print(
            f"  n x{n_ratio:.1f}: hash_time x{h_ratio:.2f}, verify_time x{v_ratio:.2f}"
        )


if __name__ == "__main__":
    main()
