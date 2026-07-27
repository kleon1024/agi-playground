---
status: draft
---

# 02 — Data

## Why this track exists

Every from-scratch LLM tutorial you can find — nanochat, Sebastian Raschka's
books, microgpt — starts from a corpus that's already clean: Tiny Shakespeare,
WikiText, a pre-filtered slice of something bigger. That choice quietly skips
the step that determines whether the resulting model is any good. The
research pass behind this repo (`research/synthesis.md`) checked this across
four independent surveys and found the same gap every time: nobody treats
data acquisition, filtering, deduplication, and annotation as a taught
subject with the same rigor as attention or optimizers. It's treated as
somebody else's problem, solved upstream, before the tutorial begins.

This track is the fix. You build the corpus instead of downloading it,
and you build the label instead of trusting one. Concretely: web-scale
curation and the funnel model of cleaning, deduplication theory (not just
"run MinHash," but why MinHash/LSH work and what the band/row tradeoff
costs you), quality filtering (heuristics vs. trained classifiers), data
mixtures and curriculum design, human annotation workflows, synthetic data
generation, preference-data collection for post-training, RLVR rubric
design, and the QA/versioning/contamination discipline that keeps a corpus
honest over time.

## What you build

Two direct ties to the speedrun, one indirect:

- **Speedrun stage [00 — corpus](../../missions/01-language-model-agent/00-corpus/)** is this
  track's flagship, and it's already built — read it before anything else
  here. It's a from-scratch WARC-to-clean-shard pipeline (~330 lines: WARC
  reading, text extraction, language ID, Gopher quality rules, C4 line
  filtering, MinHash dedup) run side-by-side against the published
  `datatrove` FineWeb recipe on identical input. The measured funnel: our
  pipeline kept 9,184 of 40,000 documents (23.0%); datatrove kept 5,513
  (13.8%) on the same input — see
  [`runs/2026-07-26-core-vs-datatrove.md`](../../missions/01-language-model-agent/00-corpus/runs/2026-07-26-core-vs-datatrove.md).
  Lessons `01-corpus-acquisition` and `02-cleaning-and-quality-filtering`
  below are that stage's seed lessons.
- **Speedrun stage [03 — sft](../../missions/01-language-model-agent/03-sft/)** consumes this
  track's later lessons: the chat-template dataset and loss-masking setup
  need instruction data built or curated with the same QA discipline taught
  in `06-data-qa-and-versioning`, and any preference pairs feeding stage 04's
  RL come from `04-annotation-with-argilla` / `05-synthetic-data-with-distilabel`.
- Everything past stage 00 in this track (annotation, preference data, RLVR
  rubrics, data mixtures) is deepened at milestone **M3**, per the roadmap
  in the top-level README — stage 00 ships first because the speedrun needs
  it immediately; the rest of the track fills in around it.

## The conceptual spine

### 1. The funnel model of cleaning

Cleaning a crawl is not one filter, it's a funnel, and the shape of that
funnel is the actual lesson. Stage 00's measured run is the reference case:
language ID removed more documents (10,862 of 40,000) than every quality
heuristic combined — "cleaning web data" is numerically mostly "choosing a
language." No single Gopher rule (length, mean word length, symbol ratios)
removes much on its own; they're jointly decisive. And the datatrove
comparison is the point that heuristics alone plateau: `GopherRepetitionFilter`
and `FineWebQualityFilter` — two filter families the from-scratch pipeline
never implements — account for datatrove's entire stricter-by-40% gap.
Repetition detection is a distinct failure mode from length/symbol
heuristics, and it's exactly the kind of thing that teaches a model to loop.

Change the three retention gates below before moving on. The goal is not to
maximize the final count; it is to see why every gate needs a separate quality
audit rather than one aggregate “documents kept” metric.

<!-- interactive: DataCurationFunnel -->

### 2. Deduplication theory: why MinHash/LSH, and the band/row tradeoff

Exact dedup (hash the document, drop collisions) catches copies; it misses
the far larger population of *near*-duplicates — the same article synced
across ten mirrors with a byline changed. MinHash approximates Jaccard
similarity between two documents' n-gram sets cheaply: hash each n-gram with
many independent hash functions, keep the minimum per function, and the
fraction of matching minimums across two documents' signatures is an
unbiased estimator of their Jaccard similarity. That turns an O(n²) exact
set-intersection problem into a signature comparison.

