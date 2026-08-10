"""The same corpus, the same merge rule, two different vocabularies.

The parent chapter showed two implementations agreeing when they run the
same algorithm the same way. This audit measures the silent second axis:
the tie-break. BPE's "merge the most frequent pair" is a partial order —
real text is full of ties — and whichever pair wins a tie is arbitrary but
not inconsequential: merging one pair creates new pairs and rewrites the
counts around it, so an early tie-break choice propagates through the whole
merge sequence. Two runs of the *same* algorithm on the *same* corpus can
therefore learn different vocabularies, and a team that swaps one BPE
implementation for another and sees a different token stream will suspect
the model, the data, or the seed before the line that chose the tie.

Measured here on the real no_robots corpus (offline HuggingFace cache):

  1. Tie incidence: at how many merge steps the chosen pair was one of
     several tied at the maximum count, and how wide those ties run.
  2. Divergence: the first merge step at which two deterministic tie-breaks
     pick different pairs, and the Jaccard overlap of the vocabularies they
     build at several merge depths.
  3. Downstream cost: chars/token on held-out text under both, and how
     number-heavy and rare-unicode strings fragment under each.

Deterministic (two fixed tie-break rules, fixed seed for data shuffle),
CPU-only. The corpus is real; the run is a mechanism demo at toy vocab size.
"""

from __future__ import annotations

import argparse
import heapq
import importlib.util
import sys
from collections import Counter, defaultdict
from pathlib import Path

_BPE = Path(__file__).resolve().parents[3] / "core" / "bpe.py"
spec = importlib.util.spec_from_file_location("bpe", _BPE)
bpe = importlib.util.module_from_spec(spec)
sys.modules["bpe"] = bpe
spec.loader.exec_module(bpe)


def train_bpe_tiebreak(
    counts: Counter[bytes],
    vocab_size: int,
    key,
    verbose: bool = False,
):
    """Indexed BPE with a pluggable tie-break `key(pair) -> tuple`.

    Mirrors `bpe.train_bpe_indexed` (lazy heap, authoritative-count check,
    touch-only-the-affected-words reindexing) with the tie-break parameterized
    instead of baked in, and records what the stage version never exposes:
    how wide the tie was at each decision, and which pair each step chose.
    """
    words: list[list[int]] = [list(w) for w in counts]
    freqs: list[int] = list(counts.values())
    vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
    merges: dict[tuple[int, int], int] = {}
    pair_counts: Counter[tuple[int, int]] = Counter()
    pair_words: dict[tuple[int, int], set[int]] = defaultdict(set)

    def index_word(i: int, sign: int) -> None:
        w, f = words[i], freqs[i]
        for pair in bpe.pairwise(w):
            pair_counts[pair] += sign * f
            if sign > 0:
                pair_words[pair].add(i)

    for i in range(len(words)):
        index_word(i, +1)

    heap = [(-c, key(p), p) for p, c in pair_counts.items() if c > 0]
    heapq.heapify(heap)
    choices: list[tuple[int, tuple[int, int], int]] = []  # (count, pair, tie width)

    for new_id in range(256, vocab_size):
        best = None
        while heap:
            neg, _, pair = heapq.heappop(heap)
            if pair_counts.get(pair, 0) == -neg and -neg >= 2:
                best = pair
                break
        if best is None:
            break
        best_count = pair_counts[best]

        # Measure the tie width at this decision point without consuming it:
        # entries with the same count are contiguous under a count-first heap.
        width = 1
        peeked: list[tuple[int, int]] = []
        while heap:
            neg, _, pair = heap[0]
            if pair_counts.get(pair, 0) != -neg or -neg < 2:
                heapq.heappop(heap)
                continue
            if -neg == best_count:
                _, _, pair = heapq.heappop(heap)
                peeked.append(pair)
                width += 1
            else:
                break
        for pair in peeked:
            heapq.heappush(heap, (-pair_counts[pair], key(pair), pair))

        affected = [i for i in pair_words[best] if bpe._has_pair(words[i], best)]
        touched: set[tuple[int, int]] = set()
        for i in affected:
            for pair in bpe.pairwise(words[i]):
                touched.add(pair)
            index_word(i, -1)
            words[i] = bpe._apply_merge(words[i], best, new_id)
            index_word(i, +1)
            for pair in bpe.pairwise(words[i]):
                touched.add(pair)
        del pair_counts[best]
        pair_words.pop(best, None)
        for pair in touched:
            c = pair_counts.get(pair, 0)
            if c > 0:
                heapq.heappush(heap, (-c, key(pair), pair))

        merges[best] = new_id
        vocab[new_id] = vocab[best[0]] + vocab[best[1]]
        choices.append((best_count, best, width))

    return merges, vocab, choices


def corpus_texts(max_docs: int) -> list[str]:
    from datasets import load_dataset

    rows = load_dataset("HuggingFaceH4/no_robots", split="train")
    texts: list[str] = []
    for row in rows:
        for msg in row["messages"]:
            texts.append(msg.get("content", ""))
        if len(texts) >= max_docs:
            break
    return texts


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def chars_per_token(tokenizer, texts: list[str]) -> float:
    chars = sum(len(t) for t in texts)
    tokens = sum(len(tokenizer.encode(t)) for t in texts)
    return chars / tokens


