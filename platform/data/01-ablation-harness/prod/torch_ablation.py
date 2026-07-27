"""The same paired multi-seed data-mixture A/B job as `core/ablation.py`, with
two pieces swapped for their real-tool equivalents:

* **A trained model instead of closed-form counts.** `core/` fits a bigram
  table by counting, which has an exact solution and no optimizer. Here a
  tiny character-level GRU is fit by gradient descent — the object every
  production ablation actually trains is a network, and its loss surface,
  initialization, and optimizer noise are additional sources of run-to-run
  variance that a counting model cannot exhibit.
* **A real hypothesis test instead of a hand-rolled interval.** `core/` builds
  a 95% interval from a normal approximation, which is a reasonable estimate
  for teaching but not the tool a statistician reaches for with small,
  independent samples of possibly unequal variance. This file hands the two
  seed-score arrays straight to `scipy.stats.ttest_ind(..., equal_var=False)`
  — Welch's t-test — and reports its p-value alongside the mean difference.

Everything about the *design* is identical to `core/`: same two synthetic
domains, same fixed held-out sequence, same rule that only the mixture
fraction may differ between arms. Swapping the model and the test changes how
precisely you can trust the answer; it does not change what question is being
asked.

Requires: pip install torch scipy

Training 32 tiny models (16 seeds x 2 arms) on CPU takes a couple of minutes —
still an afternoon's experiment, not a research budget, but slower than the
counting model in `core/`.

Run:
    python torch_ablation.py --mixture-a 0.38 --mixture-b 0.43 --seeds 16
"""

from __future__ import annotations

import argparse
import random

import torch
from scipy import stats
from torch import nn

ALPHABET = list("abcdefghijklmnopqrstuvwxyz ")
STOI = {ch: i for i, ch in enumerate(ALPHABET)}
TRAIN_LEN = 2000
EVAL_LEN = 1500
TRAIN_STEPS = 30


def _random_transitions(rng: random.Random) -> dict[str, list[float]]:
    table = {}
    for ch in ALPHABET:
        weights = [rng.random() ** 3 for _ in ALPHABET]
        total = sum(weights)
        table[ch] = [w / total for w in weights]
    return table


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
    """Same recipe as `core/ablation.py`: only sampling order depends on seed."""
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


def encode(text: str) -> torch.Tensor:
    return torch.tensor([STOI[c] for c in text], dtype=torch.long)


class TinyCharGRU(nn.Module):
    """A real, gradient-trained model — small enough for CPU, structured like
    the thing you would actually fine-tune a data decision against.
    """

    def __init__(self, vocab: int = len(ALPHABET), dim: int = 16):
        super().__init__()
        self.embed = nn.Embedding(vocab, dim)
        self.gru = nn.GRU(dim, dim, batch_first=True)
        self.head = nn.Linear(dim, vocab)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h, _ = self.gru(self.embed(x))
        return self.head(h)


def train_and_score(reference_fraction: float, seed: int) -> float:
    """Train one seed's model on one arm's mixture; return held-out cross-
    entropy in bits/char, directly comparable to `core/ablation.py`'s metric.
    """
    torch.manual_seed(seed)
    text = make_training_sequence(reference_fraction, seed)
    ids = encode(text).unsqueeze(0)

    model = TinyCharGRU()
    opt = torch.optim.Adam(model.parameters(), lr=1e-2, weight_decay=1e-3)
    loss_fn = nn.CrossEntropyLoss()

    for _ in range(TRAIN_STEPS):
        opt.zero_grad()
        logits = model(ids[:, :-1])
        loss = loss_fn(logits.reshape(-1, len(ALPHABET)), ids[:, 1:].reshape(-1))
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        eval_ids = encode(EVAL_SEQUENCE).unsqueeze(0)
        logits = model(eval_ids[:, :-1])
        nats = loss_fn(logits.reshape(-1, len(ALPHABET)), eval_ids[:, 1:].reshape(-1))
    return float(nats) / 0.6931471805599453  # nats -> bits


def run_arm(reference_fraction: float, num_seeds: int, seed_base: int) -> list[float]:
    return [train_and_score(reference_fraction, seed_base + i) for i in range(num_seeds)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mixture-a", type=float, default=0.38)
    ap.add_argument("--mixture-b", type=float, default=0.43)
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--seed-base", type=int, default=0)
    args = ap.parse_args()

    scores_a = run_arm(args.mixture_a, args.seeds, args.seed_base)
    scores_b = run_arm(args.mixture_b, args.seeds, args.seed_base)

    result = stats.ttest_ind(scores_b, scores_a, equal_var=False)
    diff = sum(scores_b) / len(scores_b) - sum(scores_a) / len(scores_a)

    print(f"mixture A (ref={args.mixture_a:.0%})  mean={sum(scores_a)/len(scores_a):.4f} bits/char")
    print(f"mixture B (ref={args.mixture_b:.0%})  mean={sum(scores_b)/len(scores_b):.4f} bits/char")
    print(f"difference (B - A): {diff:+.4f} bits/char")
    print(f"Welch's t-test: t={result.statistic:.3f}  p={result.pvalue:.4f}  (n={args.seeds}/arm)")
    print(
        "VERDICT: "
        + (
            f"not distinguishable from noise at alpha=0.05 (p={result.pvalue:.3f})"
            if result.pvalue >= 0.05
            else f"mixture B differs at alpha=0.05 (p={result.pvalue:.3f})"
        )
    )


if __name__ == "__main__":
    main()
