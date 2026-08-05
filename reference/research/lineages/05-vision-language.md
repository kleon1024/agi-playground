---
level: reference
---

# The open-source line behind the vision-language model

> Dated survey, 2026-08-06. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this mission's verdict is NOT MET — the hosted API dominates
both self-trained points on accuracy and cost. That verdict is only
interpretable against the line that made hosted multimodal cheap: contrastive
pretraining, then fusion, then native vision tokens. This survey is that
line.

## Contrastive pretraining

**CLIP** (Radford et al., 2021) trained a vision encoder and a text encoder
with a contrastive objective over image-caption pairs, producing zero-shot
classification and a shared embedding space. **ALIGN** (Jia et al., 2021)
scaled the data with noisy web pairs; **SigLIP** (Zhai et al., 2023) replaced
the softmax contrastive loss with a sigmoid loss, cutting batch-size
dependency and improving stability. The tradeoff at this end is data scale
versus objective simplicity: bigger noisy pairs helped, and the loss shape
turned out to matter more than the encoder.

## Fusion

The caption-to-generation step is where the architectures diverge.
**Flamingo** (Alayrac et al., 2022) interleaved a frozen CLIP with gated
cross-attention; **BLIP-2** (Li et al., 2023) distilled the image through a
**Q-Former**; **LLaVA** (Liu et al., 2023) showed a single linear projection
plus instruction tuning beats the more elaborate connectors — the surprise
that shaped the field, because it said the connector's job is small next to
the tuning data. **Qwen-VL** (2023) and **Qwen2-VL** (2024) moved to native
vision tokens inside the decoder, abandoning the separate connector entirely.

## The leakage trap

The metric can lie without any model lying: a synthetic image+question set
where the question gives away the answer lets a text-only model score well,
so "the vision pathway sees" needs a text-only baseline as a control. The
repo's measured version: the vision pathway's exact-match 0.4375 against the
text-only 0.3270, with the separation concentrated exactly where the question
cannot leak — shape_color 50.1% versus 27.2%, an 84% relative lift.

## The economic shift

The line's end state is the build-versus-buy question this mission measures:
hosted multimodal went from "train CLIP yourself" (2021) to a per-token API
call (2024), and the repo's three-point comparison — 0.4375 at \$0 marginal,
0.3270 at \$0, 0.8329 at \$0.00128/question — is the tradeoff the line produced.

## Evidence boundary

Dated and attributed, not measured. The repo anchors — the three-point
comparison, the shape_color separation, the warmup spread tightening from
0.2309 to 0.0536 — cite their runs. The line does not settle whether
building is ever right; it says the hosted API's dominance is a real point
the mission has to beat, not a default to assume.
