---
status: draft
level: applied
label: Vision-language model
---

# Does the picture add anything a hosted API or a blind guess couldn't?

**Question:** you have a decoder trained on text. Someone asks it to look at a
picture and answer a question about it. Before you graft on a vision pathway
and call it a VLM, you need to know it actually sees — not that it has learned
to guess plausible answers from the question's wording, and not that a single
call to a hosted API would have done the same job for less.

**The artifact this mission follows** is one instance: an image, a short
question about it, and the answer the decoder produces. Everything below is
about what it takes to trust that answer came from the picture.

## Why this mission exists

[Mission 01](../01-language-model-agent/) built a decoder — RoPE, RMSNorm,
SwiGLU, a training loop, a serving engine, an agent loop — entirely around a
1-D sequence of discrete token ids. Reading
[`02-pretrain/core/model.py`](../01-language-model-agent/02-pretrain/core/model.py)
directly shows exactly how far that goes: `Transformer.forward` has exactly
one input path, `nn.Embedding(cfg.vocab_size, cfg.d_model)`, and
`Attention.forward` calls `scaled_dot_product_attention(q, k, v,
is_causal=True)` with no split for a non-causal or cross-attended input. None
of that is a bug — it is what a text-only decoder should look like. But it
means a vision pathway is not a flag to flip. It is a real patch-embedding
module and a real change to how attention conditions on a prefix, and this
mission is where that code gets written, not assumed.

The other reason this mission exists is a trap the metric itself can fall
into. A synthetic image+question set is easy to build so that the *question*
gives away the answer — "what color is the only shape" doesn't need the image
if there's only ever one shape. The text-only baseline below exists
specifically to catch that: if a decoder with no image input matches the
vision pathway's accuracy, the dataset leaked the answer through language, and
the vision pathway proved nothing.

## What gets measured

Two baselines, because each rules out a different way this mission could
report a false win.

The build-vs-buy question is a two-axis tradeoff: accuracy against dollar
cost per question. Three real points: the vision pathway (mean exact-match
0.4375, \$0 marginal), the text-only baseline (0.3270, \$0), and the hosted API
(0.8329, \$0.00128/question, `openai/gpt-4o-mini` via OpenRouter). The hosted
point dominates both self-trained points on both axes at once, which is why
this mission's verdict is a clean NOT MET rather than a "depends on your
budget" judgment call. The aggregate hides where the vision pathway's signal
is real: `shape_color` -- the one question type mathematically unanswerable
from question text alone -- is exactly where vision separates furthest from
text-only (50.1% vs 27.2%, an 84% relative lift), the strongest evidence the
pathway conditions on pixels, not memorized phrasing.

<!-- interactive: BuildVsBuyTradeoff -->

Hosted multimodal APIs got cheap fast: CLIP (Radford et al., 2021)
established that a single contrastively-pretrained vision-language model
could zero-shot a wide range of tasks, and by 2024 that capability was
available as a per-token API call rather than something every team needed to
train -- the economic shift this mission's build-vs-buy question tests
against, at toy scale.

**Hosted VLM API** answers the same question set through a single external
call, no training, no tuning. This is the build-vs-buy control: if this
mission's own trained pathway cannot beat a stock API call, building it was
not worth the compute.

**Text-only decoder** is the identical architecture and training run, minus
the image entirely — the question goes in, no pixels ever do. This is the
leakage control described above, and it is checked *before* the vision
pathway's number is trusted, not after.

Both are compared against the vision pathway on exact-match accuracy over a
held-out set, reported beside training wall-clock and cost. Train and eval
images come from disjoint random seeds, checked programmatically — the
mission contract's guardrail against memorization passing as sight.

## What this mission reuses, and what it has to build

Reused unmodified, by direct import from mission 01's own files rather than
reimplementation: RoPE, RMSNorm, SwiGLU, and the mixed-precision training loop
in
[`../01-language-model-agent/02-pretrain/core/model.py`](../01-language-model-agent/02-pretrain/core/model.py).
This is the same cross-mission convention mission 04 already uses to import
mission 01's agent harness — a `sys.path` import into that file's classes, not
a duplicated copy.

