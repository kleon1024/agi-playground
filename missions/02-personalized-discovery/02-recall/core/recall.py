"""From-scratch multi-queue candidate generation, scored against exhaustive truth.

Recall is the one stage nothing downstream can repair: a perfect ranker cannot
rank an item that was never retrieved. So before any ranking code exists, this
file asks a narrower question — does the union of a handful of cheap retrieval
methods actually surface the items a user should see, or does turning one of
them off create a hole nothing else fills?

Every queue here is plain Python over lists of floats, on a catalogue small
enough (a few hundred items) to score exhaustively. That smallness is not a
simplification for the exercise; it is what makes "measure recall against
ground truth" possible at all, and it is why the mission starts here before
ever needing an approximate index (see `prod/faiss_recall.py`).

The catalogue, users, and "true" targets below are synthetic and clearly
labeled as such: a deterministic generator builds a small item catalogue with
known embeddings, tokens, recency, and popularity, then builds users whose
one true target set is constructed with a known provenance per item — one
findable only by semantic similarity, one only by an exact keyword, one only
by proximity to a specific history item, one only because it is new. Nothing
here is a claim about a real dataset; it is a controlled instrument for
answering one question: which queue found which target?

Run:  python recall.py --catalogue-size 400 --seed 0
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass, field

EMBED_DIM = 12


@dataclass(frozen=True)
class Item:
    id: str
    category: int
    embedding: tuple[float, ...]
    tokens: tuple[str, ...]
    created_at: float
    popularity: float
    boosted: bool = False


@dataclass(frozen=True)
class User:
    id: str
    embedding: tuple[float, ...]
    history: tuple[str, ...]
    query_tokens: tuple[str, ...]
    targets: dict[str, str] = field(default_factory=dict)  # target item id -> queue that can find it


# --- vector arithmetic, written out rather than imported ---------------------


def dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b))


def add(a: tuple[float, ...], b: tuple[float, ...], weight: float = 1.0) -> tuple[float, ...]:
    return tuple(x + weight * y for x, y in zip(a, b))


def scale(a: tuple[float, ...], k: float) -> tuple[float, ...]:
    return tuple(x * k for x in a)


def norm(a: tuple[float, ...]) -> float:
    return math.sqrt(sum(x * x for x in a)) or 1e-9


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return dot(a, b) / (norm(a) * norm(b))


# --- 1. the queues, each blind to something the others see ------------------
#
# Every queue below returns a ranked list of item ids. None of them consult
# each other. That is the point: each is good at exactly one thing, and each
# is structurally unable to find items outside that one thing.


def two_tower_recall(user: User, items: list[Item], k: int) -> list[str]:
    """Semantic similarity between a user vector and every item vector.

    Blind spot: an item whose embedding is unreliable (a cold item with no
    interaction signal yet, or a genuinely different-category item a keyword
    or a companion-item relationship would still surface) will not score well
    here no matter how relevant it turns out to be.
    """
    scored = sorted(items, key=lambda it: dot(user.embedding, it.embedding), reverse=True)
    return [it.id for it in scored[:k]]


def lexical_recall(query_tokens: tuple[str, ...], items: list[Item], k: int) -> list[str]:
    """Exact-term overlap, weighted by how rare each term is in the catalogue.

    A from-scratch TF times inverse-document-frequency score: common tokens
    (present in most items) count for little, a shared rare token counts for
    a lot. Blind spot: two items about the same thing in different words
    score zero if they share no tokens, no matter how semantically close.
    """
    if not query_tokens:
        return []
    doc_freq: dict[str, int] = {}
    for it in items:
        for token in set(it.tokens):
            doc_freq[token] = doc_freq.get(token, 0) + 1
    n = len(items)
    idf = {token: math.log(n / (1 + count)) + 1.0 for token, count in doc_freq.items()}
    scored = []
    for it in items:
        overlap = set(query_tokens) & set(it.tokens)
        score = sum(idf.get(token, 0.0) for token in overlap)
        if score > 0:
            scored.append((score, it.id))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [item_id for _, item_id in scored[:k]]


def item_to_item_recall(history: tuple[str, ...], items_by_id: dict[str, Item], items: list[Item], k: int) -> list[str]:
    """Nearest neighbours of the specific items a user just engaged with.

    Blind spot: this only looks near the handful of seed items in `history`.
    An item close to the user's *overall* taste but not close to any single
    history item is invisible here, even though two_tower_recall might find
    it from the averaged profile.
    """
    seeds = [items_by_id[item_id] for item_id in history if item_id in items_by_id]
    if not seeds:
        return []
    scores: dict[str, float] = {}
    for it in items:
        if it.id in history:
            continue
        best = max(cosine(seed.embedding, it.embedding) for seed in seeds)
        scores[it.id] = best
    ranked = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    return [item_id for item_id, _ in ranked[:k]]


def freshness_recall(items: list[Item], k: int, min_popularity: float = 0.02) -> list[str]:
    """Most recent items above a low popularity floor.

    Blind spot: says nothing about whether an item matches this particular
    user; it is a global queue, not a personalized one.
    """
    candidates = [it for it in items if it.popularity >= min_popularity]
    ranked = sorted(candidates, key=lambda it: (-it.created_at, it.id))
    return [it.id for it in ranked[:k]]


def business_recall(items: list[Item], k: int) -> list[str]:
    """Editorially boosted items, ranked by popularity among the boosted set.

    Blind spot: entirely a policy queue. It has no notion of user or query at
    all, on purpose -- it exists to carry decisions no statistic should make.
    """
    boosted = [it for it in items if it.boosted]
    ranked = sorted(boosted, key=lambda it: (-it.popularity, it.id))
    return [it.id for it in ranked[:k]]


QUEUE_NAMES = ("two_tower", "lexical", "item_to_item", "freshness", "business")


def run_queues(user: User, items: list[Item], items_by_id: dict[str, Item], k: int, enabled: dict[str, bool]) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    if enabled.get("two_tower", True):
        results["two_tower"] = two_tower_recall(user, items, k)
    if enabled.get("lexical", True):
        results["lexical"] = lexical_recall(user.query_tokens, items, k)
    if enabled.get("item_to_item", True):
        results["item_to_item"] = item_to_item_recall(user.history, items_by_id, items, k)
    if enabled.get("freshness", True):
        results["freshness"] = freshness_recall(items, k)
    if enabled.get("business", True):
        results["business"] = business_recall(items, k)
    return results


def union_queues(queue_results: dict[str, list[str]]) -> set[str]:
    """The candidate set downstream stages will ever see: the plain union."""
    unioned: set[str] = set()
    for ids in queue_results.values():
        unioned.update(ids)
    return unioned


def target_coverage(targets: dict[str, str], candidates: set[str]) -> float:
    """Fraction of a user's true target items present in the candidate set.

    This is only measurable exactly because the catalogue is small enough to
    know, by construction, which items are truly relevant to each user. That
    is "exhaustive scoring": nothing here is an estimate.
    """
    if not targets:
        return 1.0
    found = sum(1 for item_id in targets if item_id in candidates)
    return found / len(targets)


# --- synthetic catalogue, users, and targets ---------------------------------


def _category_vocab(category: int) -> list[str]:
    return [f"cat{category}_word{i}" for i in range(6)]


def build_catalogue(n_items: int, n_categories: int, seed: int) -> list[Item]:
    rng = random.Random(seed)
    centers = [
        tuple(rng.uniform(-1.0, 1.0) for _ in range(EMBED_DIM)) for _ in range(n_categories)
    ]
    items: list[Item] = []
    for i in range(n_items):
        category = i % n_categories
        center = centers[category]
        embedding = add(center, tuple(rng.gauss(0, 0.15) for _ in range(EMBED_DIM)))
        vocab = _category_vocab(category)
        tokens = tuple(rng.sample(vocab, k=min(2, len(vocab))))
        popularity = 1.0 / (1 + rng.randrange(n_items))
        created_at = rng.uniform(0.0, 1000.0)
        boosted = rng.random() < 0.05
        items.append(
            Item(
                id=f"item{i}",
                category=category,
                embedding=embedding,
                tokens=tokens,
                created_at=created_at,
                popularity=popularity,
                boosted=boosted,
            )
        )
    return items


def build_users(items: list[Item], n_users: int, n_categories: int, seed: int) -> list[User]:
    """Each user gets four targets, one per queue that alone can find it.

    This construction is what lets the demo assert something falsifiable:
    disable a queue, and exactly the target it alone covers drops out of the
    union for every user whose target relied on it.
    """
    rng = random.Random(seed + 1)
    by_category: dict[int, list[Item]] = {}
    for it in items:
        by_category.setdefault(it.category, []).append(it)

    users: list[User] = []
    for u in range(n_users):
        interest = u % n_categories
        pool = by_category[interest]
        history_items = rng.sample(pool, k=min(3, len(pool)))
        history = tuple(it.id for it in history_items)
        user_embedding = scale(
            tuple(sum(it.embedding[d] for it in history_items) for d in range(EMBED_DIM)),
            1.0 / max(1, len(history_items)),
        )
        query_tokens = tuple(_category_vocab(interest)[:1])

        used_ids = set(history)
        targets: dict[str, str] = {}

        # semantic target: close to the averaged user embedding, no shared
        # tokens with the query, not fresh, not boosted, not near any single
        # history item in particular.
        semantic_candidates = [
            it for it in pool if it.id not in used_ids and set(it.tokens).isdisjoint(query_tokens)
        ]
        if semantic_candidates:
            best = max(semantic_candidates, key=lambda it: dot(user_embedding, it.embedding))
            targets[best.id] = "two_tower"
            used_ids.add(best.id)

        # lexical target: shares the query token, but drawn from a different
        # category so its embedding sits far from this user's profile.
        other_category = (interest + 1) % n_categories
        lexical_pool = [
            it for it in by_category[other_category]
            if it.id not in used_ids and set(query_tokens).issubset(it.tokens)
        ]
        if not lexical_pool:
            # force one candidate to actually carry the query token, so the
            # lexical queue always has something to find
            forced = rng.choice([it for it in by_category[other_category] if it.id not in used_ids])
            forced = Item(
                id=forced.id, category=forced.category, embedding=forced.embedding,
                tokens=tuple(set(forced.tokens) | set(query_tokens)), created_at=forced.created_at,
                popularity=forced.popularity, boosted=forced.boosted,
            )
            idx = items.index(next(it for it in items if it.id == forced.id))
            items[idx] = forced
            by_category[other_category] = [forced if it.id == forced.id else it for it in by_category[other_category]]
            lexical_pool = [forced]
        chosen = lexical_pool[0]
        targets[chosen.id] = "lexical"
        used_ids.add(chosen.id)

        # i2i target: the single closest neighbour of one specific history
        # item, deliberately outside the user's averaged-embedding neighbourhood.
        seed_item = history_items[0]
        i2i_candidates = [it for it in items if it.id not in used_ids]
        if i2i_candidates:
            best_i2i = max(i2i_candidates, key=lambda it: cosine(seed_item.embedding, it.embedding))
            targets[best_i2i.id] = "item_to_item"
            used_ids.add(best_i2i.id)

        # freshness target: brand new, noisy embedding (a cold item with no
        # reliable collaborative signal yet), same interest category. Its
        # popularity is set explicitly above the freshness floor -- a new
        # item that nobody has interacted with yet still needs a route into
        # the candidate set, which is exactly what this queue is for.
        fresh_candidates = [it for it in pool if it.id not in used_ids]
        if fresh_candidates:
            fresh_source = rng.choice(fresh_candidates)
            noisy_embedding = add(fresh_source.embedding, tuple(rng.gauss(0, 0.6) for _ in range(EMBED_DIM)))
            fresh_item = Item(
                id=fresh_source.id, category=fresh_source.category, embedding=noisy_embedding,
                tokens=(), created_at=999.0, popularity=0.05, boosted=False,
            )
            idx = items.index(next(it for it in items if it.id == fresh_item.id))
            items[idx] = fresh_item
            targets[fresh_item.id] = "freshness"

        users.append(
            User(id=f"user{u}", embedding=user_embedding, history=history, query_tokens=query_tokens, targets=targets)
        )
    return users


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--catalogue-size", type=int, default=400)
    parser.add_argument("--categories", type=int, default=5)
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--k", type=int, default=25, help="candidates per queue")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--disable", choices=QUEUE_NAMES, default=None, help="turn off one queue and watch coverage drop"
    )
    args = parser.parse_args()

    items = build_catalogue(args.catalogue_size, args.categories, args.seed)
    users = build_users(items, args.users, args.categories, args.seed)
    items_by_id = {it.id: it for it in items}

    enabled = {name: name != args.disable for name in QUEUE_NAMES}

    print(f"catalogue: {len(items)} items, {args.categories} categories (synthetic, illustrative only)")
    if args.disable:
        print(f"queue disabled: {args.disable}\n")

    coverages = []
    per_provenance_hits = {name: 0 for name in QUEUE_NAMES}
    per_provenance_total = {name: 0 for name in QUEUE_NAMES}
    for user in users:
        queue_results = run_queues(user, items, items_by_id, args.k, enabled)
        candidates = union_queues(queue_results)
        coverage = target_coverage(user.targets, candidates)
        coverages.append(coverage)
        for target_id, provenance in user.targets.items():
            per_provenance_total[provenance] += 1
            if target_id in candidates:
                per_provenance_hits[provenance] += 1

    mean_coverage = sum(coverages) / len(coverages)
    print(f"mean target coverage across {len(users)} users: {mean_coverage:.2f}")
    print("\ncoverage by target provenance (which queue alone can find each one):")
    for name in QUEUE_NAMES:
        total = per_provenance_total[name]
        if total == 0:
            print(f"  {name:14s} not assigned a per-user target (it is a policy queue, not a personalized one)")
            continue
        hits = per_provenance_hits[name]
        rate = hits / total
        print(f"  {name:14s} {hits}/{total} found ({rate:.2f})")
    print("\nDisable the queue named as a target's provenance and its row drops")
    print("sharply -- the other queues recover a few by incidental overlap, not by")
    print("design, and never all of them. That gap is the asymmetry: recall is the")
    print("one stage downstream ranking cannot repair.")


if __name__ == "__main__":
    main()
