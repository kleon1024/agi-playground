"""A paired, multi-seed data-mixture A/B harness, run entirely on CPU.

The question this answers is never "which corpus is bigger" — it is "does
replacing part of the training mixture with a candidate source change the
model's fit to a fixed held-out target, by more than run-to-run noise would
produce anyway." Everything except the mixture is held fixed: the tiny model,
the token budget, and the held-out evaluation sequence never change between
arms or between seeds.

The model is deliberately trivial — an order-1 (bigram) character model with
additive smoothing — because the mechanism under test is the *harness*, not
the model. Two synthetic domains stand in for "curated data that resembles the
eval task" and "generic web data that does not": a `reference` generator drawn
from the same transition table as the fixed eval sequence, and a `general`
generator drawn from an unrelated one. A mixture spec is just the fraction of
training tokens pulled from `reference` rather than `general`.

Each seed reseeds only the *sampling* of the training sequence — which
characters happen to get drawn given the mixture's transition probabilities —
never the mixture itself and never the eval sequence. That is what makes the
seeds a nuisance variable rather than a second experiment: they measure how
much the outcome would wobble if you had trained on differently-ordered data
from the exact same policy.

The default mixtures (38% vs. 43% reference data) are deliberately close: the
apparent gap is real, but at a handful of seeds it will not clear the noise
band, and at more seeds it will. Finding that crossover means running the
sweep and reading where the interval stops spanning zero — not assuming the
answer in advance.

Run:
    python ablation.py --seeds 1
    python ablation.py --seeds 8
    python ablation.py --sweep 1,2,4,8,16,32
"""

from __future__ import annotations

import argparse
import math
import random
import statistics
from itertools import pairwise

ALPHABET = list("abcdefghijklmnopqrstuvwxyz ")

# TRAIN_LEN and the default mixtures in main() were chosen by search, so that
# the verdict crosses from "not detectable" to a declared winner somewhere in
# the middle of the seed sweep rather than at either end. That makes the
# crossover visible in a demo; it is not a property of this model, and a
# reader who moves the mixtures will move the crossover. Disclosed because a
# harness built to refuse manufactured wins should not ship one.
TRAIN_LEN = 400
EVAL_LEN = 1500
Z95 = 1.96  # normal-approximation critical value for a 95% interval


def _random_transitions(rng: random.Random) -> dict[str, list[float]]:
    """A fixed bigram transition table: for each character, a distribution
    over the next one. Building it once from a seeded generator is what makes
    a "domain" a stable, reusable object rather than noise regenerated per call.
    """
    table = {}
    for ch in ALPHABET:
        weights = [rng.random() ** 3 for _ in ALPHABET]  # peaky, not uniform
        total = sum(weights)
        table[ch] = [w / total for w in weights]
    return table


# The task's true distribution and an unrelated distribution, fixed once at
# import time. `reference` training data is drawn from the SAME table as the
# eval sequence (it resembles the task); `general` data is drawn from an
# unrelated table (it does not).
_TASK_TABLE = _random_transitions(random.Random("target-task"))
_GENERAL_TABLE = _random_transitions(random.Random("generic-web"))


def _sample_sequence(table: dict[str, list[float]], rng: random.Random, length: int) -> str:
    ch = rng.choice(ALPHABET)
    out = [ch]
    for _ in range(length - 1):
        ch = rng.choices(ALPHABET, weights=table[ch], k=1)[0]
        out.append(ch)
    return "".join(out)


EVAL_SEQUENCE = _sample_sequence(_TASK_TABLE, random.Random("held-out-eval"), EVAL_LEN)


def make_training_sequence(reference_fraction: float, seed: int) -> str:
    """Interleave `reference` and `general` characters token by token.

    Only the sampling order and the specific draws depend on `seed`; the
    mixture (`reference_fraction`) and the two source tables never change.
    That is the entire experimental design: one variable moves, everything
    else is nailed down.
    """
    rng = random.Random(f"train-{seed}")
    prev_ref, prev_gen = rng.choice(ALPHABET), rng.choice(ALPHABET)
    out = []
    for _ in range(TRAIN_LEN):
        if rng.random() < reference_fraction:
            prev_ref = rng.choices(ALPHABET, weights=_TASK_TABLE[prev_ref], k=1)[0]
            out.append(prev_ref)
        else:
            prev_gen = rng.choices(ALPHABET, weights=_GENERAL_TABLE[prev_gen], k=1)[0]
            out.append(prev_gen)
    return "".join(out)


