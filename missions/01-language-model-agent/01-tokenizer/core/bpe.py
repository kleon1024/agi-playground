"""Byte-level BPE tokenizer, trained from scratch.

Why byte-level: if the vocabulary is built over raw UTF-8 bytes, every possible
string is representable and there is no `<UNK>` token, ever. A Chinese
character, an emoji, or a corrupted byte all decompose into byte tokens the
model has seen. This is why GPT-2 onward all use byte-level BPE.

The training algorithm is three lines of English:

1. Split text into words with a regex, and represent each word as a sequence of
   byte tokens.
2. Count every adjacent pair of tokens across the corpus; merge the most
   frequent pair into a single new token.
3. Repeat until the vocabulary reaches the target size.

The one non-obvious engineering trick is that we never iterate over the corpus
itself after the first pass. We collapse it into a dictionary of unique words
and their counts, then merge over that. A corpus of 10^9 words typically has
only ~10^6 unique ones, so this is a thousandfold saving and is what makes
pure-Python training feasible at all.

Run:  python bpe.py train <corpus.jsonl.gz|.parquet> --vocab-size 16384
      python bpe.py test  <tokenizer.json> --text "hello world"
"""

from __future__ import annotations

import argparse
import gzip
import heapq
import json
import re
import time
from collections import Counter, defaultdict
from itertools import pairwise
from pathlib import Path

# GPT-4's pre-tokenization pattern. Pre-tokenization decides what BPE is never
# allowed to merge across: this pattern keeps merges from spanning a word
# boundary or gluing digits into long numerals (note `\p{N}{1,3}` capping number
# runs at 3 digits), both of which measurably hurt arithmetic and rare-word
# behaviour downstream.
SPLIT_PATTERN = (
    r"'(?i:[sdmt]|ll|ve|re)|[^\r\n\w]?+\w+|\d{1,3}| ?[^\s\w]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+"
)
_SPLIT_RE = re.compile(SPLIT_PATTERN)


def word_counts(texts, max_docs: int | None = None) -> Counter[bytes]:
    """Collapse a corpus into {word_bytes: frequency}."""
    counts: Counter[bytes] = Counter()
    for i, text in enumerate(texts):
        if max_docs and i >= max_docs:
            break
        for piece in _SPLIT_RE.findall(text):
            counts[piece.encode("utf-8")] += 1
    return counts


def _apply_merge(ids: list[int], pair: tuple[int, int], new_id: int) -> list[int]:
    """Replace every occurrence of `pair` in `ids` with `new_id`."""
    if len(ids) < 2:
        return ids
    out, i = [], 0
    while i < len(ids):
        if i < len(ids) - 1 and (ids[i], ids[i + 1]) == pair:
            out.append(new_id)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


