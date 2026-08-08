"""How do you find the failure cases the report demands?

Stage 09 treats a report with no failure cases as one that has not
looked. This chapter is the looking: the workflow that turns an aggregate
pass into concrete, measured cases — slice, drill, hypothesize, verify.

The simulation runs 15,000 synthetic users through a recommendation loop
with two known defects baked in:

1. A cold-start eligibility step: users with fewer than 5 interactions get
   pure popularity; users at exactly 5 get the model, but the model's
   personalization only "lands" 55% of the time at that point (a noisy
   cluster estimate), so the boundary group sits between popularity and
   the trusted cohort.
2. Rare-category recall starvation: the recall stage caps candidate pools
   by category size (head 200, mid 60, tail 10), so tail-category users
   get a popularity-shaped list even when the ranker is right about their
   taste.

The drill-down measures: aggregate nDCG@10 for the candidate and both
baselines, per-slice means, the concrete bottom cases, and the mechanism
counts that confirm the two hypotheses. Deterministic (seeded stdlib RNG,
no third-party code).

Usage:
    uv run python core/find_the_case.py
"""

from __future__ import annotations

import math
import random

SEED = 7
N_USERS = 15_000
N_ITEMS = 3_000
CATS = [("head", 1_800, 200, 0.60), ("mid", 900, 60, 0.30), ("tail", 300, 10, 0.10)]
# (name, item count, recall-pool cap, user share)
K = 10


def ndcg10(ranked: list[int], liked: set[int]) -> float:
    """Binary-gain nDCG@10. An item contributes rel/log2(rank+2)."""
    dcg = sum(1.0 / math.log2(i + 2) for i, item in enumerate(ranked[:K])
              if item in liked)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(K, len(liked))))
    return dcg / ideal if ideal > 0 else 0.0


