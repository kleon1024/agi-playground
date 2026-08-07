"""Tokenize Tiny Shakespeare into the train.bin/val.bin shape train.py reads.

The recorded stage-02 pipeline tokenizes FineWeb-Edu parquet via
`prepare_data.py`. This run instead trains a small base on Tiny Shakespeare
(the same corpus foundations/01-first-training-loop uses), because a small
base is the whole point of the model-size chapter and FineWeb-Edu is not
available in this lane. The output format is identical to `prepare_data.py`'s:
uint16 token ids, one document-separator id per line, validation taken from
the front of the stream.

Run:
    uv run --with tokenizers python tokenize_shakespeare.py \
        /tmp/shakespeare/input.txt /tmp/shakespeare/tok.json \
        --out-dir /tmp/shakespeare/tokens --val-tokens 30000
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input_txt", type=Path)
    ap.add_argument("tokenizer", type=Path, help="HF tokenizers JSON (prod/hf_tokenizer.py export)")
    ap.add_argument("--out-dir", type=Path, default=Path("tokens"))
    ap.add_argument("--val-tokens", type=int, default=30_000)
    ap.add_argument("--batch", type=int, default=1000)
    args = ap.parse_args()

    tok = Tokenizer.from_file(str(args.tokenizer))
    vocab_size = tok.get_vocab_size()
    doc_sep = vocab_size  # DOC_SEP_OFFSET = 0, same as prepare_data.py
    assert doc_sep < 65536, "uint16 storage requires vocab_size + 1 < 65536"

    docs = [line for line in args.input_txt.read_text(encoding="utf-8").split("\n") if line.strip()]
    print(f"documents : {len(docs):,}")
    print(f"vocab     : {vocab_size:,}  doc_sep id: {doc_sep:,}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.out_dir / "train.bin"
    val_path = args.out_dir / "val.bin"

    total = 0
    with open(val_path, "wb") as val_file, open(train_path, "wb") as train_file:
        current, budget = val_file, args.val_tokens
        writing_val = True
        for i in range(0, len(docs), args.batch):
            for enc in tok.encode_batch(docs[i : i + args.batch]):
                ids = np.array(enc.ids + [doc_sep], dtype=np.uint16)
                current.write(ids.tobytes())
                total += len(ids)
                budget -= len(ids)
                if writing_val and budget <= 0:
                    current = train_file
                    writing_val = False

    print(f"tokens    : {total:,}  (val prefix: {args.val_tokens:,})")
    print(f"wrote     : {val_path}  {train_path}")


if __name__ == "__main__":
    main()
