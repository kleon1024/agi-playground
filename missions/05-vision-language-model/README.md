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

No new shared capability is created for this. `capabilities/act-coordinate`
was only promoted out of mission-local code once two missions independently
needed the same agent-loop contract; the same rule holds here. A future
`perceive-understand` capability — already anticipated in
[mission 02's README](../02-personalized-discovery/README.md) — gets created
only once a second mission needs the identical vision-encoder contract this
one builds, not before.

## Stages

| Stage | Question | Status |
|---|---|---|
| 00 — Paired image-caption task | what makes a scoreable image+question+answer instance, and how is train/eval leakage checked? | not started |
| 01 — Patch embed and vision-token fusion | how does a text-only decoder learn to condition on an image, and does it beat a blind guess? | not started |
| 02 — Report | did the vision pathway add anything the hosted API or the text-only baseline couldn't already do? | not started |

Per [the mission contract](mission.yaml), the contract above is declared
before any stage is built, so its baselines and metric cannot be chosen after
seeing which ones flatter the result — the same discipline every other
mission in this repository follows.

## What this will not prove

Nothing about real photographs — the dataset is synthetic by construction.
Nothing about frontier-scale vision-language capability — the model here
trains in minutes on a single consumer-grade GPU. Nothing about video, audio,
or any modality besides still images, and nothing about which architecture
choice is best in general, only about the specific one this mission's stage 01
run record measures. Full boundary in [`mission.yaml`](mission.yaml) under
`does_not_prove`.
