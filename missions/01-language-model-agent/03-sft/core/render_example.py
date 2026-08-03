"""Render one real no_robots record and print its real loss mask.

`README.md`'s worked example for `render_and_mask` uses a hypothetical
three-token turn ("yes."). This script runs the actual function in `sft.py`
against an actual row of `HuggingFaceH4/no_robots` and writes out the actual
token-by-token mask, so the mechanism has one real record backing it, not
only an invented one.

It reuses `_rows` and `render_and_mask` from `sft.py` unmodified — this is
not a second implementation of dataset loading or masking, only a report of
what those functions already do on one row.

Run:  python render_example.py --tokenizer ../../01-tokenizer/tokenizer_hf.json \\
          --out ../runs/2026-08-03-render-example.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sft import IGNORE_INDEX, IM_END, IM_START, PAD_ID, _rows, render_and_mask
from tokenizers import Tokenizer

SPECIAL = {IM_START: "<|im_start|>", IM_END: "<|im_end|>", PAD_ID: "<|pad|>"}


def decode_token(tok: Tokenizer, token_id: int) -> str:
    if token_id in SPECIAL:
        return SPECIAL[token_id]
    return tok.decode([token_id])


def find_example(dataset: str, split: str, tok: Tokenizer, lo: int, hi: int):
    """First two-turn (user, assistant) row whose rendered length is in [lo, hi].

    The size window keeps the printed table short enough to quote in a
    README; it is the only selection criterion, applied in dataset order, so
    picking a record involves no cherry-picking of content or mask ratio.
    """
    for index, row in enumerate(_rows(dataset, split)):
        turns = row["messages"]
        if not turns or turns[-1]["role"] != "assistant" or len(turns) != 2:
            continue
        ids, labels = render_and_mask(turns, tok)
        if lo <= len(ids) <= hi:
            return index, row, ids, labels
    raise RuntimeError(f"no row in {dataset}/{split} rendered to between {lo} and {hi} tokens")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", type=Path, required=True)
    ap.add_argument("--dataset", default="HuggingFaceH4/no_robots")
    ap.add_argument("--split", default="train")
    ap.add_argument("--min-tokens", type=int, default=20)
    ap.add_argument("--max-tokens", type=int, default=45)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    tok = Tokenizer.from_file(str(args.tokenizer))
    index, row, ids, labels = find_example(
        args.dataset, args.split, tok, args.min_tokens, args.max_tokens
    )
    turns = row["messages"]

    rows_out = []
    trained = 0
    for token_id, label in zip(ids, labels):
        piece = decode_token(tok, token_id)
        if label == IGNORE_INDEX:
            mask_col = "-100"
        else:
            trained += 1
            mask_col = decode_token(tok, label)
        rows_out.append((token_id, piece, mask_col))

    lines = []
    lines.append(f"# Real rendered SFT record — {args.dataset}/{args.split}[{index}]\n")
    lines.append(f"category: {row.get('category')!r}\n")
    lines.append("turns:\n")
    for turn in turns:
        lines.append(f"  {turn['role']}: {turn['content']!r}\n")
    lines.append(
        f"\n{len(ids)} tokens total, {trained} trained (labels != -100), "
        f"{trained / len(ids):.1%} of this record's tokens\n"
    )
    # A markdown table cell containing literal "|" (from "<|im_start|>") breaks
    # this repo's MDX renderer, which reads a bare "<" as JSX; a fenced code
    # block is plain text to that renderer, matching the convention already
    # used for the same tokens in README.md's `render_and_mask` walkthrough.
    lines.append("\n```\n")
    header = f"{'i':>3}  {'token id':>8}  {'decoded token':<20} label\n"
    lines.append(header)
    for i, (token_id, piece, mask_col) in enumerate(rows_out):
        lines.append(f"{i:>3}  {token_id:>8}  {piece!r:<20} {mask_col}\n")
    lines.append("```\n")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(lines))
    print(f"{args.dataset}/{args.split}[{index}]: {len(ids)} tokens, {trained} trained")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