LSH (locality-sensitive hashing) makes that comparison scale: split each
document's MinHash signature into `b` bands of `r` hashes each. Two
documents become *candidate* duplicates if any single band matches exactly
across both — so instead of comparing every pair of documents, you only
compare pairs that collide in at least one band bucket. The tradeoff is
explicit and derivable: the probability that two documents with true
Jaccard similarity `s` are flagged as candidates is `1 - (1 - s^r)^b`, and
the threshold where that curve is steepest is approximately `(1/b)^(1/r)`.
More bands (fixed total hashes) means smaller `r` per band, which raises
recall (catches weaker near-duplicates) at the cost of more false-positive
candidate pairs to verify. Stage 00's `MinHashDeduper` (64 permutations, 16
bands) is a concrete instance of this tradeoff — its exercises ask you to
move the band count and watch the near-duplicate count and the implied
threshold both move.

The honest caveat, also from the stage 00 run: deduplicating 20,000
documents against each other found few near-duplicates (5% of the pre-dedup
set). That's not evidence dedup barely matters — it's an artifact of the
comparison window. Web repetition lives *between* crawl shards, not mostly
within a single small one, which is exactly why production dedup (datatrove,
NeMo Curator) runs as a distributed multi-stage job over the full corpus
rather than a single-pass filter.

### 3. Quality filtering: heuristics vs. classifiers

Gopher-style rules (length bounds, alpha ratio, mean word length, bullet/
ellipsis ratios) are cheap, auditable, and individually weak — you saw this
in stage 00's funnel. The FineWeb-Edu approach (Penedo et al., 2024)
replaces "did this document pass ten hand-written rules" with "does a small
trained classifier think this document has high educational value": sample
documents, have an LLM judge educational value on a 0–5 scale, train a
lightweight classifier (originally BERT-scale) to predict that judgment,
then score the full corpus and threshold. The published result — FineWeb-Edu
(~9% of FineWeb's tokens) outperforming full FineWeb on downstream
benchmarks — is the strongest evidence in this space that a *smaller,
better* corpus beats a larger unfiltered one, and it's the reason this
track's classifier-based lesson exists. Language-ID heuristics and trained
classifiers agree in aggregate more than you'd expect (stage 00's stop-word
heuristic and a fastText classifier land within three points of each other)
but disagree on *which* documents — short text, code, and lists are where
the disagreement concentrates, which is why a heuristic is fine to *teach*
with and wrong to *ship*.

### 4. Data mixtures and curriculum

Not all tokens are equal, and the mixture of sources — web, code, books,
academic text, math, dialogue — measurably changes what a model is good at.
Code data is the standard example of a mixture decision with outsized
effect: it doesn't just teach code, it improves general reasoning benchmarks,
which is why LLaMA 3 raised its code share well above what "we need a coding
model" alone would justify. Fixed mixture ratios are a starting point, not
an answer — DoReMi (Xie et al., 2023) trains a small proxy model to learn
mixture weights automatically, tracking each domain's "excess loss" (how
much worse the proxy does on that domain versus a reference model trained
on a uniform mixture) and upweighting domains where excess loss is high.
Reported gains over hand-tuned mixtures are consistently positive but
modest (low single-digit points on downstream averages) — worth knowing
because it sets expectations: mixture search is a real lever, not a magic one.

Curriculum learning and data annealing are the temporal version of the same
idea: switching to a higher-quality data mixture in the final ~5–15% of
training, with the learning rate already decaying, is a documented and
reproducible technique (Llama 2/3 report annealing gains in the low single
digits on benchmark averages). Strict easy-to-hard sample ordering across
an entire pretraining run is a much shakier claim — several ablations find
random shuffling competitive once the dataset is large enough, so this
track treats "annealing at the end" as the validated technique and
"difficulty-ordered curricula throughout" as an open question worth an
exercise, not a recipe worth following blindly.

### 5. Annotation workflows and preference-data collection

