---
status: draft
---

# 02 — Data

## Scope

Data as a first-class subject, not an assumed-clean input. This track covers
building a pipeline from raw crawl text to a trained-on shard: acquisition,
cleaning and quality filtering, deduplication at scale, human annotation, and
synthetic data generation. This is the white-space topic the research
identified — every other from-scratch curriculum (nanochat, Raschka,
microgpt) starts from an already-clean corpus; here you build the corpus.

## Prerequisites

None required to start. `01-foundations` is not a hard dependency for the
pipeline lessons (dedup/filtering/annotation don't need autograd or attention),
but later synthetic-data lessons that use a model in the loop assume a
checkpoint from `03-pretraining` or an off-the-shelf API model.

## Planned lessons

1. `01-corpus-acquisition` — pulling raw shards from Common Crawl/FineWeb-style
   sources.
2. `02-cleaning-and-quality-filtering` — heuristic and model-based filters,
   the FineWeb-style filtering stages.
3. `03-dedup-at-scale` — exact and fuzzy (MinHash/LSH) deduplication, why it
   matters at corpus scale.
4. `04-annotation-with-argilla` — human-in-the-loop labeling workflows and
   preference-data collection.
5. `05-synthetic-data-with-distilabel` — model-generated data, filtering
   generated data for quality, and RLVR rubric design.
6. `06-data-qa-and-versioning` — dataset QA checks and versioning discipline
   for reproducible corpora.

## Speedrun note

`01-corpus-acquisition` and `02-cleaning-and-quality-filtering` are the seed
lessons for speedrun stage `00-corpus` (a cleaned English shard via
datatrove, with published dedup and quality-filter stats).
