"""The production lane for stage 04: a real autodiff framework for the shared
trunk, and a non-parametric calibrator in place of core's hand-rolled Platt
scaling.

Two upgrades over `core/fine_rank.py`, each addressing a limitation the core
file states plainly rather than hides:

**PyTorch instead of hand-derived gradients.** The shared trunk plus per-task
heads architecture is unchanged; what changes is that gradients come from
autodiff and the optimizer is Adam with per-parameter adaptive step sizes,
which tolerates the naive/balanced loss-scale gap this stage exists to
teach far better than plain SGD does. That is worth knowing on its own: some
of what looks like "negative transfer" in a from-scratch SGD implementation
is really "SGD is sensitive to loss scale," and a better optimizer narrows
but does not erase the gap — normalizing the losses still helps.

**Isotonic regression instead of Platt scaling.** Platt scaling fits a single
monotonic *logistic* curve (`sigmoid(a*z + b)`) — two parameters, so it
cannot fix a miscalibration shaped differently from that curve, for instance
a model that is overconfident in the middle of its range and underconfident
at the extremes. Isotonic regression fits the least-squares-optimal
*non-decreasing step function*, with as many degrees of freedom as there are
distinct predicted values — strictly more flexible, at the cost of needing
more calibration data to avoid overfitting the calibration curve itself.

This script reuses `core/fine_rank.py`'s dataset generator (`make_dataset`)
so the comparison is apples-to-apples: same underlying labels, same
observation sparsity, different training and calibration mechanism.

Requires `torch` and `scikit-learn`, neither part of this repository's base
dependency group.

Run:  python torch_fine_rank.py --epochs 25
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

import fine_rank as core  # our from-scratch dataset and metrics
import torch
from sklearn.isotonic import IsotonicRegression
from torch import nn


class SharedTrunkModel(nn.Module):
    """One trunk, one linear head per task — the same shape as core's
    hand-rolled version, expressed as modules instead of raw lists.
    """

    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.Tanh())
        self.heads = nn.ModuleDict({task: nn.Linear(hidden_dim, 1) for task in core.TASKS})

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        h = self.trunk(x)
        return {task: self.heads[task](h).squeeze(-1) for task in core.TASKS}


def to_tensor(examples: list[core.Example]) -> torch.Tensor:
    return torch.tensor([ex.features for ex in examples], dtype=torch.float32)


def train_torch(examples: list[core.Example], hidden: int, epochs: int, lr: float, seed: int) -> SharedTrunkModel:
    torch.manual_seed(seed)
    model = SharedTrunkModel(input_dim=5, hidden_dim=hidden)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    bce = nn.BCEWithLogitsLoss()

    x_all = to_tensor(examples)
    for _ in range(epochs):
        optimizer.zero_grad()
        outputs = model(x_all)
        loss = torch.zeros(())
        for task in core.TASKS:
            idx = [i for i, ex in enumerate(examples) if task in ex.labels]
            if not idx:
                continue
            idx_t = torch.tensor(idx, dtype=torch.long)
            preds = outputs[task][idx_t]
            targets = torch.tensor([examples[i].labels[task] for i in idx], dtype=torch.float32)
            if task in core.BINARY_TASKS:
                loss = loss + bce(preds, targets)
            else:
                # Same normalization argument as core's "balanced" run: divide
                # the continuous target onto roughly the same scale as the
                # bounded binary losses before summing.
                loss = loss + 0.3 * nn.functional.mse_loss(preds, targets / core.DWELL_SCALE)
        loss.backward()
        optimizer.step()
    return model


def run(hidden: int, epochs: int, lr: float, seed: int) -> None:
    train_examples = core.make_dataset(1500, seed)
    calib_examples = core.make_dataset(400, seed + 1999)

    model = train_torch(train_examples, hidden, epochs, lr, seed)
    model.eval()

    with torch.no_grad():
        click_examples = [ex for ex in calib_examples if "click" in ex.labels]
        x = to_tensor(click_examples)
        logits = model(x)["click"].tolist()
        labels = [ex.labels["click"] for ex in click_examples]

    raw_probs = [core.sigmoid(z) for z in logits]
    ece_before = core.expected_calibration_error(raw_probs, labels)

    # IsotonicRegression maps raw score -> calibrated probability directly; it
    # does not need the logit, only a monotonic input, so raw probability
    # works as well as the logit does.
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(raw_probs, labels)
    calibrated_probs = iso.predict(raw_probs).tolist()
    ece_after = core.expected_calibration_error(calibrated_probs, labels)

    print(f"trunk hidden={hidden}, epochs={epochs}, lr={lr} (PyTorch, Adam)\n")
    print(f"calibration (click head, {len(click_examples)} held-out examples):")
    print(f"  ECE before calibration            {ece_before:.4f}")
    print(f"  ECE after isotonic regression      {ece_after:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hidden", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.hidden, args.epochs, args.lr, args.seed)


if __name__ == "__main__":
    main()
