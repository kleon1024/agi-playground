---
status: draft
level: frontier
label: Multimodal generation
---

# Does one token-stream machine survive every modality a model can produce?

**Question:** every other topic in this repository conditions a decoder on one
1-D sequence of discrete token ids. Text is one such stream. Multimodal
generation asks whether the machine built for text — a codec that turns a
signal into discrete tokens, a KV-cached autoregressive decode loop, a
compute ceiling every quality claim is measured against — is actually about
tokens, or about text. Before asking whether a generated image, song, or clip
looks or sounds right, this topic asks a cheaper, prior question it can
actually answer: does the same token-stream machinery transfer to a waveform
and to a frame sequence, and what does each transfer cost?

**The artifact this topic follows** is two short clips: a waveform in, a
discrete token sequence through a from-scratch codec, and a reconstructed
waveform out, decoded one chunk at a time; and a generated sequence of frames,
produced from a seed condition, beside the exact GPU-hours or dollars it took
to train the model that produced it. Everything below is about what it takes
to trust that the tokens carried the signal, and at what price.

## Why this topic exists

[Topic 01](../01-language-model/) built a decoder — RoPE, RMSNorm, SwiGLU, a
training loop, a serving engine — entirely around a 1-D sequence of discrete
token ids. Its vision path
([`../01-language-model/`](../01-language-model/)) showed that a
new modality is not a flag to flip: a patch-embedding module and a
vision-token prefix are real new code, and a decoder with no image input is
the baseline that catches a dataset leaking the answer through language.

This topic is the same claim tested on the output side, for two more token
streams. A waveform becomes discrete through an audio codec; frames become
discrete through a video codec. Both are still integer sequences — the same
currency the serving loop already schedules — so the transfer question is
legitimate: does the KV-cache, paged-allocation, continuous-batching
mechanism built and measured for text work unchanged? Both sub-paths answer
that question with real runs, and both hit the same failure the vision path
and the text tokenizer already hit: a codebook that quietly stops using most
of itself. The collapse shows up in every modality because it is a property
of the vector-quantization bottleneck, not of the signal being quantized —
which is exactly the kind of claim this repository exists to check.

The compute question comes second but is never optional. Text tokens are
cheap enough that cost is an afterthought; a clip is dozens of frames and
each frame is hundreds of patch tokens, and a temporal model multiplies the
two. The declared discipline of this repository — real runs, a declared
compute lane, a hard dollar ceiling — is what makes a quality claim honest
here, and the video sub-path's report is structured around the finding that
cost decides first.

## What this topic covers, and what it declares but does not run

Two sub-paths are built and measured with real runs; the rest of the
multimodal scope is declared in [`mission.yaml`](mission.yaml) and mapped to
the closest runnable machinery rather than faked:

| Capability | Status | Where the runnable core lives |
|---|---|---|
| Speech: recognition, generation, interaction | Codec + streaming-token core run; ASR/TTS heads declared, not trained | [`voice/`](voice/) |
| Synthetic video generation | Run end to end, cost-first | [`video/`](video/) |
| Image generation | Declared; the video generation model applied to a single frame is the runnable subset | [`video/02-generation-model/`](video/02-generation-model/) |
| Music generation | Declared; the audio codec is the shared input half | [`voice/00-audio-codec/`](voice/00-audio-codec/) |
| World models | Declared; the autoregressive video-token model is the runnable subset | [`video/02-generation-model/`](video/02-generation-model/) |
| Text generation | Already built in topic 01 | [`../01-language-model/`](../01-language-model/) |

The distinction is deliberate and enforced by the mission contract: a
capability listed as declared has no `runs/` entry and no `verified` status,
and the README says so. The two sub-paths below are the parts where the
mechanism is actually measured.

## The shared skeleton

Every modality here pays for the same three things, and each sub-path
measures them in its own signal:

1. **A discrete codec.** Compression is what makes long sequences
   affordable, and compression is what loses detail. The audio codec and the
   video codec are different encoder/decoder architectures but the same
   vector-quantization bottleneck, and both pay the collapse tax: stage
   `voice/00` and `video/01` each report a first training attempt that
   collapsed to a dead codebook before escaping it.
2. **The serving loop.** The KV cache was built for text. Audio and video
   tokens are still integer streams, and the transfer test is the same:
   cached decode must produce identical output to full recompute, and its
   latency must stay flat where naive decode grows. `voice/01` runs that
   test against text-token serving code imported unchanged.
3. **The compute ceiling.** A quality number with no cost number beside it
   is an incomplete result in this topic. `video/03` reports the pipeline's
   total wall-clock against the declared ceiling; the same discipline
   applies to every voice run.

## Sub-paths

| Sub-path | Question | Status |
|---|---|---|
| [Video generation](video/) | is generated video affordable on one GPU, and what does a few seconds of synthetic footage cost? | 7 stages verified |
| [Realtime voice](voice/) | does the KV cache care whether the tokens are words or sound? | 7 stages verified |

[The video path](video/) moves from a scoreable synthetic clip (stage 00)
through a per-frame VQ-VAE codec (stage 01) to an autoregressive model over
video tokens (stage 02), then reports what the whole pipeline actually cost
(stage 03) before asking whether the feasibility finding survives longer
clips (stage 04), two occluding objects (stage 05), and both axes at once
(stage 06). Its finding is that the pipeline clears the declared ceiling at
8.5% of the budget, and that the quadratic attention cost would not stay
negligible at much longer clip lengths.

[The voice path](voice/) covers the three capabilities a voice interface
needs — recognition, generation, and interaction — as one token stream. The
codec (stage 00) is the input and output boundary both halves share;
streaming decode (stage 01) is the latency contract that makes interaction
feel live; the real-speech-and-network stage (stage 03) moves the same
machinery from synthetic tones onto LibriSpeech and a real network link; the
codebook-collapse fix stages (04-06) measure which half of VQ-VAE-2's
stability fix actually did the work. The ASR and TTS heads themselves are
declared scope, not trained here.

## Model lineage

The tokenizer and generation models are points on the multimodal line:
VQ-VAE for audio and video, SoundStream/EnCodec/DAC for the audio codec,
DiT/Sora for diffusion video, and the autoregressive alternative. The
[open-source line behind multimodal generation](lineage.md)
traces it, including why the cost question comes first.

## How to read this topic

If the question is "what did it cost and did it clear the ceiling", read the
video path. If the question is "does the text-token serving mechanism
transfer to another discrete-token stream", read the voice path — and then
return to the same question at the end of the video path, because the two
sub-paths' reports reach the same verdict from different directions.
