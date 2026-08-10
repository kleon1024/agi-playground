"""Stage 03 detour -- rebalancing a skewed demo distribution: what the
per-class confusion shows, and what a reweighted clone buys in the loop.

Stage 03's headline (0.883 steer accuracy, 0.772 joint) is an average over
an action distribution in which 76% of demo frames are straight driving.
This detour conditions the same accuracy on the expert's true action and on
near-obstacle frames, then applies the two standard repairs for a skewed
label -- class-weighted loss and per-epoch oversampling -- and re-measures
both the open-loop metric and the in-loop completion the metric is supposed
to predict.

Usage:
    python imbalance_rebalance.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

torch.set_num_threads(1)  # deterministic CPU training for a recorded run

SIM_DIR = Path(__file__).resolve().parents[3] / "00-scenario-simulator" / "core"
EXP_DIR = Path(__file__).resolve().parents[3] / "02-expert-policy" / "core"
CLONE_DIR = Path(__file__).resolve().parents[3] / "03-behavior-cloning" / "core"
sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(EXP_DIR))
sys.path.insert(0, str(CLONE_DIR))
from clone import CloneNet
from driving_sim import (
    GRID,
    collect_demos,
    sample_scenario,
    simulate,
)
from expert import make_expert

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
TRAIN_SEEDS = range(60)
EVAL_SEEDS = range(100, 150)
EPOCHS = 20
BATCH = 256
LR = 1e-3
NEAR_ROW = 16  # render rows with ahead <= 4m (row 0 is farthest ahead)


def collect_frames(scenarios) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Roll out the expert on `scenarios` and record normalized renders."""
    frames, steer, throttle = [], [], []
    for s in scenarios:
        demos, _ = collect_demos([s], make_expert(s))
        for grid, st, th in demos:
            frames.append(np.asarray(grid, dtype=np.float32).reshape(-1) / 3.0)
            steer.append(st + 1)  # to 0..2 (0 = left, 1 = straight, 2 = right)
            throttle.append(th)
    return np.stack(frames), np.asarray(steer, dtype=np.int64), np.asarray(throttle, dtype=np.int64)


def near_obstacle_mask(frames: np.ndarray) -> np.ndarray:
    """True where an obstacle pixel (value 2.0 in the raw render) appears in
    the near half of the patch, i.e. within roughly 4m ahead of the car."""
    arr = frames.reshape(len(frames), GRID, GRID)
    return (arr[:, NEAR_ROW:, :] >= 2.0 / 3.0).any(axis=(1, 2))


def oversample_idx(y: np.ndarray, rng) -> np.ndarray:
    """Per-epoch index that resamples each class up to the majority size."""
    counts = np.bincount(y, minlength=3)
    target = int(counts.max())
    parts = []
    for c in range(3):
        idx_c = np.where(y == c)[0]
        if len(idx_c) == target:
            parts.append(idx_c)
        else:
            parts.append(rng.choice(idx_c, size=target, replace=True))
    return np.concatenate(parts)


def train_clone(X, ys, yt, mode: str, seed: int = 0) -> CloneNet:
    """Train one variant. `base` reproduces stage 03's procedure exactly
    (same epochs, batch, optimizer, per-epoch shuffle); `weighted` scales
    the steer loss by inverse class frequency; `oversampled` re-balances
    the steer classes by resampling within each epoch."""
    torch.manual_seed(seed)
    model = CloneNet()
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_s = nn.CrossEntropyLoss()
    loss_t = nn.CrossEntropyLoss()
    if mode == "weighted":
        counts = np.bincount(ys, minlength=3)
        w = torch.from_numpy((len(ys) / (3.0 * counts)).astype(np.float32))
        loss_s = nn.CrossEntropyLoss(weight=w)
    for _ in range(EPOCHS):
        rng = np.random.default_rng(seed)
        if mode == "oversampled":
            idx = oversample_idx(ys, rng)
        else:
            idx = np.arange(len(X))
        rng.shuffle(idx)
        model.train()
        for i in range(0, len(idx), BATCH):
            b = idx[i : i + BATCH]
            xb = torch.from_numpy(X[b])
            ps, pt = model(xb)
            loss = loss_s(ps, torch.from_numpy(ys[b])) + loss_t(pt, torch.from_numpy(yt[b]))
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.eval()
    return model


