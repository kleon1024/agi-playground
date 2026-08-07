"""From-scratch content labelling and cold-item coverage harness.

Stage 00 produced a time-split interaction log and a popularity floor. Stage
02 (recall) builds a two-tower embedding queue and an item-to-item queue
directly out of that log — which means, by construction, an item with zero
rows in the log has no training signal for either queue and cannot be
retrieved by them, however good the model. Content is the only signal that
exists before the first interaction. This file makes that claim measurable:

1. build a synthetic catalogue of items with short text descriptions, where
   popularity, text richness, and interaction count are deliberately tied
   together — the same way a newly uploaded item is simultaneously the one
   with the fewest clicks and the thinnest metadata;
2. label every item with a from-scratch pipeline: exact-keyword rules first,
   falling back to nearest-centroid matching over a hashed bag-of-words
   embedding for anything the rules miss;
3. sweep the labeller's confidence threshold and, at each point, measure
   catalogue coverage (behavior queue union content queue) split out for the
   cold subset specifically, plus label accuracy among whatever got labelled.

The point the sweep exists to make: a threshold that only labels what it is
sure about buys accuracy by leaving the tail unlabelled, and the tail is
exactly the cold items the behavior queues could never reach anyway.

Everything here is pure standard library (`zlib` supplies a deterministic
hash for the embedding; no third-party dependency, no `numpy`).

Run:

    python content_understanding.py --catalogue-size 300 --seed 0
"""

from __future__ import annotations

import argparse
import bisect
import itertools
import math
import random
import zlib
from collections import Counter, defaultdict
from dataclasses import dataclass

# --- 1. Taxonomy -------------------------------------------------------------
#
# A hierarchy, not a flat label set. Every leaf carries its parent domain,
# which is what lets a downstream diversity constraint say "no more than two
# items from `electronics` in this slate" directly. A flat label set (just
# the seven leaves below, with no domain field) cannot express that rule
# without a second lookup table living somewhere else — and that table is
# itself an undeclared piece of the taxonomy, just not one anybody can see
# in the labels.

TAXONOMY: dict[str, list[str]] = {
    "electronics": ["phones", "laptops", "audio"],
    "home": ["kitchen", "furniture"],
    "media": ["books", "movies"],
}

# One keyword deliberately shared ("battery") between phones and laptops:
# real catalogues have genuine cross-category ambiguity, not just noise.
CATEGORY_KEYWORDS: dict[tuple[str, str], list[str]] = {
    ("electronics", "phones"): ["smartphone", "touchscreen", "camera", "battery", "5g"],
    ("electronics", "laptops"): ["laptop", "keyboard", "processor", "battery", "trackpad"],
    ("electronics", "audio"): ["headphones", "speaker", "bluetooth", "bass", "microphone"],
    ("home", "kitchen"): ["cookware", "blender", "recipe", "nonstick", "simmer"],
    ("home", "furniture"): ["sofa", "armchair", "hardwood", "upholstery", "cushion"],
    ("media", "books"): ["novel", "author", "chapter", "paperback", "hardcover"],
    ("media", "movies"): ["movie", "director", "cinema", "screening", "runtime"],
}

# A synonym for exactly one keyword per leaf, deliberately absent from
# CATEGORY_KEYWORDS above. A thin item that draws one of these instead of its
# category's registered keyword produces zero rule hits — the rule labeller
# cannot see a word it was never told about, and a hashed bag-of-words
# embedding cannot either, because hashing preserves no meaning between two
# different tokens. That gap is exactly what a pretrained embedding model
# (see prod/) is for.
SYNONYMS: dict[str, str] = {
    "smartphone": "handset",
    "laptop": "notebook",
    "headphones": "earbuds",
    "cookware": "cookset",
    "sofa": "couch",
    "novel": "paperback",
    "movie": "flick",
}

FILLER_WORDS = ["new", "great", "shop", "deal", "available", "today", "listing", "popular"]


def leaf_categories() -> list[tuple[str, str]]:
    return [(domain, sub) for domain, subs in TAXONOMY.items() for sub in subs]


# --- 2. Catalogue: popularity, text richness, and coldness are one variable -


@dataclass(frozen=True)
class Item:
    id: str
    domain: str
    subcategory: str
    text: str
    rank: int  # 0 = most popular, tied to both interaction weight and text richness
    thin: bool


def _make_text(domain: str, subcategory: str, thin: bool, rand: random.Random) -> str:
    keywords = list(CATEGORY_KEYWORDS[(domain, subcategory)])
    n_keywords = 1 if thin else rand.randint(3, 5)
    chosen = rand.sample(keywords, min(n_keywords, len(keywords)))
    if thin and rand.random() < 0.6:
        # Swap the one keyword this item has for its off-list synonym --
        # simulating a real but unregistered word choice, not noise.
        word = chosen[0]
        chosen = [SYNONYMS.get(word, word)]
    filler = rand.sample(FILLER_WORDS, 3)
    words = chosen + filler
    rand.shuffle(words)
    return " ".join(words)


