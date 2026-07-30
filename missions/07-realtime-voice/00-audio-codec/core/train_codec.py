"""Train the codec on the synthetic tone-sequence dataset and measure
whether it beats the naive baselines mission.yaml names: silence (predict
all zeros) and mean-signal (predict the training set's average waveform,
the same shape regardless of what clip is actually being reconstructed).
Beating both is necessary before this codec's token sequence is worth
handing to stage 01's streaming decode loop at all -- a codec that cannot
reconstruct better than a fixed constant has not learned anything about the
waveform to put in its tokens.

Run:
    uv run --group torch python train_codec.py --steps 300 --seed 0
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from audio_data import CLIP_LEN, build_dataset, write_wav
from codec import Codec, CodecConfig
from torch.nn import functional as F


def naive_baselines(train_waveforms: torch.Tensor, eval_waveforms: torch.Tensor) -> dict[str, float]:
    silence = torch.zeros(CLIP_LEN)
    mean_signal = train_waveforms.mean(dim=0)
    mse_silence = F.mse_loss(silence.expand_as(eval_waveforms), eval_waveforms).item()
    mse_mean = F.mse_loss(mean_signal.expand_as(eval_waveforms), eval_waveforms).item()
    return {"silence": mse_silence, "mean_signal": mse_mean}


def codebook_usage(tokens: torch.Tensor, codebook_size: int) -> dict:
    flat = tokens.reshape(-1)
    counts = torch.bincount(flat, minlength=codebook_size).float()
    probs = counts / counts.sum()
    nonzero = probs[probs > 0]
    entropy = -(nonzero * nonzero.log()).sum().item()
    max_entropy = torch.log(torch.tensor(float(codebook_size))).item()
    return {
        "unique_codes_used": int((counts > 0).sum()),
        "codebook_size": codebook_size,
        "entropy": entropy,
        "max_entropy": max_entropy,
        "entropy_ratio": entropy / max_entropy,
    }


def train(args: argparse.Namespace) -> dict:
    torch.manual_seed(args.seed)
    train_clips, eval_clips = build_dataset(args.n_train, args.n_eval, args.seed)
    train_wf = torch.stack([c.waveform for c in train_clips])
    eval_wf = torch.stack([c.waveform for c in eval_clips])

    baselines = naive_baselines(train_wf, eval_wf)

    cfg = CodecConfig()
    model = Codec(cfg)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    t0 = time.perf_counter()
    history = []
    for step in range(args.steps):
        idx = torch.randint(0, train_wf.shape[0], (args.batch_size,))
        batch = train_wf[idx]
        recon, _tokens, vq_loss = model(batch)
        recon_loss = F.mse_loss(recon, batch)
        loss = recon_loss + args.commitment_weight * vq_loss

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

        if step % args.log_every == 0:
            record = {"step": step, "recon_loss": recon_loss.item(), "vq_loss": vq_loss.item()}
            history.append(record)
            print(json.dumps(record), flush=True)
    elapsed = time.perf_counter() - t0

    model.eval()
    with torch.no_grad():
        eval_recon, eval_tokens, eval_vq_loss = model(eval_wf)
        eval_mse = F.mse_loss(eval_recon, eval_wf).item()

    usage = codebook_usage(eval_tokens, cfg.codebook_size)

    examples_dir = Path(__file__).resolve().parent.parent / "runs" / "example_clips"
    examples_dir.mkdir(parents=True, exist_ok=True)
    example_records = []
    for i in range(min(3, eval_wf.shape[0])):
        write_wav(examples_dir / f"eval{i}_reference.wav", eval_wf[i])
        write_wav(examples_dir / f"eval{i}_reconstructed.wav", eval_recon[i])
        example_records.append(
            {
                "clip_index": i,
                "notes": eval_clips[i].notes,
                "tokens": eval_tokens[i].tolist(),
                "reference_wav": f"example_clips/eval{i}_reference.wav",
                "reconstructed_wav": f"example_clips/eval{i}_reconstructed.wav",
                "per_clip_mse": F.mse_loss(eval_recon[i], eval_wf[i]).item(),
            }
        )

    return {
        "seed": args.seed,
        "steps": args.steps,
        "n_train": args.n_train,
        "n_eval": args.n_eval,
        "wall_clock_s": elapsed,
        "history": history,
        "eval_mse_codec": eval_mse,
        "eval_vq_loss": eval_vq_loss.item(),
        "baseline_mse": baselines,
        "beats_silence": eval_mse < baselines["silence"],
        "beats_mean_signal": eval_mse < baselines["mean_signal"],
        "codebook_usage": usage,
        "examples": example_records,
        "tokens_per_clip": eval_tokens.shape[1],
    }


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train the from-scratch audio codec (mission 07 stage 00).")
    p.add_argument("--steps", type=int, default=300)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--n-train", type=int, default=512)
    p.add_argument("--n-eval", type=int, default=100)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--commitment-weight", type=float, default=0.25)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--log-every", type=int, default=20)
    p.add_argument("--out", type=Path, default=None)
    return p


def main() -> None:
    args = build_argparser().parse_args()
    result = train(args)
    out_path = args.out or (Path(__file__).resolve().parent.parent / "runs" / f"codec-seed{args.seed}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"wrote {out_path}")
    print(f"eval MSE: codec={result['eval_mse_codec']:.5f}  silence={result['baseline_mse']['silence']:.5f}  "
          f"mean_signal={result['baseline_mse']['mean_signal']:.5f}")
    print(f"codebook usage: {result['codebook_usage']}")


if __name__ == "__main__":
    main()