def open_loop_metrics(model: CloneNet, X, ys, yt) -> dict:
    """Per-class recall/precision on the expert's own eval frames."""
    with torch.no_grad():
        ps, pt = model(torch.from_numpy(X))
    pred_s = ps.argmax(1).numpy()
    pred_t = pt.argmax(1).numpy()
    n = len(ys)
    steer_recall = {}
    steer_precision = {}
    for c in (0, 1, 2):
        true_c = ys == c
        pred_c = pred_s == c
        steer_recall[str(c)] = round(float((true_c & pred_c).sum() / max(true_c.sum(), 1)), 3)
        steer_precision[str(c)] = round(float((true_c & pred_c).sum() / max(pred_c.sum(), 1)), 3)
    dodge = ys != 1
    pred_dodge = pred_s != 1
    near = near_obstacle_mask(X)
    near_dodge = near & dodge
    return {
        "eval_frames": n,
        "class_counts_steer": {str(c): int((ys == c).sum()) for c in (0, 1, 2)},
        "steer_recall": steer_recall,
        "steer_precision": steer_precision,
        "dodge_recall": round(float((dodge & pred_dodge).sum() / max(dodge.sum(), 1)), 3),
        "dodge_precision": round(float((dodge & pred_dodge).sum() / max(pred_dodge.sum(), 1)), 3),
        "near_obstacle_frames": int(near.sum()),
        "near_dodge_recall": round(
            float(((near_dodge) & (pred_s == ys)).sum() / max(near_dodge.sum(), 1)), 3
        ),
        "near_dodge_precision": round(
            float(((near_dodge) & (pred_s != 1)).sum() / max((near & (pred_s != 1)).sum(), 1)), 3
        ),
        "steer_accuracy": round(float((pred_s == ys).mean()), 4),
        "throttle_accuracy": round(float((pred_t == yt).mean()), 4),
        "joint_accuracy": round(float(((pred_s == ys) & (pred_t == yt)).mean()), 4),
    }


def cloned_policy(model: CloneNet):
    def policy(obs, car):
        x = torch.from_numpy(np.asarray(obs, dtype=np.float32).reshape(-1) / 3.0)
        with torch.no_grad():
            ps, pt = model(x)
        return int(ps.argmax().item() - 1), int(pt.argmax().item())

    return policy


def in_loop_eval(model: CloneNet, scenarios) -> dict:
    """Per-seed outcomes on the 50 eval scenarios, stage-04 style."""
    per_seed = []
    for s in scenarios:
        out = simulate(s, cloned_policy(model))
        if out.completed:
            code = "completed"
        elif out.collided:
            code = "collided"
        elif out.offroad:
            code = "offroad"
        else:
            code = "timeout"
        per_seed.append({"seed": s.seed, "outcome": code, "x": round(out.x_reached, 2)})
    n = len(per_seed)
    counts = {k: sum(1 for p in per_seed if p["outcome"] == k) for k in
              ("completed", "collided", "offroad", "timeout")}
    return {
        "scenarios": n,
        "completion_rate": round(counts["completed"] / n, 3),
        "collision_rate": round(counts["collided"] / n, 3),
        "offroad_rate": round(counts["offroad"] / n, 3),
        "timeout_rate": round(counts["timeout"] / n, 3),
        "fail_seeds": [p["seed"] for p in per_seed if p["outcome"] != "completed"],
        "per_seed": per_seed,
    }


def in_loop_probe(policy_factory, scenarios, easy_seeds: set[int]) -> dict:
    """How the policy actually behaves in the loop: how often it steers,
    and how far it wanders from the lane center, averaged over all steps
    and episodes. Open-loop per-class recall cannot see this."""
    per_ep = [_probe_episode(s, policy_factory(s)) for s in scenarios]
    n = len(scenarios)
    easy = [p for p in per_ep if p["seed"] in easy_seeds]
    return {
        "scenarios": n,
        "mean_nonzero_steer_share": round(float(np.mean([p["nz_steer"] for p in per_ep])), 3),
        "mean_lateral_offset_m": round(float(np.mean([p["lat"] for p in per_ep])), 3),
        "mean_steps_per_episode": round(float(np.mean([p["steps"] for p in per_ep])), 1),
        "easy_seeds": sorted(easy_seeds),
        "easy_nonzero_steer_share": round(float(np.mean([p["nz_steer"] for p in easy])), 3),
        "easy_lateral_offset_m": round(float(np.mean([p["lat"] for p in easy])), 3),
        "per_episode": per_ep,
    }


