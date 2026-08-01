"""Retrains the 10-speaker setup from stage 04, swapping in
`ResetCodec` (dead-code reset every 50 steps) instead of the plain `Codec`,
holding everything else identical: same balanced 10-speaker dataset
(`multi_speaker_data.build_balanced_dataset`, imported from stage 04), same
step count, learning rate, and batch size as stage 04's escaped config.

This stage is scoped to the codec-training question only -- stage 04's
seed-dependent finding (18-63/64 codes used) is a codec-training-time
phenomenon, and stage 01/03/04 already established the KV-cache streaming
mechanism holds regardless of speaker count, so this stage does not re-run
the LM/streaming-decode half of stage 04's pipeline; re-testing an already-
settled question would not tell us anything new about the actual question
here.

Run:
    uv run --group torch python train_reset_codec.py --seed 0
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
from audio_data import write_wav
from reset_vq import ResetCodec, ResetConfig

sys.path.pop(sys.path.index(str(CODEC_DIR)))
from codec import CodecConfig


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


def train_reset_codec(
    train_wf: torch.Tensor, eval_wf: torch.Tensor, steps: int, lr: float, seed: int, reset_cfg: ResetConfig
):
    torch.manual_seed(seed)
    cfg = CodecConfig()
    model = ResetCodec(cfg, reset_cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    history = []
    for step in range(steps):
        idx = torch.randint(0, train_wf.shape[0], (32,))
        batch = train_wf[idx]
        recon, _tokens, vq_loss = model(batch)
        recon_loss = F.mse_loss(recon, batch)
        loss = recon_loss + 0.25 * vq_loss
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % 50 == 0:
            record = {"step": step, "recon_loss": recon_loss.item(), "vq_loss": vq_loss.item()}
            history.append(record)
            print(json.dumps(record), flush=True)
    model.eval()
    with torch.no_grad():
        eval_recon, eval_tokens, _ = model(eval_wf)
        eval_mse = F.mse_loss(eval_recon, eval_wf).item()
    return model, history, eval_mse, eval_tokens, eval_recon


def per_speaker_mse(eval_clips: list, eval_wf: torch.Tensor, eval_recon: torch.Tensor) -> dict:
    per_clip = ((eval_recon - eval_wf) ** 2).mean(dim=1)
    by_speaker: dict[str, list] = {}
    for clip, mse in zip(eval_clips, per_clip.tolist()):
        by_speaker.setdefault(clip.speaker_id, []).append(mse)
    return {
        spk: {"n_clips": len(vals), "mean_mse": statistics.mean(vals)}
        for spk, vals in sorted(by_speaker.items())
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-train", type=int, default=400)
    ap.add_argument("--n-eval", type=int, default=100)
    ap.add_argument("--speakers", type=str, nargs="+", default=list(TEN_SPEAKERS))
    ap.add_argument("--per-speaker-utterances", type=int, default=10)
    ap.add_argument("--codec-steps", type=int, default=2000)
    ap.add_argument("--codec-lr", type=float, default=1e-3)
    ap.add_argument("--reset-every", type=int, default=50)
    ap.add_argument("--dead-threshold", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    t0 = time.perf_counter()
    train_clips, eval_clips = build_balanced_dataset(
        args.n_train,
        args.n_eval,
        args.seed,
        speakers=tuple(args.speakers),
        per_speaker_utterances=args.per_speaker_utterances,
    )
    data_wall = time.perf_counter() - t0
    train_wf = torch.stack([c.waveform for c in train_clips])
    eval_wf = torch.stack([c.waveform for c in eval_clips])
    baselines = naive_baselines(train_wf, eval_wf)

    reset_cfg = ResetConfig(reset_every=args.reset_every, dead_threshold=args.dead_threshold)
    t1 = time.perf_counter()
    codec, codec_history, codec_eval_mse, eval_tokens, eval_recon = train_reset_codec(
        train_wf, eval_wf, steps=args.codec_steps, lr=args.codec_lr, seed=args.seed, reset_cfg=reset_cfg
    )
    codec_wall = time.perf_counter() - t1
    usage = codebook_usage(eval_tokens, CodecConfig().codebook_size)
    speaker_breakdown = per_speaker_mse(eval_clips, eval_wf, eval_recon)

    examples_dir = Path(__file__).resolve().parent.parent / "runs" / "example_clips"
    examples_dir.mkdir(parents=True, exist_ok=True)
    codec_examples = []
    for i in range(min(3, eval_wf.shape[0])):
        write_wav(examples_dir / f"reset{i}_reference.wav", eval_wf[i])
        write_wav(examples_dir / f"reset{i}_reconstructed.wav", eval_recon[i])
        codec_examples.append(
            {
                "clip_index": i,
                "speaker_id": eval_clips[i].speaker_id,
                "utterance_id": eval_clips[i].utterance_id,
                "reference_wav": f"example_clips/reset{i}_reference.wav",
                "reconstructed_wav": f"example_clips/reset{i}_reconstructed.wav",
                "per_clip_mse": F.mse_loss(eval_recon[i], eval_wf[i]).item(),
            }
        )

    result = {
        "seed": args.seed,
        "speakers": args.speakers,
        "n_speakers": len(args.speakers),
        "n_train": args.n_train,
        "n_eval": args.n_eval,
        "codec_steps": args.codec_steps,
        "codec_lr": args.codec_lr,
        "reset_every": args.reset_every,
        "dead_threshold": args.dead_threshold,
        "resets_performed": codec.vq.resets_performed,
        "reset_log": codec.vq.reset_log,
        "data_wall_clock_s": data_wall,
        "codec_wall_clock_s": codec_wall,
        "codec_history": codec_history,
        "codec_eval_mse": codec_eval_mse,
        "baseline_mse": baselines,
        "beats_silence": codec_eval_mse < baselines["silence"],
        "beats_mean_signal": codec_eval_mse < baselines["mean_signal"],
        "codebook_usage": usage,
        "per_speaker_mse": speaker_breakdown,
        "codec_examples": codec_examples,
    }

    out_path = args.out or (
        Path(__file__).resolve().parent.parent / "runs" / f"reset-codec-seed{args.seed}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"wrote {out_path}")
    print(f"codec eval MSE: {codec_eval_mse:.5f}  vs silence={baselines['silence']:.5f}  mean_signal={baselines['mean_signal']:.5f}")
    print(f"codebook usage: {usage['unique_codes_used']}/{usage['codebook_size']}  entropy_ratio={usage['entropy_ratio']:.3f}")
    print(f"resets performed: {codec.vq.resets_performed}")


if __name__ == "__main__":
    main()
