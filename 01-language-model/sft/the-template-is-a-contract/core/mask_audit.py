"""The chat template is a contract. Measure the three places it can
drift.

Stage 03's SFT renders every conversation as
`<|im_start|>role\ncontent<|im_end|>\n` and trains only on the assistant
turn. That is a contract, not a formatting detail, and this audit
measures the three properties the contract depends on, using the real
frozen tokenizer and the real masker on the real no_robots data:

  1. Marker cost. The markers are ids 16385/16386, reserved out of the
     padding gap stage 02 left. If they had NOT been reserved, the
     frozen vocab would byte-split `<|im_start|>` into 8 tokens and
     `<|im_end|>` into 7. The contract is one id per marker, and this
     run measures what forgetting that costs in sequence length.

  2. Train/serve parity. The assistant header is supplied by the
     inference harness, never predicted, so the harness's bytes must
     match the training render exactly. This run encodes the canonical
     header and five plausible drift variants and records the first
     token where each diverges.

  3. What the mask actually trains on. Over the real 9,500 no_robots
     conversations, rendered and packed exactly as the trainer does,
     this run counts how much of each block is a real loss target
     (assistant content plus the closing marker), how much is masked
     context, and how much is template scaffolding. The masker's
     correctness is load-bearing: on this curated set the answer text
     is the majority of every block, so a masking bug trains the model
     to imitate the user.

Deterministic (single seed), CPU-only. Reads HuggingFaceH4/no_robots
from the local dataset cache (offline) and the frozen tokenizer via the
stage 01 HF export; see the runs record for the export command.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np

IM_START = 16385
IM_END = 16386
PAD_ID = 16387


def load_masker(sft_path: Path):
    """Import the real masker and packer from stage 03's trainer."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("sft", sft_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render_and_mask, mod.pack


def marker_cost(tok) -> dict:
    """Reserved-id markers vs byte-split markers on the frozen vocab."""
    byte_start = tok.encode("<|im_start|>").ids
    byte_end = tok.encode("<|im_end|>").ids
    return {
        "im_start_bytes": len(byte_start),
        "im_end_bytes": len(byte_end),
        "im_start_ids": byte_start,
        "im_end_ids": byte_end,
    }


def header_drift(tok) -> list[dict]:
    """Token sequences for the canonical header and plausible variants."""
    canonical = tok.encode("assistant\n").ids
    variants = {
        "assistant (no newline)": "assistant",
        "Assistant\\n (capital)": "Assistant\n",
        " assistant\\n (leading space)": " assistant\n",
        "assistant  \\n (two spaces)": "assistant  \n",
        "assistant\\r\\n (CRLF)": "assistant\r\n",
    }
    out = []
    for name, s in variants.items():
        ids = tok.encode(s).ids
        first = next((i for i, (a, b) in enumerate(zip(canonical, ids))
                      if a != b), min(len(canonical), len(ids)))
        out.append({
            "variant": name,
            "tokens": len(ids),
            "ids": ids,
            "first_divergence": first,
        })
    return out


def density(rows, render_and_mask, pack, tok, block_size: int) -> dict:
    """Render + pack the real data exactly as the trainer does, and
    count what each block is made of."""
    examples = []
    markers_total = 0
    for row in rows:
        turns = row["messages"]
        if not turns or turns[-1]["role"] != "assistant":
            continue
        ids, labels = render_and_mask(turns, tok)
        markers_total += sum(1 for i in ids if i in (IM_START, IM_END))
        examples.append((ids, labels))
    dropped_long = sum(1 for ids, _ in examples
                       if len(ids) > block_size + 1)
    blocks = pack(examples, block_size)

    total = target = context = scaffold = pad = 0
    per_block = []  # target fraction per block
    for ids, labels in blocks:
        n = len(ids)
        for i in range(n):
            if ids[i] == PAD_ID:
                pad += 1
                continue
            if labels[i] != -100:
                target += 1
            elif ids[i] in (IM_START, IM_END):
                scaffold += 1
            else:
                context += 1
        real = n - sum(1 for i in ids if i == PAD_ID)
        tgt = sum(1 for i, lab in enumerate(labels)
                  if lab != -100 and ids[i] != PAD_ID)
        per_block.append(tgt / max(1, real))
        total += real

    per_block = np.array(per_block)
    return {
        "conversations": len(examples),
        "blocks": len(blocks),
        "real_tokens": total,
        "target_tokens": target,
        "context_tokens": context,
        "scaffold_tokens": scaffold,
        "pad_tokens": pad,
        "target_share": target / max(1, total),
        "per_block_p50": float(np.median(per_block)),
        "per_block_min": float(per_block.min()),
        "per_block_p90": float(np.percentile(per_block, 90)),
        "markers_total": markers_total,
        "dropped_long": dropped_long,
    }


