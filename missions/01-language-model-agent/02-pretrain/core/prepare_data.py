"""Tokenize the corpus once, into a flat binary file the training loop mmaps.

Pretraining reads the same tokens many times. Tokenizing on the fly would burn
CPU on every epoch and make the dataloader the bottleneck, so we tokenize once,
write a contiguous array of token ids to disk, and let the training loop take
random windows out of it with `numpy.memmap` — the OS page cache then keeps the
hot parts in RAM without us managing a buffer at all.

Two decisions in here are worth more than they look:

**uint16, not int32.** A vocabulary under 65,536 fits in two bytes per token.
That halves the file, halves the bytes read per step, and costs nothing. A 3B
token corpus is 6GB as uint16 and 12GB as int32 — on a machine where the page
cache is the difference between fast and slow, that is the whole game.

**A document separator token.** Documents are concatenated into one stream, so
without a boundary marker the model learns to predict the first sentence of an
unrelated web page from the last sentence of the previous one — teaching it that
topics change at random. One reserved token between documents fixes it.

Run:  python prepare_data.py <parquet-dir> <tokenizer.json> --out-dir data/tokens
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from tokenizers import Tokenizer

# The BPE vocabulary occupies ids 0..vocab_size-1. The separator is the next id
# up, so it can never collide with a learned merge.
DOC_SEP_OFFSET = 0


def iter_texts(parquet_dir: Path, limit_docs: int | None):
    seen = 0
    for f in sorted(parquet_dir.glob("*.parquet")):
        pf = pq.ParquetFile(f)
        for batch in pf.iter_batches(batch_size=1000, columns=["text"]):
            for text in batch.column(0).to_pylist():
                yield text
                seen += 1
                if limit_docs and seen >= limit_docs:
                    return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("parquet_dir", type=Path)
    ap.add_argument("tokenizer", type=Path, help="HF tokenizers JSON (see prod/hf_tokenizer.py export)")
    ap.add_argument("--out-dir", type=Path, default=Path("data/tokens"))
    ap.add_argument("--limit-docs", type=int, default=None)
    ap.add_argument("--val-tokens", type=int, default=5_000_000)
    ap.add_argument("--batch", type=int, default=1000)
    args = ap.parse_args()

    tok = Tokenizer.from_file(str(args.tokenizer))
    vocab_size = tok.get_vocab_size()
    doc_sep = vocab_size + DOC_SEP_OFFSET
    assert doc_sep < 65536, "uint16 storage requires vocab_size + 1 < 65536"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.out_dir / "train.bin"
    val_path = args.out_dir / "val.bin"

    print(f"tokenizer vocab : {vocab_size:,}")
    print(f"document sep id : {doc_sep:,}")
    print(f"writing to      : {args.out_dir}")

    t0 = time.time()
    total = 0
    docs = 0
    buffer: list[str] = []

    # Validation split is taken from the *front* of the stream and never
    # revisited, so no training window can straddle into it.
    with open(val_path, "wb") as val_file, open(train_path, "wb") as train_file:
        current, current_budget = val_file, args.val_tokens
        writing_val = True

        def flush(texts: list[str]) -> int:
            nonlocal current, current_budget, writing_val, total
            if not texts:
                return 0
            written = 0
            for enc in tok.encode_batch(texts):
                ids = np.array(enc.ids + [doc_sep], dtype=np.uint16)
                current.write(ids.tobytes())
                written += len(ids)
                current_budget -= len(ids)
                if writing_val and current_budget <= 0:
                    current = train_file
                    writing_val = False
            total += written
            return written

        for text in iter_texts(args.parquet_dir, args.limit_docs):
            buffer.append(text)
            docs += 1
            if len(buffer) >= args.batch:
                flush(buffer)
                buffer = []
                if docs % 50_000 == 0:
                    rate = total / (time.time() - t0)
                    print(
                        f"  {docs:>9,} docs  {total / 1e6:>8.1f}M tokens  "
                        f"{rate / 1e3:>7.1f}k tok/s",
                        flush=True,
                    )
        flush(buffer)

    elapsed = time.time() - t0
    train_tokens = train_path.stat().st_size // 2
    val_tokens = val_path.stat().st_size // 2
    print()
    print(f"{'documents':<20}{docs:>14,}")
    print(f"{'train tokens':<20}{train_tokens:>14,}  ({train_path.stat().st_size / 1e9:.2f} GB)")
    print(f"{'val tokens':<20}{val_tokens:>14,}")
    print(f"{'wall clock':<20}{elapsed:>13.1f}s")
    print(f"{'throughput':<20}{total / elapsed / 1e3:>13.1f}k tok/s")
    print()
    print(f"Set Config.vocab_size >= {doc_sep + 1:,} so the separator is in range.")


if __name__ == "__main__":
    main()