Built new, because nothing in the repository does this yet: a patch-embedding
module that turns an image into a short sequence of vision tokens, and a
fusion point in `Attention`/`Transformer` that lets the decoder condition on
that sequence as a prefix. Repo-wide search confirms there is no image, video,
or audio tensor pipeline anywhere else in this codebase — this mission is
where the first one is built and measured.

No new shared chapter is created for this. Mission 01's agent harness
was only promoted out of mission-local code once two missions independently
needed the same agent-loop contract; the same rule holds here. A future
`perceive-understand` capability — already anticipated in
[mission 02's README](../02-personalized-discovery/README.md) — gets created
only once a second mission needs the identical vision-encoder contract this
one builds, not before.

## Model lineage

The vision pathway is a point on the VLM line — contrastive pretraining
(CLIP, SigLIP), fusion (BLIP-2, LLaVA), native vision tokens (Qwen2-VL). The
[open-source line behind the vision-language model](../../reference/research/lineages/05-vision-language.md)
traces it, including the economic shift that made the hosted API dominant.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — Paired image-caption task](00-image-caption-task/) | what makes a scoreable image+question+answer instance, and how is train/eval leakage checked? | verified |
| [01 — Patch embed and vision-token fusion](01-vision-fusion/) | how does a text-only decoder learn to condition on an image, and does it beat a blind guess? | draft — partial result, 2 of 3 seeds beat the baseline but the mean gap is smaller than seed spread |
| [02 — Report](02-report/) | did the vision pathway add anything the hosted API or the text-only baseline couldn't already do? | verified — NOT MET, hosted API decisively wins |
| [03 — Real-photo task](03-real-photo-task/) | does the same leakage-controlled task design hold once images are real photographs instead of rendered shapes? | verified |
| [04 — Real-photo vision fusion](04-real-photo-vision-fusion/) | does the same vision pathway, unchanged, still separate from text-only on real photographs? | verified — real, narrow margin (+0.0152 vs 0.0101 spread) |
| [05 — Real-photo report](05-real-photo-report/) | does the real-photo vision pathway hold up against the hosted VLM API too? | verified — NOT MET, hosted API decisively wins on real photographs too |
| [06 — Warmup stability](06-warmup-stability/) | does a linear LR warmup close stage 01's seed-2 collapse? | verified — confirmed, spread tightened from 0.2309 to 0.0536 |

[Stage 00](00-image-caption-task/) generated 2,000 train and 400 eval
image+question+answer instances and found two real defects in its own
leakage guardrail before closing it: disjoint seed ranges produced 116
pixel-identical train/eval collisions, and the rejection-sampling fix that
first closed that gap silently emptied eval's single-shape bucket. Widening
each shape's size and position space fixed both — zero collisions, and
eval's shape-count distribution now proportional to train's. Full numbers in
[its run record](00-image-caption-task/runs/2026-07-31-dataset-gen.md).

[Stage 01](01-vision-fusion/) trained the vision pathway and the text-only
baseline for 3 seeds each. Two of three vision seeds beat every text-only
seed by 17-18 points — a real, decisive margin — but the third vision seed
collapsed below the text-only floor entirely, so vision's own seed-to-seed
spread (0.231) is larger than the gap between the two means (0.111). Per this
repository's own rule for a difference smaller than run-to-run spread, that
is reported as a partial result, not a clean win: the mechanism can clearly
learn to use the image, but training at this toy scale is unstable enough
that one seed in three failed to. Full numbers in
[its run record](01-vision-fusion/runs/2026-07-31-vision-vs-text-only.md).

[Stage 02](02-report/) added the third baseline mission.yaml required — a
real hosted VLM API call, `openai/gpt-4o-mini` via OpenRouter, on the
identical 784-question eval set, \$1.00 total — and mechanically checked all
three pathways against the mission's own acceptance bar. Verdict: **NOT
MET**. The hosted API scored 0.833 exact-match against the vision pathway's
0.4375 mean, a decisive build-vs-buy loss, not a close one. A per-category
breakdown also explains stage 01's seed-2 collapse concretely: that seed
does not miscount, it emits end-of-sequence immediately after the question
for `total_count` questions specifically, scoring exactly 0/100 there while
staying in line with the other seeds on every other category. Full numbers
in [its run record](02-report/runs/2026-07-31-hosted-api-full.md) and
[category breakdown](02-report/runs/2026-07-31-category-breakdown.md).

