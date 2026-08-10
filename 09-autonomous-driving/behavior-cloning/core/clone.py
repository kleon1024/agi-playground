"""Stage 03 -- behavior cloning: train a small MLP to imitate the expert
from (render, action) pairs collected on the training scenarios, then
measure held-out imitation accuracy on frames the expert visits in the
eval scenarios.

The honest first check for a cloned policy is not whether it memorizes
training frames -- it is whether actions learned from expert state-action
pairs transfer to states the expert visits outside the training set.
Held-out imitation accuracy is that check; stage 04 adds the in-loop check
this stage deliberately does not run. A majority baseline (always steer 0,
always accelerate) is reported beside the model so an imbalanced action
distribution cannot be mistaken for learning.

Usage:
    python clone.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

SIM_DIR = Path(__file__).resolve().parents[2] / "00-scenario-simulator" / "core"
sys.path.insert(0, str(SIM_DIR))
from driving_sim import (
    GRID,
    collect_demos,
    sample_scenario,
)

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
TRAIN_SEEDS = range(60)
EVAL_SEEDS = range(100, 150)
EPOCHS = 20
BATCH = 256
LR = 1e-3


class CloneNet(nn.Module):
    """Shared trunk, two heads: steer in {-1, 0, 1} and throttle in {0, 1}."""

    def __init__(self) -> None:
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(GRID * GRID, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
        )
        self.steer_head = nn.Linear(64, 3)
        self.throttle_head = nn.Linear(64, 2)

    def forward(self, x: torch.Tensor):
        h = self.trunk(x)
        return self.steer_head(h), self.throttle_head(h)


def collect(train_scenarios) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Roll out the expert on the training scenarios and record frames."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "02-expert-policy" / "core"))
    from expert import make_expert

    frames, steer, throttle = [], [], []
    for s in train_scenarios:
        demos, _ = collect_demos([s], make_expert(s))
        for grid, st, th in demos:
            frames.append(np.asarray(grid, dtype=np.float32).reshape(-1) / 3.0)
            steer.append(st + 1)  # to 0..2
            throttle.append(th)
    return np.stack(frames), np.asarray(steer, dtype=np.int64), np.asarray(throttle, dtype=np.int64)


def eval_open_loop(model: CloneNet, scenarios) -> dict:
    """Imitation accuracy on expert states from the eval scenarios."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "02-expert-policy" / "core"))
    from expert import make_expert

    frames, steer, throttle = [], [], []
    for s in scenarios:
        demos, _ = collect_demos([s], make_expert(s))
        for grid, st, th in demos:
            frames.append(np.asarray(grid, dtype=np.float32).reshape(-1) / 3.0)
            steer.append(st + 1)
            throttle.append(th)
    X = np.stack(frames)
    y_s = np.asarray(steer, dtype=np.int64)
    y_t = np.asarray(throttle, dtype=np.int64)
    with torch.no_grad():
        ps, pt = model(torch.from_numpy(X))
    pred_s = ps.argmax(1).numpy()
    pred_t = pt.argmax(1).numpy()
    n = len(y_s)
    return {
        "eval_frames": n,
        "steer_accuracy": round(float((pred_s == y_s).mean()), 4),
        "throttle_accuracy": round(float((pred_t == y_t).mean()), 4),
        "joint_accuracy": round(float(((pred_s == y_s) & (pred_t == y_t)).mean()), 4),
        # majority baseline: always steer 0, always accelerate
        "baseline_steer_accuracy": round(float((y_s == 1).mean()), 4),
        "baseline_throttle_accuracy": round(float((y_t == 1).mean()), 4),
    }


def main() -> None:
    t0 = time.time()
    train_scenarios = [sample_scenario(seed) for seed in TRAIN_SEEDS]
    eval_scenarios = [sample_scenario(seed) for seed in EVAL_SEEDS]

    X, y_s, y_t = collect(train_scenarios)
    collect_s = time.time()

    model = CloneNet()
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_s = nn.CrossEntropyLoss()
    loss_t = nn.CrossEntropyLoss()
    idx = np.arange(len(X))
    for epoch in range(EPOCHS):
        rng = np.random.default_rng(0)
        rng.shuffle(idx)
        model.train()
        for i in range(0, len(idx), BATCH):
            b = idx[i : i + BATCH]
            xb = torch.from_numpy(X[b])
            ps, pt = model(xb)
            loss = loss_s(ps, torch.from_numpy(y_s[b])) + loss_t(pt, torch.from_numpy(y_t[b]))
            opt.zero_grad()
            loss.backward()
            opt.step()
    train_s = time.time()

    model.eval()
    ev = eval_open_loop(model, eval_scenarios)
    ev_s = time.time()

    RUNS.mkdir(parents=True, exist_ok=True)
    summary = {
        "train_scenarios": len(train_scenarios),
        "eval_scenarios": len(eval_scenarios),
        "train_frames": len(X),
        "epochs": EPOCHS,
        "params": sum(p.numel() for p in model.parameters()),
        "collect_wall_s": round(collect_s - t0, 2),
        "train_wall_s": round(train_s - collect_s, 2),
        "eval_wall_s": round(ev_s - train_s, 2),
        **ev,
    }
    with (RUNS / "2026-08-07-clone.json").open("w") as f:
        json.dump(summary, f, indent=2)
    torch.save(model.state_dict(), ROOT / "core" / "cloned_policy.pt")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
