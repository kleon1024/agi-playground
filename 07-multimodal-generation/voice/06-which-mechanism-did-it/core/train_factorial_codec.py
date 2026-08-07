"""Runs all four cells of the reset x EMA grid on one seed, back to back.

Everything outside the quantizer is stage 04's setup, unchanged and shared
across the four arms: the same balanced 10-speaker dataset built once per
seed, the same 2000 steps, the same 1e-3 learning rate, the same batch size
of 32, the same evaluation clips. Each arm re-seeds `torch.manual_seed`
immediately before building its model, so all four start from an identical
encoder, decoder, and codebook initialization -- the arms differ only in
which of the two switches is on.

Building the dataset once and reusing it across arms is what makes the
comparison a comparison. Rebuilding it per arm would put a second
uncontrolled variable (which utterances got sampled) inside a difference
that is supposed to isolate one mechanism.

Run:
    uv run --group torch python train_factorial_codec.py --seed 0
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import torch
from torch.nn import functional as F

MULTI_DIR = Path(__file__).resolve().parents[2] / "04-multi-speaker" / "core"
sys.path.insert(0, str(MULTI_DIR))
from multi_speaker_data import CLIP_LEN, TEN_SPEAKERS, build_balanced_dataset

CODEC_DIR = Path(__file__).resolve().parents[2] / "00-audio-codec" / "core"
sys.path.insert(0, str(CODEC_DIR))
from codec import CodecConfig
from factorial_vq import ARMS, ArmConfig, FactorialCodec, arm_a_matches_stage_00


def naive_baselines(train_wf: torch.Tensor, eval_wf: torch.Tensor) -> dict[str, float]:
    silence = torch.zeros(CLIP_LEN)
    mean_signal = train_wf.mean(dim=0)
    return {
        "silence": F.mse_loss(silence.expand_as(eval_wf), eval_wf).item(),
        "mean_signal": F.mse_loss(mean_signal.expand_as(eval_wf), eval_wf).item(),
    }


def codebook_usage(tokens: torch.Tensor, codebook_size: int) -> dict:
    counts = torch.bincount(tokens.reshape(-1), minlength=codebook_size).float()
    probs = counts / counts.sum()
    nonzero = probs[probs > 0]
    entropy = -(nonzero * nonzero.log()).sum().item()
    max_entropy = torch.log(torch.tensor(float(codebook_size))).item()
    return {
        "unique_codes_used": int((counts > 0).sum()),
        "codebook_size": codebook_size,
        "entropy_ratio": entropy / max_entropy,
    }


def per_speaker_mse(eval_clips: list, eval_wf: torch.Tensor, eval_recon: torch.Tensor) -> dict:
    per_clip = ((eval_recon - eval_wf) ** 2).mean(dim=1)
    by_speaker: dict[str, list] = {}
    for clip, mse in zip(eval_clips, per_clip.tolist()):
        by_speaker.setdefault(clip.speaker_id, []).append(mse)
    return {
        spk: {"n_clips": len(vals), "mean_mse": statistics.mean(vals)}
        for spk, vals in sorted(by_speaker.items())
    }


def train_arm(
    arm: ArmConfig,
    train_wf: torch.Tensor,
    eval_wf: torch.Tensor,
    eval_clips: list,
    steps: int,
    lr: float,
    seed: int,
) -> dict:
    torch.manual_seed(seed)
    model = FactorialCodec(CodecConfig(), arm)
    # With the EMA arm on, `codebook.weight` has requires_grad False, so it is
    # not in this list at all -- the optimizer never sees the tensor the EMA
    # rule owns.
    trainable = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(trainable, lr=lr)

    history = []
    t0 = time.perf_counter()
    for step in range(steps):
        idx = torch.randint(0, train_wf.shape[0], (32,))
        batch = train_wf[idx]
        recon, _tokens, vq_loss = model(batch)
        recon_loss = F.mse_loss(recon, batch)
        loss = recon_loss + 0.25 * vq_loss
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % 100 == 0:
            record = {"step": step, "recon_loss": recon_loss.item(), "vq_loss": vq_loss.item()}
            history.append(record)
            print(json.dumps({"arm": arm.label, **record}), flush=True)
    wall = time.perf_counter() - t0

    model.eval()
    with torch.no_grad():
        eval_recon, eval_tokens, _ = model(eval_wf)
        eval_mse = F.mse_loss(eval_recon, eval_wf).item()

    return {
        "arm": arm.label,
        "dead_code_reset": arm.dead_code_reset,
        "ema_codebook": arm.ema_codebook,
        "codebook_is_gradient_trained": model.vq.codebook.weight.requires_grad,
        "n_trainable_tensors": len(trainable),
        "wall_clock_s": wall,
        "history": history,
        "eval_mse": eval_mse,
        "codebook_usage": codebook_usage(eval_tokens, CodecConfig().codebook_size),
        "resets_performed": model.vq.resets_performed,
        "n_reset_events": len(model.vq.reset_log),
        "per_speaker_mse": per_speaker_mse(eval_clips, eval_wf, eval_recon),
    }


def main_effects(arms: dict[str, dict]) -> dict:
    """Each mechanism's effect measured twice: once with the other switch off,
    once with it on. Agreement means the mechanisms are roughly additive;
    disagreement is an interaction, and it is a finding, not a failure."""

    def d(after: str, before: str, key: str) -> float:
        return arms[after]["codebook_usage"][key] - arms[before]["codebook_usage"][key]

    def dmse(after: str, before: str) -> float:
        return arms[after]["eval_mse"] - arms[before]["eval_mse"]

    return {
        "reset_effect_without_ema": {
            "d_unique_codes": d("reset-only", "plain", "unique_codes_used"),
            "d_entropy_ratio": d("reset-only", "plain", "entropy_ratio"),
            "d_eval_mse": dmse("reset-only", "plain"),
        },
        "reset_effect_with_ema": {
            "d_unique_codes": d("reset+ema", "ema-only", "unique_codes_used"),
            "d_entropy_ratio": d("reset+ema", "ema-only", "entropy_ratio"),
            "d_eval_mse": dmse("reset+ema", "ema-only"),
        },
        "ema_effect_without_reset": {
            "d_unique_codes": d("ema-only", "plain", "unique_codes_used"),
            "d_entropy_ratio": d("ema-only", "plain", "entropy_ratio"),
            "d_eval_mse": dmse("ema-only", "plain"),
        },
        "ema_effect_with_reset": {
            "d_unique_codes": d("reset+ema", "reset-only", "unique_codes_used"),
            "d_entropy_ratio": d("reset+ema", "reset-only", "entropy_ratio"),
            "d_eval_mse": dmse("reset+ema", "reset-only"),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-train", type=int, default=400)
    ap.add_argument("--n-eval", type=int, default=100)
    ap.add_argument("--per-speaker-utterances", type=int, default=10)
    ap.add_argument("--codec-steps", type=int, default=2000)
    ap.add_argument("--codec-lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    parity = arm_a_matches_stage_00(seed=args.seed)
    assert all(
        parity[k]
        for k in ("codebook_init_identical", "quantized_identical", "tokens_identical", "commitment_loss_identical")
    ), f"the (off, off) arm is not stage 00's quantizer: {parity}"

    t0 = time.perf_counter()
    train_clips, eval_clips = build_balanced_dataset(
        args.n_train,
        args.n_eval,
        args.seed,
        speakers=TEN_SPEAKERS,
        per_speaker_utterances=args.per_speaker_utterances,
    )
    data_wall = time.perf_counter() - t0
    train_wf = torch.stack([c.waveform for c in train_clips])
    eval_wf = torch.stack([c.waveform for c in eval_clips])
    baselines = naive_baselines(train_wf, eval_wf)

    arms: dict[str, dict] = {}
    for arm in ARMS:
        print(f"\n=== arm {arm.label} (reset={arm.dead_code_reset}, ema={arm.ema_codebook})", flush=True)
        arms[arm.label] = train_arm(
            arm, train_wf, eval_wf, eval_clips, args.codec_steps, args.codec_lr, args.seed
        )

    result = {
        "stage": "06-which-mechanism-did-it",
        "seed": args.seed,
        "n_speakers": len(TEN_SPEAKERS),
        "n_train": args.n_train,
        "n_eval": args.n_eval,
        "codec_steps": args.codec_steps,
        "codec_lr": args.codec_lr,
        "arm_a_parity_with_stage_00": parity,
        "data_wall_clock_s": data_wall,
        "baseline_mse": baselines,
        "arms": arms,
        "main_effects": main_effects(arms),
        "compute_lane": "local CPU (no CUDA GPU available in this environment)",
        "dollar_cost": 0.0,
    }

    out_path = args.out or (
        Path(__file__).resolve().parent.parent / "runs" / f"factorial-codec-seed{args.seed}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))

    print(f"\nwrote {out_path}")
    print(f"{'arm':<12} {'codes':>6} {'entropy':>8} {'eval MSE':>10}")
    for label, a in arms.items():
        u = a["codebook_usage"]
        print(f"{label:<12} {u['unique_codes_used']:>6} {u['entropy_ratio']:>8.3f} {a['eval_mse']:>10.5f}")


if __name__ == "__main__":
    main()