def build_catalogue(n_items: int, seed: int, established_fraction: float = 0.6) -> list[Item]:
    """Assign each item a true leaf, a popularity rank, and text tied to both.

    `established_fraction` is a tuning knob, disclosed here rather than
    hidden: 0.6 was chosen so the demo catalogue lands in a regime with a
    substantial cold tail (see the module docstring's numbers below), not
    because it is a realistic estimate of any platform's actual mix.
    """
    rand = random.Random(seed)
    leaves = leaf_categories()
    order = list(range(n_items))
    rand.shuffle(order)
    cutoff = int(n_items * established_fraction)

    items: list[Item] = []
    for position, idx in enumerate(order):
        domain, subcategory = leaves[idx % len(leaves)]
        established = position < cutoff
        thin = (not established) and rand.random() < 0.85 or (established and rand.random() < 0.1)
        text = _make_text(domain, subcategory, thin, rand)
        items.append(Item(id=f"item-{idx:04d}", domain=domain, subcategory=subcategory, text=text, rank=position, thin=thin))
    items.sort(key=lambda it: it.id)
    return items


def build_interactions(items: list[Item], seed: int, n_users: int, interactions_per_user: int, zipf_s: float) -> Counter[str]:
    """Sample interactions with probability proportional to `1 / (rank + 1) ** zipf_s`.

    An item's rank was set in `build_catalogue` and drives both its text
    richness and its interaction weight here, on purpose: a newly launched
    item is simultaneously the one with the thinnest metadata and the
    fewest clicks, not two independent coincidences.
    """
    rand = random.Random(seed)
    weights = [1.0 / ((it.rank + 1) ** zipf_s) for it in items]
    cumulative = list(itertools.accumulate(weights))
    total = cumulative[-1]

    counts: Counter[str] = Counter()
    for _ in range(n_users * interactions_per_user):
        draw = rand.random() * total
        idx = bisect.bisect_left(cumulative, draw)
        counts[items[idx].id] += 1
    return counts


# --- 3. Content embedding: the hashing trick, entirely from scratch --------


def hashed_embedding(text: str, dim: int = 24) -> tuple[float, ...]:
    """A deterministic bag-of-words embedding via feature hashing.

    Each word hashes (via `zlib.crc32`, which is stable across runs and
    interpreters, unlike Python's built-in `hash()` for strings) into one of
    `dim` buckets with a pseudo-random sign, and the result is L2-normalized
    so cosine similarity is a plain dot product. This is a real, minimal
    version of the "hashing trick" (Weinberger et al., 2009) used to avoid
    keeping a growing vocabulary table — it has no notion of word meaning at
    all, which is the point made in the SYNONYMS comment above.
    """
    vec = [0.0] * dim
    for word in text.split():
        digest = zlib.crc32(word.encode("utf-8"))
        bucket = digest % dim
        sign = 1.0 if (digest // dim) % 2 == 0 else -1.0
        vec[bucket] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return tuple(v / norm for v in vec)


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    # Both inputs are already L2-normalized by hashed_embedding /
    # average_and_normalize, so a plain dot product is the cosine similarity.
    return sum(x * y for x, y in zip(a, b))


# --- 4. Labelling: rules first, nearest-centroid for whatever they miss ----


Leaf = tuple[str, str]


@dataclass(frozen=True)
class LabelResult:
    leaf: Leaf | None
    confidence: float
    method: str  # "rule", "centroid", or "none"


def rule_label(text: str) -> tuple[Leaf | None, float]:
    """Score every leaf by the fraction of its registered keywords present.

    Confidence is the winning leaf's hit rate, not a margin over the
    runner-up: a rich item that mentions four of five of its category's
    keywords scores high; a thin item with one matching keyword out of five
    scores low, on purpose, because that is the honest confidence a single
    keyword hit deserves.
    """
    words = set(text.split())
    scores: dict[Leaf, float] = {}
    for leaf, keywords in CATEGORY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in words)
        if hits:
            scores[leaf] = hits / len(keywords)
    if not scores:
        return None, 0.0
    best = max(scores, key=scores.get)
    return best, scores[best]


def build_centroids(
    items: list[Item], embeddings: dict[str, tuple[float, ...]], seed_confidence: float
) -> tuple[dict[Leaf, tuple[float, ...]], int]:
    """Bootstrap one centroid per leaf from items the rule labeller was confident about.

    This is not a VLM and not a trained classifier — it is the cheapest
    possible stand-in for "a lightweight classifier fit on high-confidence
    seed labels," built from the same rule pass rather than a second
    annotation pass. Returns the centroids and how many items seeded them,
    so the caller can report the seed set size honestly.
    """
    groups: dict[Leaf, list[tuple[float, ...]]] = defaultdict(list)
    for item in items:
        leaf, confidence = rule_label(item.text)
        if leaf is not None and confidence >= seed_confidence:
            groups[leaf].append(embeddings[item.id])

    centroids: dict[Leaf, tuple[float, ...]] = {}
    for leaf, vectors in groups.items():
        dim = len(vectors[0])
        summed = [sum(v[d] for v in vectors) for d in range(dim)]
        norm = math.sqrt(sum(s * s for s in summed)) or 1.0
        centroids[leaf] = tuple(s / norm for s in summed)
    seed_count = sum(len(vectors) for vectors in groups.values())
    return centroids, seed_count


