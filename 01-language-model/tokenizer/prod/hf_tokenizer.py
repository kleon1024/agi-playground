"""The production lane for stage 01, in two parts.

**Part 1 — the same algorithm, in Rust.** Train a `tokenizers` BPE on the same
corpus and vocabulary size as `core/bpe.py`, and compare wall-clock and
compression. Same algorithm, same data; the only difference is the
implementation language and an incremental pair-count index instead of our
recount-everything loop.

**Part 2 — keep our vocabulary, borrow their speed.** Our trainer is slow but
correct, and its merge list *is* the tokenizer. So we export our learned merges
into the `tokenizers` format and let the Rust encoder apply them. The
vocabulary stays the one our code learned; only encoding gets accelerated. The
script then asserts that both encoders produce identical ids, because an
exported tokenizer that silently disagrees with the one you trained is a
corpus-corrupting bug that will not surface until your model is mid-training.

Run:  python hf_tokenizer.py compare <corpus-dir> --vocab-size 16384 --docs 10000
      python hf_tokenizer.py export  <ours.json> <out.json> --corpus <corpus-dir>
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# The from-scratch trainer lives one directory over. Importing it rather than
# duplicating it is the point: this script must export exactly the merges that
# implementation learned.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

import bpe as core  # our from-scratch implementation
from tokenizers import Regex, Tokenizer, decoders, models, pre_tokenizers, trainers


# The byte <-> unicode trick GPT-2 introduced and every byte-level BPE since
# reuses: map all 256 byte values to printable unicode code points, so the
# vocabulary can be stored as text without control characters or invalid UTF-8.
def bytes_to_unicode() -> dict[int, str]:
    bs = (
        list(range(ord("!"), ord("~") + 1))
        + list(range(ord("¡"), ord("¬") + 1))
        + list(range(ord("®"), ord("ÿ") + 1))
    )
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return {b: chr(c) for b, c in zip(bs, cs)}


BYTE_ENCODER = bytes_to_unicode()


def encode_bytes(token: bytes) -> str:
    return "".join(BYTE_ENCODER[b] for b in token)


def build_shell() -> Tokenizer:
    """A tokenizers.Tokenizer configured to match core/bpe.py's segmentation."""
    tok = Tokenizer(models.BPE())
    # Split on our pattern first, then byte-encode each piece — the same two
    # steps, in the same order, as core/bpe.py's `_SPLIT_RE` + `.encode()`.
    tok.pre_tokenizer = pre_tokenizers.Sequence(
        [
            pre_tokenizers.Split(Regex(core.SPLIT_PATTERN), behavior="isolated"),
            pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False),
        ]
    )
    tok.decoder = decoders.ByteLevel()
    return tok


# --------------------------------------------------------------------------


def cmd_compare(args) -> None:
    texts = list(core.read_texts(args.corpus, args.docs))
    print(f"corpus: {len(texts):,} documents")

    tok = build_shell()
    trainer = trainers.BpeTrainer(
        vocab_size=args.vocab_size,
        special_tokens=[],
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        show_progress=False,
    )
    t0 = time.time()
    tok.train_from_iterator(texts, trainer=trainer)
    rust_seconds = time.time() - t0

    sample = "".join(texts[:200])[:200_000]
    ids = tok.encode(sample).ids
    print()
    print(f"{'implementation':<20}{'train time':>14}{'chars/token':>14}")
    print("-" * 48)
    print(f"{'tokenizers (Rust)':<20}{rust_seconds:>13.1f}s{len(sample) / len(ids):>14.3f}")
    print()
    print("Run core/bpe.py on the same inputs and compare. The compression")
    print("numbers should land within a few percent — same algorithm — while")
    print("the wall-clock gap is one to two orders of magnitude.")

    tok.save(str(args.out))
    print(f"saved {args.out}")


def cmd_export(args) -> None:
    ours = core.Tokenizer.load(args.ours)
    print(f"loaded our tokenizer: {len(ours.vocab):,} tokens, {len(ours.merges):,} merges")

    # vocab: token string -> id, in id order
    vocab = {encode_bytes(ours.vocab[i]): i for i in sorted(ours.vocab)}
    # merges: the pair of *pieces*, in the order we learned them
    merges = [
        (encode_bytes(ours.vocab[a]), encode_bytes(ours.vocab[b]))
        for (a, b), _ in sorted(ours.merges.items(), key=lambda kv: kv[1])
    ]

    tok = build_shell()
    tok.model = models.BPE(vocab=vocab, merges=merges, fuse_unk=False)
    tok.save(str(args.out))
    print(f"exported -> {args.out}")

    # ---- the part that matters: prove the two encoders agree ----
    texts = list(core.read_texts(args.corpus, args.verify_docs))
    fast = Tokenizer.from_file(str(args.out))
    mismatches = 0
    total_tokens = 0
    t_ours = t_fast = 0.0
    for text in texts:
        chunk = text[:5000]
        t0 = time.time()
        a = ours.encode(chunk)
        t_ours += time.time() - t0
        t0 = time.time()
        b = fast.encode(chunk).ids
        t_fast += time.time() - t0
        total_tokens += len(a)
        if a != b:
            mismatches += 1
            if mismatches == 1:
                for j, (x, y) in enumerate(zip(a, b)):
                    if x != y:
                        print(f"  first divergence at token {j}: ours={x} fast={y}")
                        print(f"  context: {chunk[max(0, j - 40):j + 40]!r}")
                        break

    print()
    print(f"{'documents verified':<24}{len(texts):>12,}")
    print(f"{'tokens compared':<24}{total_tokens:>12,}")
    print(f"{'mismatched documents':<24}{mismatches:>12,}")
    print(f"{'ours (pure Python)':<24}{t_ours:>11.2f}s")
    print(f"{'tokenizers (Rust)':<24}{t_fast:>11.2f}s")
    if t_fast > 0:
        print(f"{'speedup':<24}{t_ours / t_fast:>11.1f}x")
    if mismatches:
        raise SystemExit("EXPORT IS NOT FAITHFUL — do not tokenize a corpus with this.")
    print("\nexport verified: identical ids on every document.")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compare")
    c.add_argument("corpus", type=Path)
    c.add_argument("--vocab-size", type=int, default=16384)
    c.add_argument("--docs", type=int, default=10000)
    c.add_argument("--out", type=Path, default=Path("hf_tokenizer.json"))
    c.set_defaults(func=cmd_compare)

    e = sub.add_parser("export")
    e.add_argument("ours", type=Path)
    e.add_argument("out", type=Path)
    e.add_argument("--corpus", type=Path, required=True)
    e.add_argument("--verify-docs", type=int, default=300)
    e.set_defaults(func=cmd_export)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