Per [the mission contract](mission.yaml), the contract above is declared
before any stage is built, so its baselines and metric cannot be chosen after
seeing which ones flatter the result — the same discipline every other
mission in this repository follows.

Stages 00-02 close the synthetic-shapes question completely: NOT MET, hosted
API wins decisively. Rather than stop there, `mission.yaml` was rescoped to
ask the same question again on real photographs, since a synthetic-shapes
result alone leaves open whether the leakage-control design and the vision
pathway's partial signal were artifacts of rendered data.

[Stage 03](03-real-photo-task/) rebuilt the task on a 300/100 image subset of
VQA v2 (real photographs, COCO val2014) — the leakage guardrail changes from
pixel-hash disjointness (appropriate for procedurally generated images that
can collide) to COCO image-id disjointness (real photographs essentially
never collide by pixel hash, but the same real image could appear in both
splits by id). Full numbers in
[its run record](03-real-photo-task/runs/2026-08-01-real-photo-dataset.md).

[Stage 04](04-real-photo-vision-fusion/) retrained stage 01's exact
architecture, zero code changes, on stage 03's real photographs: vision beats
text-only by a real, narrow margin (+0.0152, larger than vision's own
seed-to-seed spread of 0.0101) — the same direction as the synthetic result,
now confirmed on real data. Interestingly the seed-stability pattern flips:
text-only is the noisier pathway here (spread 0.0707), the opposite of stage
01's synthetic case. Full numbers in
[its run record](04-real-photo-vision-fusion/runs/2026-08-01-real-photo-vision-vs-text-only.md).

[Stage 05](05-real-photo-report/) added the hosted VLM API baseline on the
same real-photo eval set, \$0.2534 total. Verdict: **NOT MET** — hosted API
scored 0.4596 exact-match against vision's 0.2374 mean, a gap roughly 22x
vision's own seed spread, not a close call. The real-photo result matches the
synthetic one on the underlying build-vs-buy answer: buy, not build, at this
scale. Full numbers in
[its run record](05-real-photo-report/runs/2026-08-01-real-photo-report.md).


## Where each stage leaves the path

A stage states a decision; these deep-dive chapters answer the decisions
the main path asserts without showing, mission-01 style — each returns an
artifact or a measurement the next stage consumes.

| At this stage | You need to decide | So read |
|---|---|---|
| `00-image-caption-task` | Why does a leakage guardrail need to check pixels, not seeds? | [seed-vs-pixels](00-image-caption-task/seed-vs-pixels/) |
| `01-vision-fusion` | There is no cross-attention module | [the-fused-attention-anatomy](01-vision-fusion/the-fused-attention-anatomy/) |
| `01-vision-fusion` | Where does the decoder look when the image matters? | [where-the-decoder-looks](01-vision-fusion/where-the-decoder-looks/) |
| `02-report` | Where the NOT MET verdict hides the pathway's real signal | [when-the-category-breaks-down](02-report/when-the-category-breaks-down/) |
| `03-real-photo-task` | The real-photo guardrail: why image ID, not pixel hash | [the-real-photo-guardrail](03-real-photo-task/the-real-photo-guardrail/) |
| `04-real-photo-vision-fusion` | The margin is narrow, real, and noisy on the control side | [when-the-margin-is-narrow](04-real-photo-vision-fusion/when-the-margin-is-narrow/) |
| `05-real-photo-report` | The build-vs-buy verdict, on real photos | [when-the-api-still-wins](05-real-photo-report/when-the-api-still-wins/) |
| `06-warmup-stability` | What the warmup changed, and what it did not | [when-warmup-closed-the-collapse](06-warmup-stability/when-warmup-closed-the-collapse/) |


## What this will not prove

Nothing about frontier-scale vision-language capability — the model here
trains in minutes on a single consumer-grade GPU (or CPU, when that GPU lane
is unreachable, as it was for stages 04-05). Nothing about video, audio, or
any modality besides still images. Stages 03-05's real-photo result covers
only a 300/100-image slice of VQA v2's roughly 40,000-image validation set —
it says nothing about how the vision pathway would fare with more real-photo
training data, and nothing about which architecture choice is best in
general, only about the specific one this mission's stage 01/04 run records
measure. Full boundary in [`mission.yaml`](mission.yaml) under
`does_not_prove`.
