# Run — stage 00 corpus, core pipeline vs datatrove

**Date:** 2026-07-26
**Hardware:** AMD/Intel x86_64, 16 cores, 15GB RAM, WSL2 Ubuntu (kernel
6.6.87.2-microsoft-standard-WSL2). CPU-only; the GPU is idle for this stage.
**Cost:** $0 (local lane).

## Input

Two WARC files from the Common Crawl June 2026 dump, 940MB and 452MB gzipped:

```
crawl-data/CC-MAIN-2026-25/segments/1780687572080.85/warc/CC-MAIN-20260605214811-20260606004811-00000.warc.gz
crawl-data/CC-MAIN-2026-25/segments/1780687572080.85/warc/CC-MAIN-20260605214811-20260606004811-00001.warc.gz
```

Both pipelines were capped at 20,000 HTML responses per file (40,000 total) so
the funnels are directly comparable.

## Command — core

```bash
for f in data/warc/*.warc.gz; do
  python core/pipeline.py "$f" --out "clean-$(basename "$f" .warc.gz).jsonl.gz"
done
```

Funnel, file `...-00000`:

```
stage                             docs  % of raw     kept
---------------------------------------------------------
1. html responses               20,000    100.0%        —
2. text extracted               18,210     91.0%    91.0%
3. english                       7,348     36.7%    40.4%
4. gopher quality                6,349     31.7%    86.4%
5. c4 line filter                4,856     24.3%    76.5%
6. minhash dedup                 4,592     23.0%    94.6%

drop reason                       docs
--------------------------------------
not_english                     10,862
extraction_empty                 1,790
empty_after_c4                   1,493
low_alpha_words                    504
too_short                          302
near_duplicate                     264
mean_word_length                   126
hash_symbol_ratio                   58
truncated_lines                      7
ellipsis_ratio                       2
```

File `...-00001` produced the same surviving-document count (4,592) from a
different funnel (4,876 into dedup, 284 near-duplicates removed). The
coincidence is genuine, not a bug: the two files' stage counts differ
everywhere upstream and their kept word counts differ (2,971,307 vs 2,843,634).

**Totals:** 40,000 → 9,184 documents (23.0%), 36,445,527 characters,
5,814,941 words, ~7.6M estimated BPE tokens. Roughly 40 seconds per 20,000
documents, single core.

## Command — prod

```bash
python prod/fineweb_recipe.py data/warc dt_out --limit 20000 --workers 8
```

Stage yields as reported by datatrove:

| Stage | In | Out | Dropped |
|---|---|---|---|
| WarcReader | — | 40,000 | — |
| URLFilter | 40,000 | 39,741 | 259 |
| Trafilatura | 39,741 | 38,328 | 1,413 |
| LanguageFilter (en, 0.65) | 38,328 | 13,467 | 24,861 |
| GopherRepetitionFilter | 13,467 | 10,664 | 2,803 |
| GopherQualityFilter | 10,664 | 7,129 | 3,535 |
| C4QualityFilter | 7,129 | 6,445 | 684 |
| FineWebQualityFilter | 6,445 | 5,513 | 932 |

**Totals:** 40,000 → 5,513 documents (13.8%), 21,131,620 characters. Total
runtime 2 minutes 27 seconds across 8 workers, of which **85% was Trafilatura**
(25.14 ms/doc). Only ranks 0 and 1 did work — datatrove shards by input file, so
6 of 8 tasks found no files and exited immediately.

## Environment note

Getting datatrove's published recipe to run took five rounds of missing
optional dependencies, each surfacing one stage deeper into the pipeline:

1. `WarcReader` → `faust-cchardet`, `python-magic`
2. `JsonlWriter` → `orjson`
3. `URLFilter` (fetches its blocklist over HTTP) → `requests`, `aiohttp`
4. `GopherRepetitionFilter` (word tokenizer) → `spacy`
5. plus `trafilatura`, `nltk`, `tldextract`, `fasttext-numpy2`, `pyarrow`

`pip install datatrove[processing]` does not cover these. Budget time for it.

## Pretraining corpus acquired

Separately, four shards of FineWeb-Edu `sample/10BT` were downloaded for stage
02:

```
data/fineweb-edu/sample/10BT/{000,001,002,003}_00000.parquet
```

**2,916,000 documents, 3.01B tokens, 8.1GB.** Above the ~2.4B tokens that
Chinchilla-optimal training of a 120M model requires.

## Verdict

Both pipelines ran clean. The core pipeline is faster and 40% too permissive;
the production recipe is slower, stricter, and extracts better text. Neither
number is the deliverable — the comparison is.