def train_bpe_indexed(
    counts: Counter[bytes],
    vocab_size: int,
    verbose: bool = True,
    checkpoint: Path | None = None,
    checkpoint_every: int = 500,
):
    """The same algorithm, with an index. This is the one you should use.

    `train_bpe` below recounts every pair in every word on every merge, which is
    O(vocab_size x corpus) and is why a 16k vocabulary takes hours. But a merge
    changes only the words that actually contain the merged pair — typically a
    tiny fraction of the corpus. So:

    * keep a running count of every pair, and
    * keep an index from each pair to the set of words containing it.

    Then a merge touches only the indexed words: subtract their old pair
    contributions, apply the merge, add the new ones back. The cost per merge
    drops from "the whole corpus" to "the words that changed".

    Selecting the most frequent pair uses a lazy heap: pushing on every count
    change would be expensive, so stale entries are left in place and discarded
    when popped if they disagree with the authoritative count. This is the same
    trick production priority queues use to avoid decrease-key.
    """
    assert vocab_size >= 256, "vocabulary must at least cover the 256 byte values"

    words: list[list[int]] = []
    freqs: list[int] = []
    for word, freq in counts.items():
        words.append(list(word))
        freqs.append(freq)

    vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
    merges: dict[tuple[int, int], int] = {}
    start_id = 256

    if checkpoint and checkpoint.exists():
        saved = json.loads(checkpoint.read_text())
        for a, b, i in saved["merges"]:
            merges[(a, b)] = i
            vocab[i] = vocab[a] + vocab[b]
        start_id = 256 + len(merges)
        for (a, b), new_id in sorted(merges.items(), key=lambda kv: kv[1]):
            words = [_apply_merge(w, (a, b), new_id) for w in words]
        if verbose:
            print(f"resumed from {checkpoint}: {len(merges):,} merges", flush=True)

    pair_counts: Counter[tuple[int, int]] = Counter()
    pair_words: dict[tuple[int, int], set[int]] = defaultdict(set)

    def index_word(i: int, sign: int) -> None:
        """Add (sign=+1) or remove (sign=-1) word i's pair contributions."""
        w, f = words[i], freqs[i]
        for pair in pairwise(w):
            pair_counts[pair] += sign * f
            if sign > 0:
                pair_words[pair].add(i)

    for i in range(len(words)):
        index_word(i, +1)

    heap = [(-c, p) for p, c in pair_counts.items() if c > 0]
    heapq.heapify(heap)

    for new_id in range(start_id, vocab_size):
        # Pop until the heap's top agrees with the authoritative count.
        best = None
        while heap:
            neg, pair = heapq.heappop(heap)
            if pair_counts.get(pair, 0) == -neg and -neg >= 2:
                best = pair
                break
        if best is None:
            if verbose:
                print(f"corpus exhausted at vocab size {new_id}", flush=True)
            break

        best_count = pair_counts[best]
        affected = [i for i in pair_words[best] if _has_pair(words[i], best)]

        touched: set[tuple[int, int]] = set()
        for i in affected:
            for pair in pairwise(words[i]):
                touched.add(pair)
            index_word(i, -1)
            words[i] = _apply_merge(words[i], best, new_id)
            index_word(i, +1)
            for pair in pairwise(words[i]):
                touched.add(pair)

        del pair_counts[best]
        pair_words.pop(best, None)
        for pair in touched:
            c = pair_counts.get(pair, 0)
            if c > 0:
                heapq.heappush(heap, (-c, pair))

        merges[best] = new_id
        vocab[new_id] = vocab[best[0]] + vocab[best[1]]

        if checkpoint and (new_id - 255) % checkpoint_every == 0:
            checkpoint.write_text(
                json.dumps({"merges": [[a, b, i] for (a, b), i in merges.items()]})
            )

        if verbose and (new_id % 1000 == 0 or new_id < 260):
            shown = vocab[new_id].decode("utf-8", errors="replace")
            print(
                f"  merge {new_id:>6}  {best[0]:>6},{best[1]:>6} -> {shown!r}  "
                f"(x{best_count:,})",
                flush=True,
            )

    return merges, vocab


def _has_pair(ids: list[int], pair: tuple[int, int]) -> bool:
    return any(p == pair for p in pairwise(ids))