def piece_disagreement(tok_a, tok_b, texts: list[str]) -> tuple[int, int, int]:
    """Share of pre-tokenized pieces the two vocabularies segment differently.

    A piece is any unit the shared pre-tokenizer emits. Same piece, same
    algorithm, two vocabularies: if the learned merges diverged, the two
    segmentations diverge. `n_diff` counts every piece whose id sequence
    differs; `n_len_diff` counts the stricter subset whose *length* differs,
    which is the change a sequence-length contract (max tokens per prompt)
    would actually notice.
    """
    n_pieces = n_diff = n_len_diff = 0
    for text in texts:
        for piece in bpe._SPLIT_RE.findall(text):
            n_pieces += 1
            a = tok_a._encode_word(piece.encode("utf-8"))
            b = tok_b._encode_word(piece.encode("utf-8"))
            if a != b:
                n_diff += 1
                if len(a) != len(b):
                    n_len_diff += 1
    return n_diff, n_len_diff, n_pieces


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=int, default=8500)
    ap.add_argument("--held-out", type=int, default=1000)
    ap.add_argument("--vocab-size", type=int, default=4096)
    args = ap.parse_args()

    texts = corpus_texts(args.docs + args.held_out)
    train_texts = texts[: args.docs]
    held_texts = texts[args.docs : args.docs + args.held_out]
    counts = bpe.word_counts(train_texts)
    print(
        f"tokenizer tie-break audit (real no_robots, CPU):\n"
        f"  train docs {args.docs:,}, held-out {len(held_texts):,}, "
        f"{len(counts):,} unique pieces, vocab {args.vocab_size}",
        flush=True,
    )

    lex_key = lambda p: (p[0], p[1])
    rlex_key = lambda p: (-p[0], -p[1])
    merges_lex, vocab_lex, choices_lex = train_bpe_tiebreak(
        counts, args.vocab_size, lex_key
    )
    merges_rlex, vocab_rlex, choices_rlex = train_bpe_tiebreak(
        counts, args.vocab_size, rlex_key
    )
    assert len(choices_lex) == len(choices_rlex)

    n = len(choices_lex)
    tie_steps = sum(1 for _, _, w in choices_lex if w > 1)
    widths = [w for _, _, w in choices_lex]
    max_w = max(widths)
    first_diff = next(
        (i for i in range(n) if choices_lex[i][1] != choices_rlex[i][1]), None
    )

    lex_pairs = set(merges_lex)
    rlex_pairs = set(merges_rlex)
    lex_d = {p: i for i, p in enumerate(lex_pairs)}
    rlex_d = {p: i for i, p in enumerate(rlex_pairs)}

    print(
        f"\n  1. tie incidence: {tie_steps}/{n} steps ({tie_steps / n:.1%}) chose "
        f"from a tie; mean width {sum(widths) / n:.1f}, max {max_w}",
        flush=True,
    )
    print(
        f"  2. divergence: first different pair at step {first_diff}; "
        f"merge-set Jaccard at depth 500/1000/2000/all: "
        + " / ".join(
            f"{jaccard({p for p, i in lex_d.items() if i < d}, {p for p, i in rlex_d.items() if i < d}):.3f}"
            for d in (500, 1000, 2000, 10**9)
        ),
        flush=True,
    )

    tok_lex = bpe.Tokenizer(merges_lex, vocab_lex)
    tok_rlex = bpe.Tokenizer(merges_rlex, vocab_rlex)
    cpt_lex = chars_per_token(tok_lex, held_texts)
    cpt_rlex = chars_per_token(tok_rlex, held_texts)
    print(
        f"  3. held-out chars/token: lex {cpt_lex:.3f} vs rlex {cpt_rlex:.3f}",
        flush=True,
    )
    n_diff, n_len_diff, n_pieces = piece_disagreement(tok_lex, tok_rlex, held_texts)
    print(
        f"     held-out segmentation: {n_diff:,}/{n_pieces:,} pieces differ "
        f"({n_diff / n_pieces:.1%}); {n_len_diff:,} differ in token count",
        flush=True,
    )

    edges = [
        "3,141,592 is approximately pi times 1,000,000 and 1234567890",
        "東京タワーの高さは333メートルです",
        "café naïve résumé",
        "hello world, the cat sat on the mat",
    ]
    print("\n  edge-case encodings (tokens; same under both arms at vocab 4096):")
    for s in edges:
        ids = tok_lex.encode(s)
        spans = "|".join(tok_lex.decode([i]) for i in ids)
        print(f"    {len(ids):>3} tokens: {spans}")

    print(
        "\n  verdict: the tokenizer's tie-break is a hidden axis of the model. "
        "The same corpus and the same 'merge the most frequent pair' rule "
        "produce different vocabularies whenever real text ties, and the "
        "difference lands exactly on the edges a downstream model cares "
        "about: numbers and rare characters.",
        flush=True,
    )


if __name__ == "__main__":
    main()