def main() -> None:
    rng = random.Random(SEED)

    # Items with a real popularity score: a category base plus noise, so
    # the global top of the list is head items and tail items sink.
    cat_base = {"head": 3.0, "mid": 2.0, "tail": 1.0}
    items = []
    for cat, n_cat, _, _ in CATS:
        for _ in range(n_cat):
            items.append({"id": len(items), "cat": cat,
                          "cluster": rng.randrange(20),
                          "pop": cat_base[cat] + rng.random()})
    pop_order = [it["id"] for it in sorted(items, key=lambda it: -it["pop"])]
    pop_rank = {item: r for r, item in enumerate(pop_order)}
    pool_cap = {cat: cap for cat, _, cap, _ in CATS}
    cat_items_by_cat = {
        cat: [it["id"] for it in sorted(
            (it for it in items if it["cat"] == cat),
            key=lambda it: -it["pop"])]
        for cat, _, _, _ in CATS
    }

    def interaction_count(rng: random.Random) -> int:
        r = rng.random()
        if r < 0.22:
            return rng.randrange(5)          # cold: 0-4
        if r < 0.30:
            return 5                          # the eligibility boundary
        return 6 + min(int(rng.expovariate(1.0 / 12.0)), 44)

    def p_personalization_lands(n: int) -> float:
        if n < 5:
            return 0.0
        if n == 5:
            return 0.65
        if n <= 10:
            return 0.82
        return 0.95

    users = []
    for u in range(N_USERS):
        n = interaction_count(rng)
        pref = rng.choices(["head", "mid", "tail"], [0.60, 0.30, 0.10])[0]
        cluster = rng.randrange(20)
        # Liked set: drawn from the same top-200 pool the candidate can
        # see, so a landed personalized list can actually find them;
        # cluster items are much more likely to be liked, and a few
        # global blockbusters are liked by everyone, so the popularity
        # baseline is never exactly zero.
        pool = cat_items_by_cat[pref][:200]
        liked = set()
        for i in pool:
            if items[i]["cluster"] == cluster and rng.random() < 0.55 or \
                    rng.random() < 0.08:
                liked.add(i)
        for i in pop_order[:200]:
            if rng.random() < 0.02:
                liked.add(i)
        # Clicks: 80% from liked, 20% from global popularity (noise).
        n_clicks = max(1, min(n, int(0.5 * len(liked)) + 1))
        n_real = int(0.8 * n_clicks)
        clicks = rng.sample(sorted(liked), k=min(n_real, len(liked)))
        clicks += rng.sample(pop_order[:300], k=n_clicks - len(clicks))
        lands = rng.random() < p_personalization_lands(n)
        users.append({
            "id": u, "n": n, "pref": pref, "cluster": cluster,
            "liked": liked, "clicks": clicks, "lands": lands,
        })

    def popular_list() -> list[int]:
        return pop_order[:K]

    # Item-item co-occurrence: how often two items share a clicking user.
    cooc: dict[int, dict[int, int]] = {i: {} for i in range(N_ITEMS)}
    for u in users:
        cs = sorted(set(u["clicks"]))
        for a in range(len(cs)):
            for b in range(a + 1, len(cs)):
                cooc[cs[a]][cs[b]] = cooc[cs[a]].get(cs[b], 0) + 1
                cooc[cs[b]][cs[a]] = cooc[cs[b]].get(cs[a], 0) + 1

    def cf_list(u: dict) -> list[int]:
        """Item-item CF: items co-clicked with the user's own clicks."""
        if len(u["clicks"]) < 3:
            return popular_list()
        scores: dict[int, float] = {}
        for c in u["clicks"]:
            for item, w in cooc[c].items():
                scores[item] = scores.get(item, 0.0) + w
        ranked = sorted(scores, key=lambda i: (-scores[i], pop_rank[i]))
        return ranked[:K] if ranked else popular_list()

    def candidate_list(u: dict) -> list[int]:
        if not u["lands"]:
            return popular_list()
        pool_cat = u["pref"]
        pool = cat_items_by_cat[pool_cat][:pool_cap[pool_cat]]
        pool.sort(key=lambda i: (0 if items[i]["cluster"] == u["cluster"] else 1,
                                 pop_rank[i]))
        return pool[:K]

    pop_list = popular_list()

    rows = []
    for u in users:
        rows.append({
            "u": u, "pop": ndcg10(pop_list, u["liked"]),
            "cf": ndcg10(cf_list(u), u["liked"]),
            "cand": ndcg10(candidate_list(u), u["liked"]),
        })

    def mean(xs: list[float]) -> float:
        return sum(xs) / len(xs)

    def bucket(n: int) -> str:
        if n < 5:
            return "0-4"
        if n == 5:
            return "5"
        if n <= 10:
            return "6-10"
        if n <= 20:
            return "11-20"
        return "21+"

    print("== 1. the aggregate: it passes ==")
    a_pop = mean([r["pop"] for r in rows])
    a_cf = mean([r["cf"] for r in rows])
    a_cand = mean([r["cand"] for r in rows])
    print(f"{N_USERS:,} users, {N_ITEMS:,} items, 10 slots, binary relevance")
    print(f"candidate nDCG@10 {a_cand:.3f} vs popularity {a_pop:.3f} "
          f"vs item-item CF {a_cf:.3f}")
    print("the candidate beats both baselines. the report would pass.\n")

    print("== 2. slice by interaction count: the boundary shows ==")
    print(f"{'bucket':>7} {'users':>7} {'cand':>7} {'CF':>7} {'pop':>7} "
          f"{'gap to 21+':>11}")
    trusted = mean([r["cand"] for r in rows if bucket(r["u"]["n"]) == "21+"])
    for b in ["0-4", "5", "6-10", "11-20", "21+"]:
        group = [r for r in rows if bucket(r["u"]["n"]) == b]
        cand = mean([r["cand"] for r in group])
        print(f"{b:>7} {len(group):>7,} "
              f"{cand:>7.3f} "
              f"{mean([r['cf'] for r in group]):>7.3f} "
              f"{mean([r['pop'] for r in group]):>7.3f} "
              f"{cand - trusted:>11.3f}")

    print("\n== 3. slice by preferred-category size: the tail shows ==")
    print(f"{'pref':>7} {'users':>7} {'cand':>7} {'CF':>7} {'pop':>7} "
          f"{'pool cap':>9}")
    for cat, _, cap, _ in CATS:
        group = [r for r in rows if r["u"]["pref"] == cat]
        print(f"{cat:>7} {len(group):>7,} "
              f"{mean([r['cand'] for r in group]):>7.3f} "
              f"{mean([r['cf'] for r in group]):>7.3f} "
              f"{mean([r['pop'] for r in group]):>7.3f} {cap:>9}")

    print("\n== 4. drill into the bottom cases ==")
    bottom = sorted(rows, key=lambda r: r["cand"])[:50]
    print("worst 50 users by candidate nDCG@10:")
    print(f"{'user':>6} {'int':>4} {'pref':>5} {'lands':>6} {'pool':>5} "
          f"{'cand':>6} {'cf':>6} {'pop':>6}")
    for r in bottom[:10]:
        u = r["u"]
        pool_size = (len(cat_items_by_cat[u["pref"]][:pool_cap[u["pref"]]])
                     if u["lands"] else 0)
        print(f"{u['id']:>6} {u['n']:>4} {u['pref']:>5} "
              f"{u['lands']!s:>6} {pool_size:>5} {r['cand']:>6.3f} "
              f"{r['cf']:>6.3f} {r['pop']:>6.3f}")
    by_cat = {cat: sum(1 for r in bottom if r["u"]["pref"] == cat)
              for cat, _, _, _ in CATS}
    by_bucket = {b: sum(1 for r in bottom if bucket(r["u"]["n"]) == b)
                 for b in ["0-4", "5", "6-10", "11-20", "21+"]}
    print(f"worst-50 pref mix: {by_cat}; interaction mix: {by_bucket}")
    tail_share = len([u for u in users if u["pref"] == "tail"]) / N_USERS
    print(f"tail users are {tail_share:.0%} of the population and "
          f"{by_cat['tail'] / len(bottom):.0%} of the worst 50 "
          f"({by_cat['tail']} of 50).")

    print("\n== 5. verify the mechanisms, not just the cases ==")
    for b in ["5", "6-10", "11-20", "21+"]:
        group = [u for u in users if bucket(u["n"]) == b]
        landed = mean([1.0 if u["lands"] else 0.0 for u in group])
        print(f"interactions {b:>5}: personalization lands {landed:.0%} "
              f"of the time (n={len(group):,})")
    for cat, _, cap, _ in CATS:
        n_cat = len(cat_items_by_cat[cat])
        print(f"{cat:>4} recall pool: {n_cat:>5,} items, capped at {cap:>3} "
              "by the recall stage")

    print("\n== 6. the verdict ==")
    print("the aggregate passed, and the two slices that trail map to the")
    print("two mechanisms: the 5-interaction boundary group (personalization")
    print("lands 65% vs 95% at 11+) and tail-pref users (a 10-item pool,")
    print("exactly one slate, so the ranker has nothing to reorder). these")
    print("are the case files the report attaches, each with a named fix")
    print("target: move the eligibility boundary or widen the")
    print("rare-category recall pool.")


if __name__ == "__main__":
    main()