def centroid_label(embedding: tuple[float, ...], centroids: dict[Leaf, tuple[float, ...]]) -> tuple[Leaf | None, float]:
    if not centroids:
        return None, 0.0
    similarities = {leaf: cosine(embedding, centroid) for leaf, centroid in centroids.items()}
    best = max(similarities, key=similarities.get)
    return best, max(0.0, similarities[best])


def label_item(item: Item, embedding: tuple[float, ...], centroids: dict[Leaf, tuple[float, ...]]) -> LabelResult:
    """Rule first; nearest-centroid only for whatever the rule pass could not touch at all."""
    leaf, confidence = rule_label(item.text)
    if leaf is not None:
        return LabelResult(leaf, confidence, "rule")
    leaf, confidence = centroid_label(embedding, centroids)
    if leaf is not None:
        return LabelResult(leaf, confidence, "centroid")
    return LabelResult(None, 0.0, "none")


# --- 5. Coverage: the quantity this whole stage exists to make measurable -


def compute_coverage(
    items: list[Item],
    interaction_counts: Counter[str],
    labels: dict[str, LabelResult],
    threshold: float,
) -> dict[str, float]:
    total = len(items)
    behavior_reachable = {it.id for it in items if interaction_counts.get(it.id, 0) > 0}
    content_reachable = {it.id for it in items if labels[it.id].confidence >= threshold}
    union_reachable = behavior_reachable | content_reachable

    cold_items = [it for it in items if it.id not in behavior_reachable]
    cold_content_reachable = [it for it in cold_items if it.id in content_reachable]

    labelled = [it for it in items if it.id in content_reachable]
    correct = sum(1 for it in labelled if labels[it.id].leaf == (it.domain, it.subcategory))

    return {
        "threshold": threshold,
        "catalogue_coverage": len(union_reachable) / total,
        "behavior_only_coverage": len(behavior_reachable) / total,
        "content_labelled_frac": len(content_reachable) / total,
        "label_accuracy": (correct / len(labelled)) if labelled else float("nan"),
        "n_cold": len(cold_items),
        "cold_coverage": (len(cold_content_reachable) / len(cold_items)) if cold_items else float("nan"),
    }


# --- 6. CLI ------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--catalogue-size", type=int, default=300)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n-users", type=int, default=150)
    parser.add_argument("--interactions-per-user", type=int, default=10)
    parser.add_argument("--zipf-s", type=float, default=1.2)
    parser.add_argument("--seed-confidence", type=float, default=0.5, help="rule confidence needed to seed a centroid")
    parser.add_argument(
        "--thresholds",
        type=str,
        default="0.0,0.2,0.35,0.5,0.65,0.8",
        help="comma-separated content-labeller confidence thresholds to sweep",
    )
    args = parser.parse_args()

    items = build_catalogue(args.catalogue_size, args.seed)
    interaction_counts = build_interactions(items, args.seed, args.n_users, args.interactions_per_user, args.zipf_s)
    embeddings = {it.id: hashed_embedding(it.text) for it in items}
    centroids, seed_count = build_centroids(items, embeddings, args.seed_confidence)
    labels = {it.id: label_item(it, embeddings[it.id], centroids) for it in items}
    via_centroid = sum(1 for l in labels.values() if l.method == "centroid")

    n_cold = sum(1 for it in items if interaction_counts.get(it.id, 0) == 0)
    print(f"catalogue: {len(items)} items, {n_cold} with zero interactions ({n_cold / len(items):.0%} cold)")
    print(f"centroids seeded from {seed_count} rule-confident items across {len(centroids)}/{len(leaf_categories())} leaves")
    print(f"{via_centroid} items had zero rule hits and fell back to nearest-centroid matching")
    print()
    header = f"{'threshold':>9} {'union_cov':>9} {'behavior_only':>13} {'labelled_frac':>13} {'label_acc':>9} {'cold_cov':>9}"
    print(header)
    print("-" * len(header))
    for threshold in (float(t) for t in args.thresholds.split(",")):
        row = compute_coverage(items, interaction_counts, labels, threshold)
        print(
            f"{row['threshold']:>9.2f} {row['catalogue_coverage']:>9.0%} {row['behavior_only_coverage']:>13.0%} "
            f"{row['content_labelled_frac']:>13.0%} {row['label_accuracy']:>9.0%} {row['cold_coverage']:>9.0%}"
        )
    print()
    print("behavior_only_coverage is the same at every threshold: the behavior queue's reach does not")
    print("depend on the labeller at all. cold_cov is 0% only if the content queue is removed entirely --")
    print("that is the coverage a fine-ranker downstream would have for the cold slice with no stage 01.")


if __name__ == "__main__":
    main()
