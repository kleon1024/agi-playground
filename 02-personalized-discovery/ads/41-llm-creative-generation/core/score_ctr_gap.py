"""Score-versus-CTR gap, audited: does the surface score pick the
creative that converts?

Stage 41's pipeline generates variants and a scoring model picks the
one that gets delivered. This audit asks the industrial question the
stage's single scored batch skips: the score is a surface judgment
(urgency, buzzwords), the measured CTR is what the delivery earns, and
the two pick different winners. It draws batches of generated variants,
gives each a surface score that mixes the true signal with
surface-appeal junk that predicts nothing, and measures how often the
surface-selected creative is not the CTR-best one, and what the
selection costs in expected CTR.

Run:
    uv run python core/score_ctr_gap.py
"""

from __future__ import annotations

import random

BATCH_SIZE = 10
BATCHES = 5_000
APPEAL_WEIGHT = 0.40


def draw_batch(rng: random.Random) -> tuple[list[float], list[float], list[str]]:
    """One batch: true CTRs, surface scores, and text labels."""
    ctrs: list[float] = []
    scores: list[float] = []
    texts: list[str] = []
    for i in range(BATCH_SIZE):
        ctr = rng.uniform(0.005, 0.10)
        ctrs.append(ctr)
        appeal = rng.uniform(0.0, 1.0)
        score = (1.0 - APPEAL_WEIGHT) * ctr / 0.10 + APPEAL_WEIGHT * appeal
        scores.append(score)
        texts.append(f"variant {i + 1}")
    return ctrs, scores, texts


def main() -> None:
    rng = random.Random(1)
    ctrs, scores, texts = draw_batch(rng)
    surface_winner = max(range(BATCH_SIZE), key=lambda i: scores[i])
    ctr_winner = max(range(BATCH_SIZE), key=lambda i: ctrs[i])

    print("score-versus-CTR gap, audited: does the surface pick convert?")
    print("  one illustrative batch of 10 generated variants")
    print("  surface score = 60% true-signal proxy + 40% appeal junk")
    print()
    print("  variant      | surface score | true CTR")
    for i in range(BATCH_SIZE):
        marker = " <- selected" if i == surface_winner else ""
        if i == ctr_winner:
            marker += " <- CTR best"
        print(f"  {texts[i]:12s} | {scores[i]:8.3f}      | {ctrs[i]:.4f}{marker}")
    print()
    print(f"  surface-selected: {texts[surface_winner]} (CTR {ctrs[surface_winner]:.4f})")
    print(f"  CTR-best:         {texts[ctr_winner]} (CTR {ctrs[ctr_winner]:.4f})")
    print()

    rng = random.Random(11)
    mismatched = 0
    ctr_loss_sum = 0.0
    chosen_sum = 0.0
    best_sum = 0.0
    for _ in range(BATCHES):
        ctrs, scores, _ = draw_batch(rng)
        surface_winner = max(range(BATCH_SIZE), key=lambda i: scores[i])
        ctr_winner = max(range(BATCH_SIZE), key=lambda i: ctrs[i])
        if surface_winner != ctr_winner:
            mismatched += 1
        best = ctrs[ctr_winner]
        chosen = ctrs[surface_winner]
        ctr_loss_sum += (best - chosen) / best
        chosen_sum += chosen
        best_sum += best
    print(f"  over {BATCHES:,} batches of {BATCH_SIZE} variants:")
    print(f"    surface selection != CTR best: {mismatched / BATCHES:6.1%}")
    print(f"    mean relative CTR loss:        {ctr_loss_sum / BATCHES:6.1%}")
    print(f"    mean chosen CTR vs best CTR:   {chosen_sum / BATCHES:.4f} vs "
          f"{best_sum / BATCHES:.4f}")
    print()
    print("reading: with a surface-appeal component of 0.40, the")
    print("surface score picks the CTR-best creative in only about")
    print("half the batches, and the selection gives up a slice of")
    print("delivered CTR every time it misses. The score has to be")
    print("calibrated against measured delivery before it decides —")
    print("stage 16's pCTR rule applied to the creative surface.")


if __name__ == "__main__":
    main()