def _probe_episode(scenario, base_policy) -> dict:
    """Roll one episode, recording the actions the policy actually took so
    the probe can report steering share and lateral offset per seed."""
    act = {"steer": [], "lat": []}

    def policy(obs, car):
        st, th = base_policy(obs, car)
        act["steer"].append(st)
        act["lat"].append(abs(car.y - scenario.lane_center(car.x)))
        return st, th

    out = simulate(scenario, policy)
    return {
        "seed": scenario.seed,
        "steps": out.steps,
        "nz_steer": float(np.mean(np.asarray(act["steer"]) != 0)),
        "lat": float(np.mean(act["lat"])),
    }


def main() -> None:
    t0 = time.time()
    train_scenarios = [sample_scenario(seed) for seed in TRAIN_SEEDS]
    eval_scenarios = [sample_scenario(seed) for seed in EVAL_SEEDS]
    Xtr, ytr_s, ytr_t = collect_frames(train_scenarios)
    Xev, yev_s, yev_t = collect_frames(eval_scenarios)
    collect_s = time.time()

    shipped = CloneNet()
    shipped.load_state_dict(torch.load(CLONE_DIR / "cloned_policy.pt", weights_only=True))
    shipped.eval()

    models = {}
    for mode in ("base", "weighted", "oversampled"):
        models[mode] = train_clone(Xtr, ytr_s, ytr_t, mode)
    train_s = time.time()

    cells = {"shipped": shipped, **models}
    open_loop = {name: open_loop_metrics(m, Xev, yev_s, yev_t) for name, m in cells.items()}
    open_s = time.time()
    in_loop = {name: in_loop_eval(m, eval_scenarios) for name, m in cells.items()}
    probe_s = time.time()
    easy_seeds = {p["seed"] for p in in_loop["base"]["per_seed"] if p["outcome"] == "completed"}
    probe = {name: in_loop_probe(lambda s, m=m: cloned_policy(m), eval_scenarios, easy_seeds)
             for name, m in cells.items()}
    probe["expert"] = in_loop_probe(make_expert, eval_scenarios, easy_seeds)
    loop_s = time.time()

    class_counts = {str(c): int((ytr_s == c).sum()) for c in (0, 1, 2)}
    counts = np.bincount(ytr_s, minlength=3)
    base_fails = set(in_loop["base"]["fail_seeds"])
    transfer = {}
    for name, m in in_loop.items():
        variant_fails = set(m["fail_seeds"])
        transfer[name] = {
            "recovered_vs_base": sorted(base_fails - variant_fails),
            "regressed_vs_base": sorted(variant_fails - base_fails),
        }
    summary = {
        "train_frames": len(Xtr),
        "eval_frames": len(Xev),
        "train_steer_counts": class_counts,
        "train_steer_share_straight": round(float(counts[1] / len(Xtr)), 3),
        "weighted_steer_loss_weights": {
            str(c): round(float(len(Xtr) / (3.0 * counts[c])), 3) for c in (0, 1, 2)
        },
        "epochs": EPOCHS,
        "batch": BATCH,
        "params": sum(p.numel() for p in shipped.parameters()),
        "wall_s": {
            "collect": round(collect_s - t0, 2),
            "train": round(train_s - collect_s, 2),
            "open_loop": round(open_s - train_s, 2),
            "in_loop": round(probe_s - open_s, 2),
            "probe": round(loop_s - probe_s, 2),
        },
        "open_loop": open_loop,
        "in_loop": in_loop,
        "in_loop_probe": probe,
        "transfer_vs_base": transfer,
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / "2026-08-08-imbalance-rebalance.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
