# Run — stage 00 corpus, concrete examples and a length distribution

**Date:** 2026-07-30
**Hardware:** macOS, Apple Silicon (arm64). CPU-only; no GPU involved.
**Cost:** \$0 (local lane, one WARC download over the public internet).

## Purpose

The 2026-07-26 run recorded funnel counts and percentages but no actual
document text and no distribution over the kept set. This run exists to
answer "what does a document dropped/kept by each stage actually look like,"
grounding the README's new "What a document actually looks like at each gate"
section in real output instead of paraphrase.

## Input

One fresh WARC file from the same crawl as the 2026-07-26 run:

```
crawl-data/CC-MAIN-2026-25/segments/.../warc/CC-MAIN-...-00000.warc.gz  (~940MB gzipped)
```

## Command

```bash
curl -s https://data.commoncrawl.org/crawl-data/CC-MAIN-2026-25/warc.paths.gz \
  | gunzip | head -1 \
  | xargs -I{} curl -o sample.warc.gz https://data.commoncrawl.org/{}

uv run --with warcio python3 core/pipeline.py sample.warc.gz --limit 3000 --out clean.jsonl.gz
```

`uv run --with warcio` installs `warcio` into an ephemeral environment for the
run rather than adding it to the repo's `pyproject.toml` — this stage already
documents `warcio` as its one third-party dependency, and it is not meant to
be a permanent project dependency of the whole curriculum.

## Funnel, 3,000-document sample

```
stage                             docs  % of raw     kept
---------------------------------------------------------
1. html responses                3,000    100.0%        —
2. text extracted                2,699     90.0%    90.0%
3. english                         947     31.6%    35.1%
4. gopher quality                  755     25.2%    79.7%
5. c4 line filter                  569     19.0%    75.4%
6. minhash dedup                   550     18.3%    96.7%

drop reason                       docs
--------------------------------------
not_english                      1,752
extraction_empty                   301
empty_after_c4                     186
low_alpha_words                     97
too_short                           46
mean_word_length                    33
near_duplicate                      19
hash_symbol_ratio                   11
truncated_lines                      4
ellipsis_ratio                       1
```

This funnel shape (31.6% English survival, 96.7% dedup survival) is broadly
consistent with the 2026-07-26 20,000-document run (36.7%, 94.6%) at a smaller
sample size — the small differences are sampling variance, not a
contradiction.

## Example documents, by outcome

Extracted with a small standalone probe script (not committed — it imports
`iter_warc`, `extract_text`, `english_score`, `gopher_quality`, and
`c4_line_filter` directly from `core/pipeline.py` and inspects intermediate
values `pipeline.py`'s own `main()` does not expose):

- **`not_english`** — `06072005.eu/nowatorskie-metody-nauczania`, a Polish
  cooking blog, `english_score = 0.065` against a `0.12` threshold. Selected
  over other `not_english` candidates specifically because it is ASCII-legible
  prose in a non-English language (most raw `not_english` hits in this sample
  were mojibake from charset-detection failures upstream of this stage, which
  is a real and separate finding worth naming but not a clean teaching
  example).
- **`extraction_empty`** — `070404.com/video/170434785.html`, an empty
  `<title>` and a mostly-JavaScript page; under 200 characters of text survive
  extraction.
- **`empty_after_c4`** — `bftu.org.bw`, a homepage whose lines are mostly
  navigation and calls to action; what remains after the C4 line filter is
  under 50 words.
- **Survivor, substantive** — `abirdslifeinontario.blogspot.com/2015/10/day-tripper.html`,
  842 words of continuous first-person travel prose.
- **Survivor, boilerplate** — `137hnluxury.com/cgi-sys/defaultwebpage.cgi`, a
  148-word hosting-provider default error page. Grammatical, English, above
  every length floor, and not meaningfully different in kind from what
  datatrove's extra filters (`GopherRepetitionFilter`,
  `FineWebQualityFilter`) exist to catch, per the README's existing
  core-vs-datatrove comparison.

## Word-count distribution over the 569 kept documents

```
   <200 words: 196  (34.4%)
 200-500 words: 167  (29.3%)
500-1000 words: 110  (19.3%)
  1000-2000 words: 58  (10.2%)
     2000+ words: 38  ( 6.7%)
median: 322 words   mean: 705.2 words
```

## Verdict

The funnel counts from 2026-07-26 were real but silent about what a document
actually contains. This run makes that concrete: a third of the surviving
documents are near-floor length, two structurally identical "survivors" can be
a real essay or an error page, and the not_english bucket catches both
genuinely non-English prose and charset-decoding failures the funnel cannot
tell apart from each other.
