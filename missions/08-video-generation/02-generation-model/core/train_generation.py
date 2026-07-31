"""Train the video-token LM and check whether its greedy completion beats
mission.yaml's declared "no learning" control -- frame-repeat -- the primary
feasibility/quality question this mission exists to answer.

Given the first `PROMPT_FRAMES` real frames of a held-out clip (encoded to
tokens by stage 01's codec), the model generates the remaining frames'
tokens autoregressively; those are decoded back to pixels and compared
against the real remaining frames. The frame-repeat baseline simply repeats
the last conditioning frame's real pixels for every frame it did not see --
"a model that predicts nothing about motion should not be able to beat this."

Usage:
    python train_generation.py --codec-steps 800 --lm-steps 400 --prompt-frames 4
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
from torch import nn

CORE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CORE_DIR))
from video_lm import (
    BOS_TOKEN,
    CodecRecipe,
    build_lm_config,
    build_lm_dataset,
    generate_greedy,
    retrain_codec,
    train_lm,
)

CODEC_CORE = Path(__file__).resolve().parents[2] / "01-video-tokenizer" / "core"
sys.path.insert(0, str(CODEC_CORE))
from video_codec import N_FRAMES

# Declared before this run, per mission.yaml's cost_budget discipline: this
# stage trains on the local CPU lane only (no Modal spend), and the run
# stops and reports if wall-clock crosses this ceiling before completing.
COMPUTE_CEILING_SECONDS = 1800.0  # 30 minutes


def frame_repeat_baseline(eval_clips: torch.Tensor, prompt_frames: int) -> torch.Tensor:
    """Repeat frame `prompt_frames - 1` for every frame from `prompt_frames`
    onward -- the mission's declared "no learning" control."""
    last_seen = eval_clips[:, prompt_frames - 1 : prompt_frames]  # (N, 1, 3, H, W)
    repeated = last_seen.expand(-1, N_FRAMES - prompt_frames, -1, -1, -1)
    return repeated


def run(codec_steps: int, lm_steps: int, lm_lr: float, prompt_frames: int, seed: int, out: Path) -> dict:
    t0 = time.perf_counter()

    codec, train_clips, eval_clips = retrain_codec(CodecRecipe(steps=codec_steps, seed=seed))
    codec_wall_clock = time.perf_counter() - t0
    if codec_wall_clock > COMPUTE_CEILING_SECONDS:
        return {"verdict": "CEILING_EXCEEDED", "stage": "codec", "wall_clock_s": codec_wall_clock}

    train_seq, eval_seq = build_lm_dataset(codec, train_clips, eval_clips)
    block_size = train_seq.shape[1] - 1
    cfg = build_lm_config(block_size)
    lm, lm_wall_clock = train_lm(train_seq, cfg, steps=lm_steps, lr=lm_lr, batch_size=32, seed=seed)
    if time.perf_counter() - t0 > COMPUTE_CEILING_SECONDS:
        return {"verdict": "CEILING_EXCEEDED", "stage": "lm", "wall_clock_s": time.perf_counter() - t0}

    n_eval = eval_seq.shape[0]
    n_new = N_FRAMES - prompt_frames
    prompt = eval_seq[:, : prompt_frames + 1]  # +1 for BOS
    t2 = time.perf_counter()
    generated = generate_greedy(lm, prompt, n_new)
    gen_wall_clock = time.perf_counter() - t2
    predicted_tokens = generated[:, prompt_frames + 1 :]  # drop BOS + conditioning tokens
    oracle_tokens = eval_seq[:, prompt_frames + 1 :]

    with torch.no_grad():
        predicted_pixels = codec.decode(predicted_tokens)  # (N, n_new, 3, H, W)
        oracle_pixels = codec.decode(oracle_tokens)

    real_future = eval_clips[:, prompt_frames:]  # (N, n_new, 3, H, W)
    lm_mse = nn.functional.mse_loss(predicted_pixels, real_future).item()
    oracle_mse = nn.functional.mse_loss(oracle_pixels, real_future).item()

    baseline_pixels = frame_repeat_baseline(eval_clips, prompt_frames)
    baseline_mse = nn.functional.mse_loss(baseline_pixels, real_future).item()

    exact_match = (predicted_tokens == oracle_tokens).all(dim=1).float().mean().item()

    total_wall_clock = time.perf_counter() - t0

    result = {
        "seed": seed,
        "codec_steps": codec_steps,
        "lm_steps": lm_steps,
        "lm_lr": lm_lr,
        "prompt_frames": prompt_frames,
        "n_new_frames": n_new,
        "n_eval_clips": n_eval,
        "reconstruction_mse": {
            "lm_completion": lm_mse,
            "oracle_tokens": oracle_mse,
            "frame_repeat_baseline": baseline_mse,
        },
        "beats_frame_repeat_baseline": lm_mse < baseline_mse,
        "predicted_token_sequence_exact_match_rate": exact_match,
        "vocab_size_including_bos": len(range(BOS_TOKEN + 1)),
        "compute": {
            "codec_wall_clock_s": codec_wall_clock,
            "lm_train_wall_clock_s": lm_wall_clock,
            "generation_wall_clock_s": gen_wall_clock,
            "total_wall_clock_s": total_wall_clock,
            "compute_ceiling_s": COMPUTE_CEILING_SECONDS,
            "ceiling_exceeded": total_wall_clock > COMPUTE_CEILING_SECONDS,
            "compute_lane": "local CPU (no CUDA GPU available in this environment)",
            "dollar_cost": 0.0,
        },
        "verdict": "MET" if lm_mse < baseline_mse else "NOT_MET",
    }

    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"generation-seed{seed}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out_path}")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--codec-steps", type=int, default=800)
    ap.add_argument("--lm-steps", type=int, default=400)
    ap.add_argument("--lm-lr", type=float, default=3e-3)
    ap.add_argument("--prompt-frames", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("../runs"))
    args = ap.parse_args()
    run(args.codec_steps, args.lm_steps, args.lm_lr, args.prompt_frames, args.seed, args.out)


if __name__ == "__main__":
    main()