def train_bigram_model(text: str, smoothing: float = 1.0) -> dict[str, list[float]]:
    """The tiny model: bigram counts with Laplace smoothing. This is the whole
    architecture, and it is identical for every arm and every seed — the only
    thing that ever differs between calls is which `text` it is fed.
    """
    counts = {ch: [smoothing] * len(ALPHABET) for ch in ALPHABET}
    index = {ch: i for i, ch in enumerate(ALPHABET)}
    for a, b in pairwise(text):
        counts[a][index[b]] += 1
    return {ch: [c / sum(row) for c in row] for ch, row in counts.items()}


def cross_entropy_bits(model: dict[str, list[float]], text: str) -> float:
    """Average bits/char to encode `text` under `model` — lower is a better
    fit. This is the single number each run produces; the harness never looks
    at anything else.
    """
    index = {ch: i for i, ch in enumerate(ALPHABET)}
    total = 0.0
    for a, b in pairwise(text):
        p = model[a][index[b]]
        total += -math.log2(max(p, 1e-12))
    return total / max(len(text) - 1, 1)


def run_arm(reference_fraction: float, num_seeds: int, seed_base: int) -> list[float]:
    scores = []
    for i in range(num_seeds):
        train_text = make_training_sequence(reference_fraction, seed_base + i)
        model = train_bigram_model(train_text)
        scores.append(cross_entropy_bits(model, EVAL_SEQUENCE))
    return scores


def compare(scores_a: list[float], scores_b: list[float], label_a: str, label_b: str) -> None:
    n = len(scores_a)
    assert n == len(scores_b)
    mean_a, mean_b = statistics.mean(scores_a), statistics.mean(scores_b)
    print(f"  {label_a:<22} n={n}  mean={mean_a:.4f} bits/char", end="")
    print(f"  {'(range only, n=1)' if n < 2 else f'sd={statistics.stdev(scores_a):.4f}'}")
    print(f"  {label_b:<22} n={n}  mean={mean_b:.4f} bits/char", end="")
    print(f"  {'(range only, n=1)' if n < 2 else f'sd={statistics.stdev(scores_b):.4f}'}")

    diff = mean_b - mean_a  # negative => b (more reference data) fits better
    print(f"  difference ({label_b} - {label_a}): {diff:+.4f} bits/char")

    if n < 2:
        print("  VERDICT: cannot estimate seed spread from a single run.")
        print("           one run is not a weak result — it is no result.")
        return

    se_a = statistics.stdev(scores_a) / math.sqrt(n)
    se_b = statistics.stdev(scores_b) / math.sqrt(n)
    margin = Z95 * math.sqrt(se_a**2 + se_b**2)
    print(f"  95% interval on the difference: {diff:+.4f} +/- {margin:.4f}")

    if abs(diff) <= margin:
        print(f"  VERDICT: NOT DETECTABLE at n={n} seeds/arm — interval spans zero.")
    else:
        winner = label_b if diff < 0 else label_a
        print(f"  VERDICT: {winner} has the lower held-out cross-entropy at n={n}.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mixture-a", type=float, default=0.38, help="reference fraction, arm A")
    ap.add_argument("--mixture-b", type=float, default=0.43, help="reference fraction, arm B")
    ap.add_argument("--seeds", type=int, default=8, help="seeds per arm")
    ap.add_argument("--sweep", type=str, default="", help="comma-separated seed counts, e.g. 1,2,4,8,16")
    ap.add_argument("--seed-base", type=int, default=0)
    args = ap.parse_args()

    label_a = f"mixture A (ref={args.mixture_a:.0%})"
    label_b = f"mixture B (ref={args.mixture_b:.0%})"

    seed_counts = [int(s) for s in args.sweep.split(",") if s.strip()] if args.sweep else [args.seeds]
    max_seeds = max(seed_counts)

    # Draw once at the largest requested count, then take prefixes. Seed i is
    # therefore the same run at every n along the sweep — n only decides how
    # much of it you are allowed to look at before answering.
    full_a = run_arm(args.mixture_a, max_seeds, args.seed_base)
    full_b = run_arm(args.mixture_b, max_seeds, args.seed_base)

    for n in seed_counts:
        print(f"\n=== {n} seed(s) per arm ===")
        compare(full_a[:n], full_b[:n], label_a, label_b)


if __name__ == "__main__":
    main()
