"""Preference optimization, read: the ranker trained on pairwise choices.

Stage 32 is RLHF applied to ranking: instead of predicting a score,
the model learns from pairwise preferences which item the user chose.
This script reads a Bradley-Terry log loss step on three preference
pairs.

Run:
    uv run python core/preference_opt.py
    uv run python core/preference_opt.py --emit-log /tmp/pair-margin-envelope.json

The `--emit-log` flag writes the audit cohort: 20 preference pairs —
10 head and 10 tail — with their chosen and rejected scores and whether
the observed label flipped under label noise. Head pairs have wide
margins and are stable; tail pairs are near ties, where noise can flip
the preference. The production path in `prod/pair_margin_audit.py`
measures the flip rate per stratum, the case-finding that shows which
preferences the label noise actually decides.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# Audit cohort: preference pairs with their chosen and rejected scores.
# The `flip` flag says whether label noise made the observed label
# contradict the true preference. Head pairs have wide margins, so
# noise cannot flip them; tail pairs are near ties, where a small
# perturbation decides which item is reported as chosen.
AUDIT_PAIRS = {
    "head": [
        {"chosen": 1.2, "rejected": 0.4, "flip": False},
        {"chosen": 1.5, "rejected": 0.3, "flip": False},
        {"chosen": 2.0, "rejected": 0.5, "flip": False},
        {"chosen": 1.8, "rejected": 0.7, "flip": False},
        {"chosen": 1.4, "rejected": 0.2, "flip": False},
        {"chosen": 1.7, "rejected": 0.6, "flip": False},
        {"chosen": 1.9, "rejected": 0.8, "flip": False},
        {"chosen": 2.1, "rejected": 1.0, "flip": False},
        {"chosen": 1.3, "rejected": 0.1, "flip": False},
        {"chosen": 1.6, "rejected": 0.5, "flip": False},
    ],
    "tail": [
        {"chosen": 0.90, "rejected": 0.85, "flip": False},
        {"chosen": 1.05, "rejected": 1.00, "flip": False},
        {"chosen": 0.95, "rejected": 0.90, "flip": True},
        {"chosen": 1.10, "rejected": 1.05, "flip": False},
        {"chosen": 0.80, "rejected": 0.78, "flip": True},
        {"chosen": 1.20, "rejected": 1.18, "flip": False},
        {"chosen": 0.75, "rejected": 0.72, "flip": True},
        {"chosen": 1.30, "rejected": 1.28, "flip": False},
        {"chosen": 0.85, "rejected": 0.80, "flip": True},
        {"chosen": 1.00, "rejected": 0.95, "flip": False},
    ],
}


def render() -> None:
    # (chosen score, rejected score) pairs with the model's logits.
    pairs = [(1.2, 0.4), (0.9, 0.8), (0.3, 1.1)]
    print("preference optimization, read (Bradley-Terry log loss):")
    total = 0.0
    for chosen, rejected in pairs:
        logit = chosen - rejected
        p = sigmoid(logit)
        loss = -math.log(p)
        total += loss
        print(
            f"  chosen {chosen} vs rejected {rejected}: "
            f"logit {logit:.1f}, p {p:.2f}, loss {loss:.2f}"
        )
    print(f"  total loss: {total:.2f}")
    print("\nreading: the model is pushed to widen the gap between the")
    print("chosen and the rejected item. The loss is the negative log")
    print("probability of the preference; real RLHF optimizes it over")
    print("sampled pairs, which is where the reward-hacking detour lives.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the audit cohort as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        Path(args.emit_log).write_text(json.dumps({"pairs": AUDIT_PAIRS}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