def byte_marker_prompt(tok, render_and_mask, rows, n: int) -> dict:
    """One conversation rendered with reserved-id markers vs with the
    marker strings fed through the frozen vocab (the no-reserved-id
    world)."""
    ids_reserved, _ = render_and_mask(rows[0]["messages"], tok)
    start_ids = tok.encode("<|im_start|>").ids
    end_ids = tok.encode("<|im_end|>").ids
    ids_bytes = []
    for i in ids_reserved:
        if i == IM_START:
            ids_bytes += start_ids
        elif i == IM_END:
            ids_bytes += end_ids
        else:
            ids_bytes.append(i)
    return {
        "reserved_tokens": len(ids_reserved),
        "byte_tokens": len(ids_bytes),
        "inflation": len(ids_bytes) / max(1, len(ids_reserved)),
    }


def run(args) -> None:
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    np.random.seed(42)

    from datasets import load_dataset
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(args.tokenizer))
    render_and_mask, pack = load_masker(args.sft_path)
    rows = load_dataset("HuggingFaceH4/no_robots", split="train")
    rows = list(rows.select(range(min(args.rows, len(rows)))))

    mc = marker_cost(tok)
    hd = header_drift(tok)
    dd = density(rows, render_and_mask, pack, tok, args.block_size)
    bm = byte_marker_prompt(tok, render_and_mask, rows, 1)

    print("chat template contract audit (real tokenizer, real masker, "
          f"real no_robots {len(rows):,} conversations):")
    print()
    print("  marker cost on the frozen vocab:")
    print(f"    reserved id: 1 token per marker (ids {IM_START}/{IM_END})")
    print(f"    <|im_start|> byte-split: {mc['im_start_bytes']} tokens "
          f"{mc['im_start_ids']}")
    print(f"    <|im_end|>   byte-split: {mc['im_end_bytes']} tokens "
          f"{mc['im_end_ids']}")
    print()
    canon_ids = tok.encode("assistant\n").ids
    print("  train/serve header parity (canonical "
          f"'assistant\\n' = {canon_ids}):")
    for v in hd:
        print(f"    {v['variant']:<28} {v['tokens']} token(s) {v['ids']} "
              f"first divergence at token {v['first_divergence']}")
    print()
    print(f"  what the mask trains on ({dd['conversations']:,} conversations, "
          f"{dd['blocks']:,} packed blocks of {args.block_size}):")
    print(f"    real tokens:      {dd['real_tokens']:>9,}")
    print(f"    loss targets:    {dd['target_tokens']:>9,} "
          f"({dd['target_share']:.1%} of real tokens)")
    print(f"    masked context:  {dd['context_tokens']:>9,}")
    print(f"    marker scaffold: {dd['scaffold_tokens']:>9,}")
    print(f"    padding:         {dd['pad_tokens']:>9,}")
    print(f"    per-block target share: min {dd['per_block_min']:.1%}, "
          f"p50 {dd['per_block_p50']:.1%}, p90 {dd['per_block_p90']:.1%}")
    byte_extra = dd["markers_total"] * 6.5  # avg (8+7)/2 - 1 per marker
    print(f"    markers: {dd['markers_total']:,}; if byte-split they add "
          f"~{byte_extra:,.0f} tokens (+{byte_extra / dd['real_tokens']:.2%}"
          f" of real tokens)")
    print(f"    long conversations dropped by packing: {dd['dropped_long']:,}")
    print()
    print("  the same conversation in the no-reserved-id world:")
    print(f"    reserved markers: {bm['reserved_tokens']} tokens; "
          f"byte markers: {bm['byte_tokens']} tokens "
          f"({bm['inflation']:.1f}x)")
    print()
    print("  verdict: the template is a contract - one id per marker,")
    print("  byte-exact train/serve parity, and a masker whose whole job")
    print("  is keeping user text out of a loss that is mostly answer")
    print("  on this curated set - except in the long-prompt tail.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", type=Path,
                    default=Path("/tmp/tokenizer_hf.json"))
    ap.add_argument("--sft-path", type=Path,
                    default=Path(__file__).resolve().parents[2]
                    / "core" / "sft.py")
    ap.add_argument("--rows", type=int, default=9500)
    ap.add_argument("--block-size", type=int, default=1024)
    args = ap.parse_args()
    run(args)


if __name__ == "__main__":
    main()
