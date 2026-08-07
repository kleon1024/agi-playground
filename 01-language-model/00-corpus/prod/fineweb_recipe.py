"""The same job as `core/pipeline.py`, built from datatrove's FineWeb recipe.

Run this against the same WARC file the core pipeline used and compare the two
funnels. The differences are the lesson:

* **Trafilatura vs. our regex stripper.** A real extractor understands document
  structure and drops navigation, cookie banners, and comment threads. Our
  version keeps them, which quietly fills a corpus with repeated template text.
* **fastText vs. our stop-word ratio.** A trained classifier handles short
  documents, lists, and code — cases where a stop-word ratio guesses badly and
  throws away good English.
* **URLFilter.** A blocklist of domains that no heuristic would catch from text
  alone (adult, spam, and link-farm hosts).
* **GopherRepetitionFilter.** Catches documents that repeat their own lines and
  paragraphs — a failure mode our core pipeline does not test for at all.

Every component here is the same code that produced the public FineWeb dataset,
which is why the stage yields are directly comparable to HuggingFace's
published numbers rather than a reimplementation that merely resembles them.

Run:  python fineweb_recipe.py <warc-dir> <out-dir> [--limit N]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from datatrove.executor import LocalPipelineExecutor
from datatrove.pipeline.extractors import Trafilatura
from datatrove.pipeline.filters import (
    C4QualityFilter,
    FineWebQualityFilter,
    GopherQualityFilter,
    GopherRepetitionFilter,
    LanguageFilter,
    URLFilter,
)
from datatrove.pipeline.readers import WarcReader
from datatrove.pipeline.writers.jsonl import JsonlWriter


def build(warc_dir: Path, out_dir: Path, limit: int, workers: int) -> LocalPipelineExecutor:
    return LocalPipelineExecutor(
        pipeline=[
            WarcReader(str(warc_dir), glob_pattern="*.warc.gz", limit=limit),
            # Domain blocklist — cheapest filter, so it runs before extraction.
            URLFilter(),
            # HTML → text with structure awareness and boilerplate removal.
            Trafilatura(favour_precision=True, timeout=30),
            # fastText language ID. 0.65 is FineWeb's published threshold.
            LanguageFilter(languages=["en"], language_threshold=0.65),
            # Documents that repeat their own lines/paragraphs.
            GopherRepetitionFilter(),
            # Length, word-length, symbol-ratio, stop-word heuristics.
            GopherQualityFilter(),
            # Line-level boilerplate removal (the C4 recipe).
            C4QualityFilter(filter_no_terminal_punct=False),
            # FineWeb's own additions on top of Gopher + C4.
            FineWebQualityFilter(),
            JsonlWriter(str(out_dir)),
        ],
        # Each WARC file is an independent task, so this scales linearly with
        # cores. Production runs swap LocalPipelineExecutor for a Slurm
        # executor and the arithmetic is otherwise identical.
        tasks=workers,
        workers=workers,
        logging_dir=str(out_dir / "logs"),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("warc_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--limit", type=int, default=-1, help="docs per task; -1 = all")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    executor = build(args.warc_dir, args.out_dir, args.limit, args.workers)
    print(executor.run())


if __name__ == "__main__":
    main()
