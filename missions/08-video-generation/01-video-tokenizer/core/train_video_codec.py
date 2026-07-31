"""Train `VideoCodec` against stage 00's real clips, and check whether the
resulting per-frame reconstruction beats two naive, no-learning baselines.

Frames are normalized to [-1, 1] the same way mission 05's patch embed
normalizes pixels, and reconstruction loss is plain per-pixel MSE plus the
codec's own VQ commitment loss -- the identical recipe mission 07's
`train_codec.py` uses for audio, since nothing about that recipe is
audio-specific either.

Usage:
    python train_video_codec.py --steps 600 --batch-size 16 --lr 1e-3 --seed 0
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
from video_codec import HEIGHT, N_FRAMES, WIDTH, CodecConfig, VideoCodec

DATA_DIR = Path(__file__).resolve().parents[2] / "00-synthetic-video-dataset" / "data" / "raw"
FIXTURES_DIR = Path(__file__).resolve().parents[2] / "00-synthetic-video-dataset" / "fixtures"


def load_clips(path: Path) -> torch.Tensor:
    """Read a stage-00 jsonl manifest into a (N, T, 3, H, W) float tensor in
    [-1, 1] -- pixels/127.5 - 1.0, the same normalization mission 05's patch
    embed uses."""
    rows = []
    with path.open() as fh:
        for line in fh:
            ex = json.loads(line)
            frames = ex["frames_pixels_rgb"]  # (T, H*W, 3) ints in [0, 255]
            rows.append(frames)
    arr = torch.tensor(rows, dtype=torch.float32)  # (N, T, H*W, 3)
    arr = arr.view(arr.shape[0], N_FRAMES, HEIGHT, WIDTH, 3).permute(0, 1, 4, 2, 3).contiguous()
    return (arr / 127.5) - 1.0


def naive_baselines(train: torch.Tensor, eval_: torch.Tensor) -> dict:
    """Two no-learning controls, matching mission 07 stage 00's convention:
    a flat-background prediction (white, this dataset's fixed background),
    and the pixel-wise mean frame over the training set, broadcast to every
    frame of every eval clip."""
    background = torch.ones_like(eval_)  # normalized white == 1.0
    background_mse = nn.functional.mse_loss(background, eval_).item()

    mean_frame = train.mean(dim=(0, 1), keepdim=True)  # (1, 1, 3, H, W)
    mean_pred = mean_frame.expand_as(eval_)
    mean_mse = nn.functional.mse_loss(mean_pred, eval_).item()

    return {"background": background_mse, "mean_frame": mean_mse}


def shape_vs_background_mse(pred: torch.Tensor, eval_: torch.Tensor) -> dict:
    """Split eval MSE into shape pixels (reference deviates from pure white
    background by more than 0.15) and background pixels. Beating a naive
    baseline in aggregate MSE alone does not say whether a model learned the
    shape or just matched background slightly better -- this is the check
    that distinguishes the two, since background is over 94% of every
    frame's pixels by construction and can dominate an aggregate number."""
    bg = torch.ones(1, 1, 3, 1, 1)
    shape_mask = (eval_ - bg).abs().sum(dim=2) > 0.15  # (N, T, H, W)
    diff2 = (pred - eval_).pow(2).mean(dim=2)  # (N, T, H, W)
    return {
        "shape_pixel_fraction": shape_mask.float().mean().item(),
        "shape_mse": diff2[shape_mask].mean().item(),
        "background_mse": diff2[~shape_mask].mean().item(),
    }


def codebook_usage(all_tokens: torch.Tensor, codebook_size: int) -> dict:
    flat = all_tokens.reshape(-1)
    counts = torch.bincount(flat, minlength=codebook_size).float()
    probs = counts / counts.sum()
    nonzero = probs[probs > 0]
    entropy = -(nonzero * nonzero.log()).sum().item()
    max_entropy = torch.log(torch.tensor(float(codebook_size))).item()
    return {
        "unique_codes_used": int((counts > 0).sum().item()),
        "codebook_size": codebook_size,
        "entropy": entropy,
        "max_entropy": max_entropy,
        "entropy_ratio": entropy / max_entropy,
    }


@torch.no_grad()
def init_codebook_from_data(model: VideoCodec, train_clips: torch.Tensor, sample_size: int = 256) -> None:
    """Seed the codebook from real encoder outputs instead of its default
    near-zero random init.

    A pilot run of this exact codec collapsed to a single used code even
    after 600 steps at lr up to 3e-3 -- unlike mission 07's audio codec,
    which escaped its own local minimum with more steps. A single-clip
    overfitting sanity check (see runs/) showed why: `VectorQuantizer`'s
    codebook initializes every entry to `uniform(-1/64, 1/64)`, a ball of
    radius ~0.016 around the origin, while a randomly-initialized conv
    encoder's outputs land far outside that ball at a much larger, arbitrary
    scale. Every codebook entry is then nearly equidistant from any given
    encoder output, so the nearest-neighbor argmin picks one index almost
    arbitrarily and consistently; gradient only updates whichever entry gets
    picked (an `nn.Embedding` lookup only backprops into the selected row),
    so the other 63 entries never move and never become competitive. This
    does not modify `VectorQuantizer` itself -- it only sets its embedding
    weights, once, before training starts, to a random sample of real
    encoder outputs on real data, so every codebook entry starts inside the
    actual data distribution instead of at the origin."""
    idx = torch.randint(0, train_clips.shape[0], (sample_size,))
    z = model.encoder(train_clips[idx])  # (sample_size, T, latent_dim)
    flat = z.reshape(-1, z.shape[-1])
    codebook_size = model.vq.codebook.weight.shape[0]
    pick = torch.randint(0, flat.shape[0], (codebook_size,))
    model.vq.codebook.weight.data.copy_(flat[pick])


@torch.no_grad()
def revive_dead_codes(model: VideoCodec, batch: torch.Tensor, used_counts: torch.Tensor) -> int:
    """Reset codebook entries unused since the last check to a perturbed
    sample of the current batch's encoder outputs.

    Data-dependent init alone was not enough: a single-clip overfit check
    (see the docstring above and `runs/`) showed that once training starts,
    whichever code the argmin happens to favor keeps winning -- only a
    selected embedding row receives gradient, so an early, arbitrary winner
    entrenches itself and every other row stays exactly where it was seeded,
    permanently uncompetitive. This is the standard fix real neural codecs
    (SoundStream, EnCodec) use: periodically replace codebook rows that
    received zero assignments in a recent window with fresh, perturbed
    samples from the live data distribution, so a dead code gets another
    chance instead of staying dead for the rest of training. Returns how
    many codes were revived, so a run can report whether this ever fired."""
    z = model.encoder(batch)
    flat = z.reshape(-1, z.shape[-1])
    dead = (used_counts == 0).nonzero(as_tuple=True)[0]
    if dead.numel() == 0:
        return 0
    pick = torch.randint(0, flat.shape[0], (dead.numel(),))
    noise = torch.randn_like(flat[pick]) * 0.01
    model.vq.codebook.weight.data[dead] = flat[pick] + noise
    return dead.numel()


def train(
    steps: int, batch_size: int, lr: float, seed: int, revive_every: int = 20
) -> tuple[dict, VideoCodec, torch.Tensor]:
    torch.manual_seed(seed)
    t0 = time.perf_counter()

    train_clips = load_clips(DATA_DIR / "train.jsonl")
    eval_clips = load_clips(DATA_DIR / "eval.jsonl")

    cfg = CodecConfig()
    model = VideoCodec(cfg)
    init_codebook_from_data(model, train_clips)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)

    n_train = train_clips.shape[0]
    losses = []
    used_counts = torch.zeros(cfg.codebook_size, dtype=torch.long)
    total_revivals = 0
    for step in range(steps):
        idx = torch.randint(0, n_train, (batch_size,))
        batch = train_clips[idx]
        recon, tokens, vq_loss = model(batch)
        recon_loss = nn.functional.mse_loss(recon, batch)
        loss = recon_loss + 0.25 * vq_loss
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(recon_loss.item())
        used_counts += torch.bincount(tokens.reshape(-1), minlength=cfg.codebook_size)

        if (step + 1) % revive_every == 0:
            total_revivals += revive_dead_codes(model, batch, used_counts)
            used_counts.zero_()

    model.eval()
    with torch.no_grad():
        eval_recon, eval_tokens, _ = model(eval_clips)
        eval_mse = nn.functional.mse_loss(eval_recon, eval_clips).item()

    baselines = naive_baselines(train_clips, eval_clips)
    usage = codebook_usage(eval_tokens, cfg.codebook_size)
    shape_bg = shape_vs_background_mse(eval_recon, eval_clips)
    baseline_shape_bg = {
        "background": shape_vs_background_mse(torch.ones_like(eval_clips), eval_clips),
        "mean_frame": shape_vs_background_mse(
            train_clips.mean(dim=(0, 1), keepdim=True).expand_as(eval_clips), eval_clips
        ),
    }
    wall_clock = time.perf_counter() - t0

    result = {
        "seed": seed,
        "steps": steps,
        "batch_size": batch_size,
        "lr": lr,
        "n_train_clips": n_train,
        "n_eval_clips": eval_clips.shape[0],
        "eval_mse_codec": eval_mse,
        "baseline_mse": baselines,
        "shape_vs_background": {"codec": shape_bg, "baselines": baseline_shape_bg},
        "beats_background": eval_mse < baselines["background"],
        "beats_mean_frame": eval_mse < baselines["mean_frame"],
        "codebook_usage": usage,
        "dead_codes_revived_total": total_revivals,
        "revive_every": revive_every,
        "final_train_recon_loss_last50_mean": sum(losses[-50:]) / len(losses[-50:]),
        "wall_clock_s": wall_clock,
    }
    return result, model, eval_clips


def write_example_frames(model: VideoCodec, eval_clips: torch.Tensor, out_dir: Path, n: int = 3) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        recon, _tokens, _ = model(eval_clips[:n])
    for i in range(n):
        for t in [0, N_FRAMES - 1]:
            ref = ((eval_clips[i, t] + 1.0) * 127.5).clamp(0, 255).byte()
            rec = ((recon[i, t] + 1.0) * 127.5).clamp(0, 255).byte()
            _write_ppm(out_dir / f"eval{i}_frame{t}_reference.ppm", ref)
            _write_ppm(out_dir / f"eval{i}_frame{t}_reconstructed.ppm", rec)


def _write_ppm(path: Path, chw: torch.Tensor) -> None:
    _c, h, w = chw.shape
    header = f"P6\n{w} {h}\n255\n".encode("ascii")
    body = chw.permute(1, 2, 0).contiguous().numpy().tobytes()
    path.write_bytes(header + body)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("../runs"))
    args = ap.parse_args()

    result, model, eval_clips = train(args.steps, args.batch_size, args.lr, args.seed)
    write_example_frames(model, eval_clips, args.out / "example_frames", n=3)

    out_path = args.out / f"video-codec-seed{args.seed}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
