"""Stage 01 -- recover two quantities from the render that a controller
needs: lateral offset from the lane center, and distance to the nearest
obstacle ahead. Hand-built estimator versus a small learned network, both
measured against ground truth from the simulator state.

The hand-built estimator is the honest first baseline: road-surface pixels
in the near rows give the lane-center offset; the nearest obstacle-valued
pixel gives obstacle distance. A learned model should not need to beat it
by a huge margin to be worth having -- but if it cannot beat it at all,
the render already leaks what the controller needs.

Usage:
    python perception.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import torch
from torch import nn

SIM_DIR = Path(__file__).resolve().parents[2] / "00-scenario-simulator" / "core"
sys.path.insert(0, str(SIM_DIR))
from driving_sim import (
    GRID,
    M_PER_PIX,
    PATCH,
    Car,
    render,
    sample_scenario,
)

RUNS = Path(__file__).resolve().parents[1] / "runs"
N_FRAMES = 4000
EPOCHS = 40


def hand_estimates(scenario, car):
    grid = render(scenario, car)
    # lateral offset: mean horizontal position of road pixels in the bottom
    # half (near rows), expressed in meters from the render center
    rows = GRID // 2
    xs, weights = [], []
    for row in range(rows, GRID):
        for col in range(GRID):
            v = grid[row][col]
            if 0.0 < v < 2.0:
                xs.append(col + 0.5)
                weights.append(v)
    lat_px = (sum(x * w for x, w in zip(xs, weights)) / sum(weights)
              - GRID / 2) if weights else 0.0
    lateral = lat_px * M_PER_PIX
    # nearest obstacle: the largest row index (closest) holding an obstacle
    # pixel; distance = (GRID - row) * M_PER_PIX
    dist = None
    for row in range(GRID - 1, -1, -1):
        if any(v >= 2.0 for v in grid[row]):
            dist = (GRID - row) * M_PER_PIX
            break
    return lateral, dist if dist is not None else 99.0


def nearest_obstacle_ahead(scenario, car):
    """Distance to the nearest obstacle visible in the rendered patch
    (within `PATCH` meters ahead and the patch's lateral span), or 99.0 if
    none is visible. Matching the render's answer space is the point: the
    perception task is what can be recovered from the render, not oracle
    knowledge of the whole road."""
    best = None
    for ox, oy, r, _ in scenario.obstacles:
        d = ox - car.x
        if d < -0.5 or d > PATCH + 0.5:
            continue
        if abs(oy - car.y) < PATCH / 2:
            dist = max(0.0, d - r)
            best = dist if best is None else min(best, dist)
    return best if best is not None else 99.0


def build_frames(seed0: int, n: int):
    rng = torch.Generator().manual_seed(1234)
    frames, lateral_gt, obs_gt = [], [], []
    made = 0
    while made < n:
        scenario = sample_scenario(int(torch.randint(0, 200, (1,), generator=rng)))
        car = Car(x=float(torch.randint(2, 40, (1,), generator=rng)),
                  y=scenario.lane_center(4.0),
                  theta=0.0)
        for _ in range(8):
            grid = render(scenario, car)
            lateral = car.y - scenario.lane_center(car.x)
            frames.append([v for row in grid for v in row])
            lateral_gt.append(lateral)
            obs_gt.append(nearest_obstacle_ahead(scenario, car))
            car.x += 0.8
            made += 1
            if made >= n:
                break
    return (torch.tensor(frames, dtype=torch.float32).unsqueeze(1),
            torch.tensor(lateral_gt, dtype=torch.float32).unsqueeze(1),
            torch.tensor(obs_gt, dtype=torch.float32).unsqueeze(1))


class PerceptionMLP(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(GRID * GRID, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 2),
        )

    def forward(self, x):
        return self.net(x)


def main() -> None:
    t0 = time.time()
    x, lat, obs = build_frames(0, N_FRAMES)
    n = x.shape[0]
    split = int(0.8 * n)
    x_tr, lat_tr, obs_tr = x[:split], lat[:split], obs[:split]
    x_te, lat_te, obs_te = x[split:], lat[split:], obs[split:]
    # scale targets so the two quantities share a loss scale
    lat_tr_s, obs_tr_s = lat_tr / 2.0, obs_tr / 20.0

    # hand-built estimator on the test split
    # (rebuild scenarios identically: frames were generated with a fixed
    #  generator; here we re-derive per-frame ground truth is not needed --
    #  we re-estimate from the same renders)
    hand_lat, hand_obs = [], []
    for i in range(len(x_te)):
        grid = x_te[i, 0].view(GRID, GRID).tolist()
        rows = GRID // 2
        xs, weights = [], []
        for row in range(rows, GRID):
            for col in range(GRID):
                v = grid[row][col]
                if 0.0 < v < 2.0:
                    xs.append(col + 0.5)
                    weights.append(v)
        if weights:
            lat_px = (sum(a * w for a, w in zip(xs, weights)) / sum(weights)
                      - GRID / 2)
        else:
            lat_px = 0.0
        hand_lat.append(lat_px * M_PER_PIX)
        dist = 99.0
        for row in range(GRID - 1, -1, -1):
            if any(v >= 2.0 for v in grid[row]):
                dist = (GRID - row) * M_PER_PIX
                break
        hand_obs.append(dist)

    lat_te_l = lat_te[:, 0].tolist()
    obs_te_l = obs_te[:, 0].tolist()
    hand_lat_mae = sum(abs(a - b) for a, b in zip(hand_lat, lat_te_l)) / len(lat_te_l)
    hand_obs_mae = sum(abs(a - b) for a, b in zip(hand_obs, obs_te_l)) / len(obs_te_l)

    # learned model
    model = PerceptionMLP()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    lossf = nn.MSELoss()
    batch = 128
    train_t0 = time.time()
    for epoch in range(EPOCHS):
        perm = torch.randperm(split)
        total = 0.0
        for i in range(0, split, batch):
            idx = perm[i:i + batch]
            y = torch.cat([lat_tr_s[idx], obs_tr_s[idx]], dim=1)
            opt.zero_grad()
            loss = lossf(model(x_tr[idx]), y)
            loss.backward()
            opt.step()
            total += loss.item() * len(idx)
        if epoch in (0, EPOCHS - 1):
            print(f"epoch {epoch:02d} train mse {total / split:.4f}")
    train_wall = time.time() - train_t0

    with torch.no_grad():
        pred = model(x_te)
    pred_lat_mae = (pred[:, 0] * 2.0 - lat_te[:, 0]).abs().mean().item()
    pred_obs_mae = (pred[:, 1] * 20.0 - obs_te[:, 0]).abs().mean().item()

    summary = {
        "frames": n,
        "train_frames": split,
        "test_frames": n - split,
        "epochs": EPOCHS,
        "hand_lateral_mae_m": round(hand_lat_mae, 4),
        "hand_obstacle_mae_m": round(hand_obs_mae, 4),
        "learned_lateral_mae_m": round(pred_lat_mae, 4),
        "learned_obstacle_mae_m": round(pred_obs_mae, 4),
        "learned_train_wall_s": round(train_wall, 2),
        "total_wall_s": round(time.time() - t0, 2),
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / "2026-08-07-perception.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