def train_bpe(
    counts: Counter[bytes],
    vocab_size: int,
    verbose: bool = True,
    checkpoint: Path | None = None,
    checkpoint_every: int = 500,
):
    """Learn merges until the vocabulary reaches `vocab_size`.

    Returns (merges, vocab) where merges maps (a, b) -> new_id in learned order
    and vocab maps id -> bytes.

    Pass `checkpoint` to make the run resumable. This is not premature caution:
    training a 16k vocabulary in pure Python takes hours, and anything that
    interrupts it — a laptop sleeping, an SSH session dropping, a machine
    leaving the network — otherwise costs the entire run. Checkpointing turns a
    two-hour loss into a two-minute one, and the merge list is small enough that
    saving it is free relative to the cost of not having it.
    """
    assert vocab_size >= 256, "vocabulary must at least cover the 256 byte values"

    # Each unique word becomes a list of token ids; ids 0..255 are raw bytes.
    words: list[tuple[list[int], int]] = [
        (list(word), freq) for word, freq in counts.items()
    ]
    vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
    merges: dict[tuple[int, int], int] = {}
    start_id = 256

    if checkpoint and checkpoint.exists():
        saved = json.loads(checkpoint.read_text())
        for a, b, i in saved["merges"]:
            merges[(a, b)] = i
            vocab[i] = vocab[a] + vocab[b]
        start_id = 256 + len(merges)
        # Replay the learned merges onto the word state so training resumes
        # from exactly where it stopped.
        for (a, b), new_id in sorted(merges.items(), key=lambda kv: kv[1]):
            words = [(_apply_merge(ids, (a, b), new_id), freq) for ids, freq in words]
        if verbose:
            print(f"resumed from {checkpoint}: {len(merges):,} merges", flush=True)

    for new_id in range(start_id, vocab_size):
        # Count adjacent pairs, weighted by how often the word occurs.
        pairs: Counter[tuple[int, int]] = Counter()
        for ids, freq in words:
            for pair in pairwise(ids):
                pairs[pair] += freq
        if not pairs:
            if verbose:
                print(f"corpus exhausted at vocab size {new_id}")
            break

        # Break ties by pair ordering, not by insertion order, so the result
        # is deterministic and comparable against train_bpe_indexed.
        best = min(pairs.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        best_count = pairs[best]
        if best_count < 2:  # nothing left worth merging
            break

        # Apply the merge everywhere it appears.
        words = [(_apply_merge(ids, best, new_id), freq) for ids, freq in words]

        merges[best] = new_id
        vocab[new_id] = vocab[best[0]] + vocab[best[1]]

        if checkpoint and (new_id - 255) % checkpoint_every == 0:
            checkpoint.write_text(
                json.dumps({"merges": [[a, b, i] for (a, b), i in merges.items()]})
            )

        if verbose and (new_id % 1000 == 0 or new_id < 260):
            token = vocab[new_id]
            shown = token.decode("utf-8", errors="replace")
            # flush=True matters more than it looks: BPE training is a long
            # job, and Python block-buffers stdout when it is redirected to a
            # file. Without this, a two-hour run writes nothing to its log
            # until it finishes, and you cannot tell progress from a hang.
            print(
                f"  merge {new_id:>6}  {best[0]:>6},{best[1]:>6} -> {shown!r}  (×{best_count:,})",
                flush=True,
            )

    return merges, vocab


class Tokenizer:
    def __init__(self, merges: dict[tuple[int, int], int], vocab: dict[int, bytes]):
        self.merges, self.vocab = merges, vocab

    # -- encoding -----------------------------------------------------------
    def _encode_word(self, piece: bytes) -> list[int]:
        ids = list(piece)
        while len(ids) >= 2:
            # Apply the *earliest-learned* applicable merge. Merge order is the
            # tokenizer's contract: applying them out of order produces a
            # different segmentation than training implied.
            pair = min(
                (p for p in pairwise(ids) if p in self.merges),
                key=lambda p: self.merges[p],
                default=None,
            )
            if pair is None:
                break
            new_id, out, i = self.merges[pair], [], 0
            while i < len(ids):
                if i < len(ids) - 1 and (ids[i], ids[i + 1]) == pair:
                    out.append(new_id)
                    i += 2
                else:
                    out.append(ids[i])
                    i += 1
            ids = out
        return ids

    def encode(self, text: str) -> list[int]:
        out: list[int] = []
        for piece in _SPLIT_RE.findall(text):
            out.extend(self._encode_word(piece.encode("utf-8")))
        return out

    def decode(self, ids: list[int]) -> str:
        return b"".join(self.vocab[i] for i in ids).decode("utf-8", errors="replace")

    # -- persistence --------------------------------------------------------
    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "pattern": SPLIT_PATTERN,
                    "merges": [[a, b, i] for (a, b), i in self.merges.items()],
                    "vocab_size": len(self.vocab),
                }
            )
        )

    @classmethod
    def load(cls, path: Path) -> Tokenizer:
        blob = json.loads(path.read_text())
        merges = {(a, b): i for a, b, i in blob["merges"]}
        vocab = {i: bytes([i]) for i in range(256)}
        for (a, b), i in sorted(merges.items(), key=lambda kv: kv[1]):
            vocab[i] = vocab[a] + vocab[b]
        return cls(merges, vocab)


