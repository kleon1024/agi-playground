---
status: draft
base: none
---

# Stage 00 — Corpus

**Goal:** turn raw Common Crawl into clean, deduplicated English text, and
understand every filter that made it clean.

**Why this is stage 00 and not an appendix.** Every from-scratch LLM tutorial
starts by downloading a tidy dataset — Tiny Shakespeare, WikiText, an
already-filtered slice of something larger. That skips the part that actually
determines whether your model is any good. A model trained on raw Common Crawl
and the same model trained on filtered Common Crawl are not close, and the gap
is larger than most architecture changes you could make. Data is the
highest-leverage variable in the pipeline, and it is the one nearly every
curriculum treats as somebody else's problem.

So we start here, and we start by writing the filters ourselves.

## What you build

`core/pipeline.py` — a complete web-cleaning pipeline in ~330 lines with one
third-party dependency (`warcio`, for the container format):

| Stage | What it does | Why it exists |
|---|---|---|
| WARC reading | Pull HTML responses out of Common Crawl's archive format | The raw crawl is headers, redirects, and markup around the text you want |
| Text extraction | Strip tags, entities, scripts, navigation | HTML is mostly markup by volume |
| Language ID | Keep English via stop-word ratio | Common Crawl is majority non-English |
| Gopher quality | Length, mean word length, symbol ratios, bullet and ellipsis ratios, stop-word presence | Kills keyword stuffing, navigation dumps, link farms, truncated listings |
| C4 line filter | Drop boilerplate lines, keep sentences | A document can pass document-level checks and still be 40% cookie banner |
| MinHash dedup | Near-duplicate detection via LSH banding and union-find | The web is enormously repetitive, and duplicates drive memorization |

## What we measured

Two WARC files from `CC-MAIN-2026-25` (the June 2026 crawl), 20,000 HTML
responses each. One file's funnel:

```
stage                             docs  % of raw     kept
---------------------------------------------------------
1. html responses               20,000    100.0%        —
2. text extracted               18,210     91.0%    91.0%
3. english                       7,348     36.7%    40.4%
4. gopher quality                6,349     31.7%    86.4%
5. c4 line filter                4,856     24.3%    76.5%
6. minhash dedup                 4,592     23.0%    94.6%
```

Across both files: **40,000 documents in, 9,184 out (23%), ~7.6M tokens.**

Read the funnel, because it contradicts the usual intuition:

- **Language is the single biggest filter**, removing 10,862 documents — more
  than every quality heuristic combined. Numerically, "cleaning web data" is
  mostly "choosing a language."
- **Quality filters are individually small but jointly decisive.** No single
  Gopher rule removes much; together they take another third.
- **Dedup at this scale looks cheap (5%) and that is misleading.** We compared
  20,000 documents only against each other. Deduplicating a full crawl removes
  far more, because the repetition lives *between* shards rather than within
  them — which is precisely why production dedup is a distributed multi-stage
  job instead of one pipeline step.

## Reproducing

```bash
# fetch one WARC file (~940MB)
curl -s https://data.commoncrawl.org/crawl-data/CC-MAIN-2026-25/warc.paths.gz \
  | gunzip | head -1 \
  | xargs -I{} curl -O https://data.commoncrawl.org/{}

# run the from-scratch pipeline
python core/pipeline.py CC-MAIN-*.warc.gz --limit 20000 --out clean.jsonl.gz
```

Roughly 40 seconds per 20,000 documents on one core. The recorded run is in
[`runs/`](runs/).

## The production lane, on identical input

`prod/fineweb_recipe.py` runs the published FineWeb recipe from
[datatrove](https://github.com/huggingface/datatrove) over the same two WARC
files. Same input, same document count, different implementation:

| | ours (`core/`) | datatrove (`prod/`) |
|---|---|---|
| Documents in | 40,000 | 40,000 |
| Documents out | 9,184 (23.0%) | 5,513 (13.8%) |
| Characters out | 36.4M | 21.1M |
| Chars/document | 3,968 | 3,833 |
| Wall clock | ~80s, 1 core | 2m27s, 8 workers |
| Extraction cost | ~2 ms/doc (regex) | 25 ms/doc (trafilatura) |

Four things fall out of this comparison, and they are the point of the stage:

**1. We are 40% too permissive.** datatrove discards a third more documents than
we do. It is not being fussy — it runs two filter families we never wrote:
`GopherRepetitionFilter` (2,803 docs: pages that repeat their own lines and
n-grams) and `FineWebQualityFilter` (932 docs: character-duplication ratio, line
punctuation ratio, short-line ratio). Repetition is a failure mode our funnel is
structurally blind to, and repetitive documents are exactly the ones that teach
a model to loop.

**2. Both agree on language, from completely different mechanisms.** Our
stop-word ratio keeps 36.7% of raw documents; fastText at threshold 0.65 keeps
33.7%. A crude heuristic and a trained classifier land within three points of
each other on aggregate — which is why the heuristic is good enough to teach
with, and why you should still not ship it (they disagree on *which*
documents, particularly short ones, code, and lists).

**3. Extraction is where the money goes.** Trafilatura accounts for **85% of
datatrove's total runtime** at 25ms/doc — twelve times our regex stripper. It
buys structural awareness: navigation, cookie banners, and comment threads that
survive our extractor get removed. Our output has *more* characters per
document than datatrove's, and that is not a win; it is the boilerplate we
failed to strip.

**4. Fast and wrong is easy.** Our pipeline is genuinely faster in raw
throughput. That is what a naive implementation always looks like right up
until you read its output.

## The corpus we actually pretrain on

Here the lesson and the engineering diverge, and it is worth stating why rather
than hiding it.

Our pipeline yields about 3.9M tokens per 20,000 documents. Stage 02 trains a
120M-parameter model, which at Chinchilla-optimal ratios wants roughly 2.4B
tokens. Producing that ourselves would mean downloading and processing on the
order of **250GB of raw WARC** — many hours of network and CPU — to reproduce,
less well, a corpus that has already been published.

So we run the pipeline to understand it, and we download
[FineWeb-Edu](https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu) to
train on. Four shards of the `sample/10BT` subset give **3.01B tokens across
2.9M documents in 8.1GB** — produced by the same recipe our `prod/` script
runs, plus an educational-quality classifier that small models benefit from
disproportionately.

This is what a practitioner does, and pretending otherwise would be theatre.
What you should not do is skip the pipeline: if you have never watched 77% of a
crawl evaporate through filters you wrote, you do not really know what is in
your training data.

## Exercises

1. **Break the language filter.** Feed it a page of English source code, then a
   list of product names. Both are English; the stop-word ratio disagrees. This
   is why production uses a trained classifier.
2. **Tune the dedup threshold.** `MinHashDeduper` uses 64 permutations in 16
   bands. Change the band count and watch the near-duplicate count move — more
   bands means higher recall and more false positives. Derive the implied
   similarity threshold from `(1/b)^(1/r)`.
3. **Catalogue the boilerplate.** Log what the C4 line filter drops instead of
   discarding it. The result is a survey of the web's furniture.
4. **Find the extraction failures.** Rank surviving documents by the ratio of
   short navigation-like lines to prose. The worst offenders show exactly what
   `prod/`'s trafilatura buys you.

## Next

[Stage 01 — tokenizer](../01-tokenizer/): turn this text into the integers a
model can consume, with a byte-level BPE you train yourself.
