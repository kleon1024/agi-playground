"""From-scratch web-corpus pipeline: WARC in, clean deduplicated text out.

Every filter here is implemented directly rather than imported, because the
point of this lesson is that "cleaning web data" is not one magic step — it is
a funnel of cheap heuristics, each of which throws away a specific kind of
garbage, and each of which you can reason about and tune.

The only third-party dependency is `warcio`, for parsing the WARC container
format. Container parsing is plumbing, not pedagogy; everything downstream of
`iter_warc` is ours.

Run:  python pipeline.py <file.warc.gz> [--limit N]
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import statistics
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from warcio.archiveiterator import ArchiveIterator

# --------------------------------------------------------------------------
# Funnel bookkeeping
# --------------------------------------------------------------------------


@dataclass
class Funnel:
    """Counts documents surviving each stage, plus why they died."""

    stages: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    reasons: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def seen(self, stage: str) -> None:
        if stage not in self.stages:
            self.stages.append(stage)
        self.counts[stage] += 1

    def killed(self, reason: str) -> None:
        self.reasons[reason] += 1

    def report(self) -> str:
        first = self.counts[self.stages[0]] if self.stages else 0
        out = [f"{'stage':<28}{'docs':>10}{'% of raw':>10}{'kept':>9}"]
        out.append("-" * 57)
        prev = None
        for s in self.stages:
            n = self.counts[s]
            pct = 100 * n / first if first else 0
            kept = f"{100 * n / prev:.1f}%" if prev else "—"
            out.append(f"{s:<28}{n:>10,}{pct:>9.1f}%{kept:>9}")
            prev = n
        out.append("")
        out.append(f"{'drop reason':<28}{'docs':>10}")
        out.append("-" * 38)
        for r, n in sorted(self.reasons.items(), key=lambda kv: -kv[1]):
            out.append(f"{r:<28}{n:>10,}")
        return "\n".join(out)


# --------------------------------------------------------------------------
# 1. WARC reading
# --------------------------------------------------------------------------


def iter_warc(path: Path, limit: int | None = None, funnel: Funnel | None = None):
    """Yield (url, html) for successful HTML responses in a WARC file.

    Records that fail to decode are counted, not silently skipped. Data
    pipelines that swallow errors quietly are how corpora end up with holes
    nobody can explain three stages later — if 2% of a crawl fails to parse,
    that should appear in the funnel, not in nothing.
    """
    n = 0
    with open(path, "rb") as fh:
        for record in ArchiveIterator(fh):
            if record.rec_type != "response":
                continue
            ctype = record.http_headers.get_header("Content-Type") or ""
            if "html" not in ctype.lower():
                continue
            try:
                raw = record.content_stream().read()
                html = raw.decode("utf-8", errors="ignore")
            except (OSError, ValueError, UnicodeDecodeError):
                # Truncated payloads, bad chunked encoding, corrupt gzip members
                # — all routine in a web crawl of this size.
                if funnel:
                    funnel.killed("warc_record_unreadable")
                continue
            yield record.rec_headers.get_header("WARC-Target-URI"), html
            n += 1
            if limit and n >= limit:
                return


# --------------------------------------------------------------------------
# 2. Text extraction
# --------------------------------------------------------------------------

_DROP_TAGS = re.compile(
    r"<(script|style|nav|header|footer|aside|form|noscript)[^>]*>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)
_BLOCK_END = re.compile(r"</(p|div|h[1-6]|li|tr|br|section|article)>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\x0b\f]+")
_NL = re.compile(r"\n{3,}")

_ENTITIES = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
    "&#39;": "'", "&apos;": "'", "&nbsp;": " ", "&mdash;": "—", "&ndash;": "–",
}


def extract_text(html: str) -> str:
    """Strip HTML to plain text.

    This is deliberately naive — regex over HTML, no DOM, no boilerplate
    detection. Compare its output against trafilatura (used in the `prod/`
    pipeline) to see what a real extractor buys you: it drops navigation,
    cookie banners, and comment sections that survive here and quietly poison
    a corpus with repeated template text.
    """
    html = _DROP_TAGS.sub(" ", html)
    html = _BLOCK_END.sub("\n", html)
    text = _TAG.sub(" ", html)
    for ent, ch in _ENTITIES.items():
        text = text.replace(ent, ch)
    text = unicodedata.normalize("NFKC", text)
    text = _WS.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _NL.sub("\n\n", text).strip()


# --------------------------------------------------------------------------
# 3. Language identification
# --------------------------------------------------------------------------

# Production pipelines use a fastText classifier. A stop-word ratio is a
# surprisingly strong proxy for English and needs no model file — but it does
# fail on lists, code, and very short documents, which is exactly why the real
# pipeline uses a trained classifier.
_EN_STOPWORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for",
    "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his",
    "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my",
    "one", "all", "would", "there", "their", "what", "so", "up", "out", "if",
    "about", "who", "get", "which", "go", "me", "when", "make", "can", "like",
    "no", "just", "him", "know", "take", "into", "your", "some", "them", "see",
    "other", "than", "then", "now", "look", "only", "come", "its", "over",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well",
    "way", "even", "new", "want", "because", "any", "these", "us", "is", "are",
    "was", "were", "has", "had", "been", "more", "most", "such", "may",
}

_WORD = re.compile(r"[a-z']+")


def english_score(text: str) -> float:
    words = _WORD.findall(text.lower())
    if len(words) < 20:
        return 0.0
    hits = sum(1 for w in words if w in _EN_STOPWORDS)
    return hits / len(words)


# --------------------------------------------------------------------------
# 4. Quality filters (Gopher- and C4-style)
# --------------------------------------------------------------------------

_BULLETS = ("•", "-", "*", "‣", "·", "–")
_BAD_PHRASES = ("lorem ipsum", "javascript is disabled", "enable javascript",
                "your browser does not support", "terms of service", "cookie policy")
_END_PUNCT = (".", "!", "?", '"', "'", "”", "’", ":")


def gopher_quality(text: str) -> str | None:
    """Return a rejection reason, or None if the document passes.

    These thresholds come from the Gopher paper (Rae et al. 2021) and are the
    backbone of every open web-cleaning recipe since. Each one targets a real
    failure mode: keyword-stuffed SEO pages, navigation dumps, link farms,
    truncated listings.
    """
    words = text.split()
    n = len(words)
    if n < 50:
        return "too_short"
    if n > 100_000:
        return "too_long"

    mean_len = statistics.fmean(len(w) for w in words)
    if not 3 <= mean_len <= 10:
        # Very short mean word length means tokenised junk or menus; very long
        # means base64 blobs, URLs, or agglutinated text.
        return "mean_word_length"

    alpha = sum(1 for w in words if any(c.isalpha() for c in w))
    if alpha / n < 0.8:
        return "low_alpha_words"

    if text.count("#") / max(n, 1) > 0.1:
        return "hash_symbol_ratio"
    if text.count("...") / max(n, 1) > 0.1:
        return "ellipsis_ratio"

    lines = [ln for ln in text.split("\n") if ln.strip()]
    if not lines:
        return "no_lines"
    bullets = sum(1 for ln in lines if ln.lstrip().startswith(_BULLETS))
    if bullets / len(lines) > 0.9:
        return "mostly_bullets"
    ellipsis_end = sum(1 for ln in lines if ln.rstrip().endswith("..."))
    if ellipsis_end / len(lines) > 0.3:
        return "truncated_lines"

    # A document with almost no stop words is usually a keyword list, not prose.
    if english_score(text) < 0.08:
        return "no_stopwords"
    return None


def c4_line_filter(text: str) -> str:
    """C4-style line-level cleaning: drop boilerplate lines, keep prose.

    Applied after document-level filters because it changes the text — a
    document can pass Gopher and still be 40% cookie-banner lines.
    """
    keep = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        low = s.lower()
        if any(p in low for p in _BAD_PHRASES):
            continue
        if "{" in s or "}" in s:  # stray JS/CSS the extractor missed
            continue
        if len(s.split()) < 3:  # menu items, single words
            continue
        if not s.endswith(_END_PUNCT):  # not a real sentence
            continue
        keep.append(s)
    return "\n".join(keep)


# --------------------------------------------------------------------------
# 5. MinHash near-duplicate detection
# --------------------------------------------------------------------------

_MERSENNE = (1 << 61) - 1  # prime modulus for the hash family


class MinHashDeduper:
    """Near-duplicate detection via MinHash + LSH banding.

    The idea in three steps:

    1. Represent each document as a set of overlapping word n-grams
       ("shingles"). Two documents that share most shingles are near-copies.
    2. Estimate that overlap cheaply. Comparing full shingle sets pairwise is
       O(n^2); instead, hash the set `num_perm` times and keep only the minimum
       hash from each permutation. The probability that two documents share a
       given minimum equals their Jaccard similarity — so a short signature
       vector approximates the similarity of huge sets.
    3. Avoid comparing all pairs at all. Split the signature into `bands` chunks
       and index each chunk. Documents colliding in ANY band become candidates.
       Tuning bands vs rows sets the similarity threshold: more bands catches
       more pairs (higher recall, more false positives).

    Production systems (datatrove, NeMo Curator) implement exactly this, but
    sharded across machines so the index never has to fit in one process.
    """

    def __init__(self, num_perm: int = 64, bands: int = 16, ngram: int = 5, seed: int = 0):
        assert num_perm % bands == 0, "num_perm must divide evenly into bands"
        self.num_perm, self.bands, self.ngram = num_perm, bands, ngram
        self.rows = num_perm // bands
        rng = __import__("random").Random(seed)
        # A universal hash family: h_i(x) = (a_i * x + b_i) mod p
        self.a = [rng.randrange(1, _MERSENNE) for _ in range(num_perm)]
        self.b = [rng.randrange(0, _MERSENNE) for _ in range(num_perm)]
        self.buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
        self.parent: dict[int, int] = {}

    # --- union-find, to group transitively-similar documents into clusters ---
    def _find(self, x: int) -> int:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def _union(self, x: int, y: int) -> None:
        rx, ry = self._find(x), self._find(y)
        if rx != ry:
            self.parent[min(rx, ry)] = self.parent[max(rx, ry)] = min(rx, ry)

    def shingles(self, text: str) -> set[int]:
        words = text.split()
        if len(words) < self.ngram:
            return {hash(text)}
        return {
            hash(" ".join(words[i : i + self.ngram]))
            for i in range(len(words) - self.ngram + 1)
        }

    def signature(self, text: str) -> list[int]:
        sh = self.shingles(text)
        sig = []
        for a, b in zip(self.a, self.b):
            sig.append(min(((a * (h & _MERSENNE) + b) % _MERSENNE) for h in sh))
        return sig

    def add(self, doc_id: int, text: str) -> None:
        sig = self.signature(text)
        self._find(doc_id)
        for band in range(self.bands):
            key = (band, hash(tuple(sig[band * self.rows : (band + 1) * self.rows])))
            for other in self.buckets[key]:
                self._union(doc_id, other)
            self.buckets[key].append(doc_id)

    def survivors(self) -> set[int]:
        """One representative per cluster — the lowest id."""
        return {self._find(d) for d in self.parent}


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("warc", type=Path)
    ap.add_argument("--limit", type=int, default=20000)
    ap.add_argument("--out", type=Path, default=Path("clean.jsonl.gz"))
    ap.add_argument("--min-english", type=float, default=0.12)
    args = ap.parse_args()

    funnel = Funnel()
    deduper = MinHashDeduper()
    kept: list[tuple[str, str]] = []

    for url, html in iter_warc(args.warc, args.limit, funnel):
        funnel.seen("1. html responses")

        text = extract_text(html)
        if len(text) < 200:
            funnel.killed("extraction_empty")
            continue
        funnel.seen("2. text extracted")

        if english_score(text) < args.min_english:
            funnel.killed("not_english")
            continue
        funnel.seen("3. english")

        reason = gopher_quality(text)
        if reason:
            funnel.killed(reason)
            continue
        funnel.seen("4. gopher quality")

        text = c4_line_filter(text)
        if len(text.split()) < 50:
            funnel.killed("empty_after_c4")
            continue
        funnel.seen("5. c4 line filter")

        deduper.add(len(kept), text)
        kept.append((url, text))

    survivors = deduper.survivors()
    for _ in survivors:
        funnel.seen("6. minhash dedup")
    funnel.reasons["near_duplicate"] = len(kept) - len(survivors)

    with gzip.open(args.out, "wt", encoding="utf-8") as fh:
        total_words = 0
        for i, (url, text) in enumerate(kept):
            if i in survivors:
                fh.write(json.dumps({"url": url, "text": text}) + "\n")
                total_words += len(text.split())

    print(funnel.report())
    print()
    print(f"output          : {args.out} ({args.out.stat().st_size / 1e6:.1f} MB gz)")
    print(f"documents kept  : {len(survivors):,}")
    print(f"words kept      : {total_words:,}")
    print(f"est. BPE tokens : {total_words * 1.3 / 1e6:.1f}M  (~1.3 tokens/word)")


if __name__ == "__main__":
    sys.exit(main())
