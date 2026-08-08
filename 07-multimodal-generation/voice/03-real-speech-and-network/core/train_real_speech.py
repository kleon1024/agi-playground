"""Does stage 00's codec architecture and stage 01's KV-cache mechanism
still hold on real speech, not procedural tones?

Retrains the *identical* `Codec`/`CodecConfig` (no architecture change) on a
LibriSpeech `dev-clean` subset (2 speakers requested; the speaker-major
slice served 2277 only -- see the mix audit), then reuses
`audio_lm`'s LM training and `streaming_decode`'s naive-vs-cached generation
functions unchanged -- the same reuse discipline stage 01 itself established
for `engine.py`. This script is deliberately a thin orchestrator: every
non-trivial piece of logic already exists in stage 00/01's `core/` and is
imported, not copied.

Run:
    uv run --group torch python train_real_speech.py --codec-steps 600 --lm-steps 800
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import torch
from speech_data import CLIP_LEN, DEFAULT_SPEAKERS, build_dataset
from torch.nn import functional as F

CODEC_DIR = Path(__file__).resolve().parents[2] / "00-audio-codec" / "core"
sys.path.insert(0, str(CODEC_DIR))
from audio_data import write_wav
from codec import Codec, CodecConfig

STREAM_DIR = Path(__file__).resolve().parents[2] / "01-streaming-decode" / "core"
sys.path.insert(0, str(STREAM_DIR))
from audio_lm import build_lm_config, build_lm_dataset, train_lm
from streaming_decode import generate_cached_timed, generate_naive_timed, percentiles


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


def train_speech_codec(train_wf: torch.Tensor, eval_wf: torch.Tensor, steps: int, lr: float, seed: int):
    torch.manual_seed(seed)
    cfg = CodecConfig()
    model = Codec(cfg)
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
    return model, history, eval_mse, eval_tokens


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-train", type=int, default=256)
    ap.add_argument("--n-eval", type=int, default=60)
    ap.add_argument("--speakers", type=str, nargs="+", default=list(DEFAULT_SPEAKERS))
    ap.add_argument("--max-utterances", type=int, default=40)
    ap.add_argument("--codec-steps", type=int, default=600)
    ap.add_argument("--codec-lr", type=float, default=1e-3)
    ap.add_argument("--lm-steps", type=int, default=800)
    ap.add_argument("--prompt-len", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", type=str, default="cpu")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--balanced",
        action="store_true",
        help="use stage 04's per-speaker-bounded balanced builder (the mix-audit "
        "fix) instead of the naive speaker-major slice, so a multi-speaker "
        "request actually serves every requested speaker",
    )
    args = ap.parse_args()

    t0 = time.perf_counter()
    if args.balanced:
        MSP_DIR = Path(__file__).resolve().parents[2] / "04-multi-speaker" / "core"
        sys.path.insert(0, str(MSP_DIR))
        from multi_speaker_data import build_balanced_dataset

        train_clips, eval_clips = build_balanced_dataset(
            args.n_train,
            args.n_eval,
            args.seed,
            speakers=tuple(args.speakers),
            per_speaker_utterances=args.max_utterances,
        )
    else:
        train_clips, eval_clips = build_dataset(
            args.n_train, args.n_eval, args.seed, speakers=tuple(args.speakers), max_utterances=args.max_utterances
        )
    data_wall = time.perf_counter() - t0
    train_wf = torch.stack([c.waveform for c in train_clips])
    eval_wf = torch.stack([c.waveform for c in eval_clips])
    baselines = naive_baselines(train_wf, eval_wf)

    t1 = time.perf_counter()
    codec, codec_history, codec_eval_mse, eval_tokens = train_speech_codec(
        train_wf, eval_wf, steps=args.codec_steps, lr=args.codec_lr, seed=args.seed
    )
    codec_wall = time.perf_counter() - t1
    usage = codebook_usage(eval_tokens, CodecConfig().codebook_size)

    examples_dir = Path(__file__).resolve().parent.parent / "runs" / "example_clips"
    examples_dir.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        eval_recon = codec.decode(eval_tokens)
    codec_examples = []
    for i in range(min(3, eval_wf.shape[0])):
        write_wav(examples_dir / f"real{i}_reference.wav", eval_wf[i])
        write_wav(examples_dir / f"real{i}_reconstructed.wav", eval_recon[i])
        codec_examples.append(
            {
                "clip_index": i,
                "speaker_id": eval_clips[i].speaker_id,
                "utterance_id": eval_clips[i].utterance_id,
                "reference_wav": f"example_clips/real{i}_reference.wav",
                "reconstructed_wav": f"example_clips/real{i}_reconstructed.wav",
                "per_clip_mse": F.mse_loss(eval_recon[i], eval_wf[i]).item(),
            }
        )

    train_seq, eval_seq = build_lm_dataset(codec, train_wf, eval_wf)
    lm_cfg = build_lm_config(block_size=65)
    t2 = time.perf_counter()
    lm = train_lm(train_seq, lm_cfg, steps=args.lm_steps, lr=3e-4, batch_size=32, seed=args.seed)
    lm_wall = time.perf_counter() - t2

    n_new = 64 - args.prompt_len
    max_logit_gaps, tokens_matched = [], []
    early_naive, late_naive, early_cached, late_cached = [], [], [], []
    examples = []
    for i in range(eval_seq.shape[0]):
        prompt_ids = eval_seq[i, : args.prompt_len + 1].tolist()
        naive_ids, naive_logits, naive_times = generate_naive_timed(lm, prompt_ids, n_new, args.device)
        cached_ids, cached_logits, cached_times = generate_cached_timed(
            lm, lm_cfg, prompt_ids, n_new, args.device, max_len=65
        )
        gaps = [float((a - b).abs().max()) for a, b in zip(naive_logits, cached_logits)]
        max_logit_gaps.append(max(gaps))
        tokens_matched.append(naive_ids == cached_ids)
        early_naive.extend(naive_times[:5])
        late_naive.extend(naive_times[-5:])
        early_cached.extend(cached_times[:5])
        late_cached.extend(cached_times[-5:])
        if i < 3:
            examples.append(
                {
                    "clip_index": i,
                    "speaker_id": eval_clips[i].speaker_id,
                    "utterance_id": eval_clips[i].utterance_id,
                    "tokens_match": naive_ids == cached_ids,
                }
            )

    result = {
        "seed": args.seed,
        "speakers": args.speakers,
        "n_train": args.n_train,
        "n_eval": args.n_eval,
        "data_wall_clock_s": data_wall,
        "codec_wall_clock_s": codec_wall,
        "lm_wall_clock_s": lm_wall,
        "codec_history": codec_history,
        "codec_eval_mse": codec_eval_mse,
        "baseline_mse": baselines,
        "beats_silence": codec_eval_mse < baselines["silence"],
        "beats_mean_signal": codec_eval_mse < baselines["mean_signal"],
        "codebook_usage": usage,
        "codec_examples": codec_examples,
        "streaming_correctness": {
            "max_logit_gap_over_all_clips": max(max_logit_gaps),
            "mean_logit_gap": statistics.mean(max_logit_gaps),
            "all_token_sequences_matched": all(tokens_matched),
            "n_clips_total": len(tokens_matched),
        },
        "latency_s_local_cpu": {
            "naive_early_steps": percentiles(early_naive),
            "naive_late_steps": percentiles(late_naive),
            "cached_early_steps": percentiles(early_cached),
            "cached_late_steps": percentiles(late_cached),
        },
        "examples": examples,
    }

    out_path = args.out or (Path(__file__).resolve().parent.parent / "runs" / f"real-speech-seed{args.seed}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"wrote {out_path}")
    print(f"codec eval MSE: {codec_eval_mse:.5f}  vs silence={baselines['silence']:.5f}  mean_signal={baselines['mean_signal']:.5f}")
    print(json.dumps(result["streaming_correctness"], indent=2))
    print(json.dumps(result["latency_s_local_cpu"], indent=2))


if __name__ == "__main__":
    main()
