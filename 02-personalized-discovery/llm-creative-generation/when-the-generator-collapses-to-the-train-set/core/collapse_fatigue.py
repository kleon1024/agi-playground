"""Generator collapse to the train set, audited: does re-run copy wear out?

Stage 41's generator is scored on the surface and the winner is
delivered. This audit prices the failure the stage's single scored
batch skips: when the generator keeps re-emitting the top ads from the
historical corpus (mode-seeking generation), the scorer keeps picking
those same winners, and the cohort has already seen them — the
delivered creative wears out at generation time, before a single new
impression is bought.

It sweeps the collapse severity p (chance each candidate is a copy of
an existing top ad rather than novel copy), runs flights of 25
deliveries to one cohort each, and measures the cohort's mean delivered
CTR under per-ad fatigue, the share of deliveries that re-run copy the
cohort has already seen, and how much the flight decays from its first
block to its last.

Run:
    uv run python core/collapse_fatigue.py
"""

from __future__ import annotations

import random

CANDIDATES = 10
FLIGHTS = 4_000
DELIVERIES = 25
FATIGUE = 0.78
CORPUS_CTRS = (0.090, 0.084, 0.078)


def run_flight(
    rng: random.Random, collapse: float
) -> tuple[float, float, float, float]:
    """One flight to one cohort; returns effective CTR, re-run share,
    winner lock share, and first-block minus last-block CTR."""
    seen: list[int] = [0] * len(CORPUS_CTRS)
    effective: list[float] = []
    reruns = 0
    counts: dict[int, int] = {}
    for delivery in range(DELIVERIES):
        latents: list[float] = []
        corpus_ids: list[int] = []
        for _ in range(CANDIDATES):
            if rng.random() < collapse:
                cid = rng.randrange(len(CORPUS_CTRS))
                corpus_ids.append(cid)
                latents.append(CORPUS_CTRS[cid])
            else:
                corpus_ids.append(-1)
                latents.append(rng.uniform(0.005, 0.10))
        scores = [
            latent + rng.uniform(-0.004, 0.004) for latent in latents
        ]
        winner = max(range(CANDIDATES), key=lambda i: scores[i])
        cid = corpus_ids[winner]
        if cid >= 0:
            seen[cid] += 1
            counts[cid] = counts.get(cid, 0) + 1
            ctr = CORPUS_CTRS[cid] * (FATIGUE ** (seen[cid] - 1))
            if seen[cid] > 1:
                reruns += 1
        else:
            ctr = latents[winner]
        effective.append(ctr)
    first_block = sum(effective[:5]) / 5
    last_block = sum(effective[-5:]) / 5
    if counts:
        top_ad_share = max(counts.values()) / DELIVERIES
    else:
        top_ad_share = 0.0
    mean_ctr = sum(effective) / DELIVERIES
    return mean_ctr, reruns / DELIVERIES, top_ad_share, first_block - last_block


def main() -> None:
    rng = random.Random(23)
    print("generator collapse, audited: does re-run copy wear out?")
    print("  one flight = 25 deliveries to the same cohort")
    print("  per-ad fatigue: each re-run of the same ad earns CTR x 0.78")
    print()
    print("collapse p | delivered CTR | re-run share | top-ad lock | decay first-last")
    for collapse in (0.0, 0.3, 0.6):
        rng = random.Random(23)
        ctr_sum = 0.0
        rerun_sum = 0.0
        lock_sum = 0.0
        decay_sum = 0.0
        for _ in range(FLIGHTS):
            mean_ctr, reruns, lock, decay = run_flight(rng, collapse)
            ctr_sum += mean_ctr
            rerun_sum += reruns
            lock_sum += lock
            decay_sum += decay
        print(
            f"    {collapse:.1f} |     {ctr_sum / FLIGHTS:.4f} | "
            f"     {rerun_sum / FLIGHTS:6.1%} | "
            f"     {lock_sum / FLIGHTS:6.1%} | "
            f"{decay_sum / FLIGHTS:+.4f}"
        )
    print()
    print("reading: even with a scorer that picks the highest latent")
    print("CTR, mode-seeking generation turns the winner into a re-run:")
    print("the cohort has already seen it, so the delivered CTR decays")
    print("inside the flight. Diversity controls at generation are not")
    print("a style preference — they are what keeps the delivered")
    print("creative novel enough to still convert (Keon et al. 2025).")


if __name__ == "__main__":
    main()
