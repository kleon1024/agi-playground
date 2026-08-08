"""Does the KV-cache decode loop mission 01 built for text tokens work
unchanged for audio tokens, and what does the cache actually buy?

Reuses `KVCache`, `_forward_with_cache`, and `build_rope_cache` directly from
[`engine.py`](../../../01-language-model/05-serve/core/engine.py) --
the same building blocks its own `KVCacheEngine.generate()` wraps, called
directly here because per-step timing and per-step logits (what this stage
needs to measure) are not something that wrapper exposes. No line of
`engine.py` was changed to make this work: the functions are generic over
`Config`/`Transformer`/token ids and were never text-specific in the first
place.

Correctness is checked on **logits**, not generated token ids, following the
exact methodology and stated reason in this repository's own
`tests/test_decode_correctness.py`: an id-level match can pass trivially on
a degenerate model that repeats its input, while a logit-level match cannot.

Run:
    uv run --group torch python streaming_decode.py --n-eval-clips 30 --prompt-len 16
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import torch
from audio_lm import build_lm_config, build_lm_dataset, train_codec, train_lm
from torch.nn import functional as F

ENGINE_DIR = Path(__file__).resolve().parents[4] / "01-language-model" / "05-serve" / "core"
sys.path.insert(0, str(ENGINE_DIR))
from engine import Config, KVCache, Transformer, _forward_with_cache, build_rope_cache

CODEC_DIR = Path(__file__).resolve().parents[2] / "00-audio-codec" / "core"
sys.path.insert(0, str(CODEC_DIR))
from audio_data import CLIP_LEN


@torch.no_grad()
def generate_naive_timed(model: Transformer, prompt_ids: list[int], n_new: int, device: str):
    idx = torch.tensor([prompt_ids], device=device)
    logits_trace, times, out = [], [], []
    for _ in range(n_new):
        t0 = time.perf_counter()
        logits, _ = model(idx)
        step_logits = logits[0, -1].clone()
        next_id = int(step_logits.argmax())
        times.append(time.perf_counter() - t0)
        logits_trace.append(step_logits)
        out.append(next_id)
        idx = torch.cat([idx, torch.tensor([[next_id]], device=device)], dim=1)
    return out, logits_trace, times


@torch.no_grad()
def generate_cached_timed(model: Transformer, cfg: Config, prompt_ids: list[int], n_new: int, device: str, max_len: int):
    cache = KVCache(cfg, max_len, device)
    cos_full, sin_full = build_rope_cache(max_len, cfg.d_head, cfg.rope_theta, device)
    idx = torch.tensor([prompt_ids], device=device)

    t0 = time.perf_counter()
    logits = _forward_with_cache(model, cfg, idx, cache, 0, cos_full, sin_full)
    step_logits = logits[0, -1].clone()
    next_id = int(step_logits.argmax())
    times = [time.perf_counter() - t0]
    logits_trace, out = [step_logits], [next_id]

    pos = len(prompt_ids)
    for _ in range(n_new - 1):
        t0 = time.perf_counter()
        step = torch.tensor([[next_id]], device=device)
        logits = _forward_with_cache(model, cfg, step, cache, pos, cos_full, sin_full)
        step_logits = logits[0, -1].clone()
        next_id = int(step_logits.argmax())
        times.append(time.perf_counter() - t0)
        logits_trace.append(step_logits)
        out.append(next_id)
        pos += 1
    return out, logits_trace, times


def percentiles(values: list[float]) -> dict[str, float]:
    s = sorted(values)
    def pct(p):
        idx = min(len(s) - 1, int(p * len(s)))
        return s[idx]
    return {"p50": pct(0.50), "p95": pct(0.95), "mean": statistics.mean(s)}


def run_latency_stress(vocab_size: int, seq_len: int, seed: int, device: str) -> dict:
    """The 48-token real-audio-completion measurement above is too short for
    naive recompute's O(t) per-step cost to diverge from the cache's O(1)
    one -- fixed per-step Python/tensor overhead dominates at that length.
    This runs one much longer sequence (arbitrary token ids, matching how
    `engine.py`'s own `_bench_naive`/`_bench_kvcache` use `list(range(n))` --
    a pure timing stress test, not a claim about audio quality) to check
    whether the same divergence documented for text in
    `../../../01-language-model/05-serve/README.md` shows up for this
    audio-token vocabulary too, at a length actually long enough to reveal it.
    """
    torch.manual_seed(seed + 2)
    cfg = build_lm_config(block_size=seq_len + 8)
    model = Transformer(cfg).eval()
    prompt_ids = list(range(min(8, vocab_size)))

    _naive_ids, _naive_logits, naive_times = generate_naive_timed(model, prompt_ids, seq_len, device)
    _cached_ids, _cached_logits, cached_times = generate_cached_timed(
        model, cfg, prompt_ids, seq_len, device, max_len=seq_len + 8
    )
    return {
        "seq_len": seq_len,
        "naive_first_10_steps": percentiles(naive_times[:10]),
        "naive_last_10_steps": percentiles(naive_times[-10:]),
        "cached_first_10_steps": percentiles(cached_times[:10]),
        "cached_last_10_steps": percentiles(cached_times[-10:]),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--codec-steps", type=int, default=600)
    ap.add_argument("--lm-steps", type=int, default=800)
    ap.add_argument("--prompt-len", type=int, default=16, help="real codec tokens given as prompt, out of 64")
    ap.add_argument("--n-eval-clips", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", type=str, default="cpu")
    ap.add_argument("--latency-stress-len", type=int, default=400,
                     help="arbitrary-token sequence length for the long-sequence timing-only stress test")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    t_codec0 = time.perf_counter()
    codec, _train_clips, eval_clips, train_wf, eval_wf = train_codec(args.seed, steps=args.codec_steps)
    codec_wall = time.perf_counter() - t_codec0

    train_seq, eval_seq = build_lm_dataset(codec, train_wf, eval_wf)
    lm_cfg = build_lm_config(block_size=65)

    t_lm0 = time.perf_counter()
    lm = train_lm(train_seq, lm_cfg, steps=args.lm_steps, lr=3e-4, batch_size=32, seed=args.seed)
    lm_wall = time.perf_counter() - t_lm0

    n_new = 64 - args.prompt_len
    early_naive, late_naive, early_cached, late_cached = [], [], [], []
    max_logit_gaps = []
    tokens_matched = []
    codec_mse, oracle_mse = [], []
    examples = []

    n_clips = min(args.n_eval_clips, eval_seq.shape[0])
    for i in range(n_clips):
        prompt_ids = eval_seq[i, : args.prompt_len + 1].tolist()  # +1 for BOS
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

        full_tokens = torch.tensor([eval_seq[i, 1 : args.prompt_len + 1].tolist() + cached_ids])
        with torch.no_grad():
            recon = codec.decode(full_tokens)
        mse = F.mse_loss(recon[0], eval_wf[i]).item()
        codec_mse.append(mse)

        oracle_tokens = eval_seq[i, 1:].unsqueeze(0)
        with torch.no_grad():
            oracle_recon = codec.decode(oracle_tokens)
        oracle_mse.append(F.mse_loss(oracle_recon[0], eval_wf[i]).item())

        if i < 3:
            examples.append(
                {
                    "clip_index": i,
                    "notes": eval_clips[i].notes,
                    "prompt_len_tokens": args.prompt_len,
                    "real_prefix_tokens": eval_seq[i, 1 : args.prompt_len + 1].tolist(),
                    "generated_completion_tokens": cached_ids,
                    "naive_completion_tokens": naive_ids,
                    "tokens_match": naive_ids == cached_ids,
                    "reconstruction_mse": mse,
                }
            )

    silence_mse = F.mse_loss(torch.zeros(CLIP_LEN).expand_as(eval_wf), eval_wf).item()
    mean_signal_mse = F.mse_loss(train_wf.mean(dim=0).expand_as(eval_wf), eval_wf).item()

    stress = run_latency_stress(
        vocab_size=lm_cfg.vocab_size, seq_len=args.latency_stress_len, seed=args.seed, device=args.device
    )

    result = {
        "seed": args.seed,
        "codec_steps": args.codec_steps,
        "lm_steps": args.lm_steps,
        "codec_wall_clock_s": codec_wall,
        "lm_wall_clock_s": lm_wall,
        "prompt_len": args.prompt_len,
        "n_new_tokens": n_new,
        "n_eval_clips": n_clips,
        "device": args.device,
        "correctness": {
            "max_logit_gap_over_all_clips": max(max_logit_gaps),
            "mean_logit_gap": statistics.mean(max_logit_gaps),
            "n_clips_tokens_matched": sum(tokens_matched),
            "n_clips_total": len(tokens_matched),
            "all_token_sequences_matched": all(tokens_matched),
        },
        "latency_s": {
            "naive_early_steps": percentiles(early_naive),
            "naive_late_steps": percentiles(late_naive),
            "cached_early_steps": percentiles(early_cached),
            "cached_late_steps": percentiles(late_cached),
        },
        "reconstruction_mse": {
            "lm_completion_mean": statistics.mean(codec_mse),
            "oracle_tokens_mean": statistics.mean(oracle_mse),
            "silence_baseline": silence_mse,
            "mean_signal_baseline": mean_signal_mse,
        },
        "examples": examples,
        "latency_stress": stress,
    }

    out_path = args.out or (Path(__file__).resolve().parent.parent / "runs" / f"streaming-seed{args.seed}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"wrote {out_path}")
    print(json.dumps(result["correctness"], indent=2))
    print(json.dumps(result["latency_s"], indent=2))
    print(json.dumps(result["reconstruction_mse"], indent=2))
    print(json.dumps(result["latency_stress"], indent=2))


if __name__ == "__main__":
    main()