# --------------------------------------------------------------------------
# Corpus readers
# --------------------------------------------------------------------------


def read_texts(path: Path, limit: int | None):
    if path.suffix == ".parquet" or path.is_dir():
        import pyarrow.parquet as pq

        files = sorted(path.glob("*.parquet")) if path.is_dir() else [path]
        seen = 0
        for f in files:
            pf = pq.ParquetFile(f)
            for batch in pf.iter_batches(batch_size=2000, columns=["text"]):
                for t in batch.column(0).to_pylist():
                    yield t
                    seen += 1
                    if limit and seen >= limit:
                        return
    else:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                if limit and i >= limit:
                    return
                yield json.loads(line)["text"]


# --------------------------------------------------------------------------


def cmd_train(args) -> None:
    t0 = time.time()
    print(f"reading up to {args.docs:,} documents from {args.corpus} ...", flush=True)
    counts = word_counts(read_texts(args.corpus, args.docs))
    total_words = sum(counts.values())
    print(
        f"  {total_words:,} words, {len(counts):,} unique "
        f"({total_words / max(len(counts), 1):.0f}x collapse)  [{time.time() - t0:.1f}s]",
        flush=True,
    )

    print(f"training BPE to vocab_size={args.vocab_size} ...", flush=True)
    trainer = train_bpe if args.naive else train_bpe_indexed
    merges, vocab = trainer(counts, args.vocab_size, checkpoint=args.checkpoint)
    tok = Tokenizer(merges, vocab)
    tok.save(args.out)
    print(f"saved {args.out}  [{time.time() - t0:.1f}s total]")

    # Compression is the number that matters: fewer tokens per character means
    # more text fits in the same context window and the same compute budget.
    sample = "".join(list(read_texts(args.corpus, 200)))[:200_000]
    ids = tok.encode(sample)
    print()
    print(f"{'chars':<22}{len(sample):>12,}")
    print(f"{'tokens':<22}{len(ids):>12,}")
    print(f"{'chars/token':<22}{len(sample) / len(ids):>12.3f}")
    print(f"{'bytes/token':<22}{len(sample.encode()) / len(ids):>12.3f}")
    assert tok.decode(ids) == sample, "round-trip failed"
    print("round-trip: ok")


def cmd_test(args) -> None:
    tok = Tokenizer.load(args.tokenizer)
    ids = tok.encode(args.text)
    print(f"text   : {args.text!r}")
    print(f"ids    : {ids}")
    print(f"pieces : {[tok.vocab[i].decode('utf-8', errors='replace') for i in ids]}")
    print(f"decoded: {tok.decode(ids)!r}")
    assert tok.decode(ids) == args.text, "round-trip failed"


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    tr = sub.add_parser("train")
    tr.add_argument("corpus", type=Path)
    tr.add_argument("--vocab-size", type=int, default=16384)
    tr.add_argument("--docs", type=int, default=50_000)
    tr.add_argument("--out", type=Path, default=Path("tokenizer.json"))
    tr.add_argument(
        "--naive",
        action="store_true",
        help="use the unindexed reference implementation (much slower)",
    )
    tr.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="save merges periodically here and resume from it if present",
    )
    tr.set_defaults(func=cmd_train)

    te = sub.add_parser("test")
    te.add_argument("tokenizer", type=Path)
    te.add_argument("--text", default="Hello world! 你好，世界。 1234567")
    te.set_defaults(func=cmd_test)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