Human annotation for preference data (the `(prompt, chosen, rejected)`
pairs DPO-family methods train on) is a pipeline in its own right: collect
prompts stratified by task type and difficulty, generate K candidate
responses at varied temperature, get ≥2 annotators to rank or pairwise-
compare them, and measure Inter-Annotator Agreement (Cohen's κ) to catch a
bad annotation guide before it poisons the dataset — κ above 0.6 is usable,
below 0.4 means the rubric needs rework, and RLHF preference labeling
typically lands around κ ≈ 0.7–0.8 for clear-cut comparisons and
κ ≈ 0.4–0.6 for subtle ones. Argilla (human review UI, Hub-integrated) and
distilabel (LLM-as-annotator pipelines: self-instruct, UltraFeedback-style
generation, DPO pair synthesis) are the tools this track teaches directly —
this is one of the few places in the curriculum where "toy" and
"production" collapse into the same tool, because reimplementing an
annotation UI from scratch teaches far less than using the real one at
small scale (see `LANDSCAPE.md`).

LLM-as-judge annotation is cheaper by roughly two orders of magnitude than
human labeling (\$0.01–\$0.05/pair via API vs. \$0.50–\$2/pair for crowdworkers)
but carries known, well-characterized biases: position bias (favoring
whichever response appears first — mitigated by scoring both orderings and
discarding disagreements), length/verbosity bias (favoring longer or more
list-formatted answers regardless of quality), and self-enhancement bias
(a judge favoring outputs from its own model family). Multi-judge voting
(3–5 independent judges, majority or weighted vote) is the standard
mitigation when a single judge's biases can't be fully prompted away.

### 6. RLVR rubric design

Verifiable-reward RL (RLVR) replaces a learned reward model with a rule:
does the final answer match, does the code pass its tests, does the output
satisfy a checkable format. That sounds like it removes data engineering
from the loop — it doesn't; it relocates it. Designing the rubric *is* the
data-engineering problem now: what counts as a match (exact string vs.
normalized numeric answer vs. semantic equivalence), how partial credit is
scored, what to do about a policy that games the rubric's letter while
violating its spirit (reward hacking), and how tasks are selected so the
verifier is actually reliable at scale. A sloppy rubric is exactly as
damaging as a sloppy preference-annotation guide — it just fails silently,
because there's no human in the loop to notice the drift.

### 7. Data QA, versioning, and contamination

A corpus that isn't versioned isn't reproducible, and a corpus that isn't
checked against your eval sets isn't trustworthy. QA here means: schema and
encoding checks, distributional monitoring (token length, language mix,
duplicate rate over time) so a pipeline regression is caught before a
training run burns compute on it, and — critically — decontamination:
n-gram overlap checks between your training corpus and every benchmark
you'll report a number against. This is the same discipline `07-evals`
covers from the benchmark side; here it's the training-data side of the
same problem, and the two must be checked together or neither claim means
anything.

### Beyond text: multimodal data, briefly

This repo doesn't currently carry a dedicated vision-language track, but
the same theory generalizes directly, and it's worth knowing the shape of
that generalization even without a full lesson: image-text pair filtering
uses CLIP-score thresholding (cosine similarity between CLIP image and text
embeddings) in place of a text quality classifier — LAION-derived pipelines
commonly threshold around 0.28, which keeps roughly 30–40% of raw pairs —
and image deduplication uses perceptual hashing (pHash/dHash: downsample,
transform, threshold) or CLIP-embedding nearest-neighbor search in place of
MinHash. DataComp's published filtering ablations (Gadre et al., 2023) are
the multimodal analog of the FineWeb quality-filtering story: filtering
LAION down to ~25% by pairing CLIP-score with image- and text-quality
filters more than 10x'd downstream ImageNet zero-shot accuracy versus no
filtering at all. If this repo grows a VLM track later, this is where its
data lesson would begin.

## Planned lessons

1. `01-corpus-acquisition` — pulling raw shards from Common Crawl/FineWeb-style
   sources; WARC format, HTML extraction. Seeds speedrun stage 00.
2. `02-cleaning-and-quality-filtering` — Gopher/C4-style heuristic filters,
   and the classifier-based alternative (FineWeb-Edu methodology). Seeds
   speedrun stage 00.
3. `03-dedup-at-scale` — exact hashing, MinHash + LSH (banding, the
   `(1/b)^(1/r)` threshold derivation), suffix-array substring dedup, and
   why small-scale dedup measurements understate full-corpus dedup.
4. `04-data-mixtures-and-curriculum` — mixture design, DoReMi-style
   automatic mixture weighting, data annealing, and the evidence for and
   against strict difficulty-ordered curricula.
5. `05-annotation-with-argilla` — human-in-the-loop labeling, annotation
   guide design, Inter-Annotator Agreement, preference-pair collection
   (pairwise/ranking/pointwise formats and their tradeoffs).
6. `06-synthetic-data-with-distilabel` — LLM-as-annotator pipelines,
   LLM-as-judge bias mitigation, rejection sampling for preference pairs,
   and RLVR rubric design.
7. `07-data-qa-and-versioning` — dataset QA checks, distributional
   monitoring, versioning discipline, and contamination/decontamination
   against eval sets.

## Common misconceptions

- **"More data is always better."** Repeated data has sharply diminishing
  value (Hernandez et al., 2022, find seeing a sample 4 times is worth
  roughly 3x a fresh sample; well beyond that the model starts overfitting
  to the repeats), and FineWeb-Edu's ~9%-of-tokens subset outperforming the
  full corpus is direct evidence that a smaller, better-filtered corpus can
  beat a larger unfiltered one.
- **"Heuristic filters are basically as good as classifiers."** They agree
  in aggregate more often than you'd expect, but disagree systematically on
  short text, code, and lists — and heuristics are structurally blind to
  whole failure classes (repetition) that a purpose-built filter catches.
  Stage 00's measured 40% permissiveness gap versus datatrove is the
  concrete evidence, not a hypothetical.
- **"Small-scale dedup numbers predict full-corpus dedup rates."** Stage
  00's near-duplicate rate (5%) was measured by comparing 20,000 documents
  against each other; cross-shard repetition — which is most of what
  production dedup removes — is invisible at that scale. Underestimating
  dedup by comparing too small a corpus is the standard reason distributed
  multi-stage dedup jobs exist at all.
- **"LLM-as-judge is a neutral, objective proxy for human preference."**
  It carries reproducible, well-documented biases (position, length,
  self-enhancement) that require explicit countermeasures — swapped-order
  scoring, length control, multi-judge voting — not just a well-worded prompt.
- **"RLVR removes the data-engineering problem."** It moves it into rubric
  design. A reward function a policy can game silently is exactly as
  damaging as a low-agreement annotation guide, and it fails without the
  visibility a human annotator would have flagged.

## Prerequisites

None required to start. `01-foundations` is not a hard dependency for the
pipeline lessons (dedup/filtering/annotation don't need autograd or
attention), but the synthetic-data and RLVR-rubric lessons that use a model
in the loop assume a checkpoint from `03-pretraining` or an off-the-shelf
API model.

## Key papers

- Penedo et al., *"The FineWeb Datasets"* (2024) — the classifier-based
  quality-filtering recipe this track teaches from; FineWeb-Edu's smaller,
  higher-quality subset beating the full corpus is the central data point
  for "quality over quantity."
- Xie et al., *"DoReMi: Optimizing Data Mixtures via Small Proxy Models"*
  (2023) — automatic mixture-weight learning; the reference for treating
  data mixture as an optimization problem instead of a hand-tuned constant.
- Hernandez et al., *"Scaling Data-Constrained Language Models"* (2022) —
  quantifies the diminishing (and eventually negative) value of repeated
  training data.
- Gadre et al., *"DataComp: In Search of the Next Generation of Multimodal
  Datasets"* (2023) — the multimodal analog of the FineWeb story; published
  ablations isolating exactly which filters buy which downstream accuracy.
- Rafailov et al., *"Direct Preference Optimization"* (2023) — defines the
  `(prompt, chosen, rejected)` format this track's annotation and synthetic-
  data lessons produce data for.
- Lambert et al., *"Tulu 3"* report (2024) — a fully documented SFT → DPO →
  RLVR recipe, including preference-data construction and verifiable-reward
  task design, worth reading end-to-end alongside this track.

## Next

Read [speedrun stage 00 — corpus](../../missions/01-language-model-agent/00-corpus/) first if you
haven't — it's this track's working flagship, not a placeholder.
