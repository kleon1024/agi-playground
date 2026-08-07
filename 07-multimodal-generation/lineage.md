---
level: reference
---

# The open-source line behind multimodal generation

> Dated survey, 2026-08-07. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this topic asks the transfer question before the quality
question — is the token-stream machinery built for text actually about
tokens, or about text, and what does a few seconds of synthetic audio or
video cost to produce? Every architecture in the line answers that question
differently, and the answer changed twice.

## The shared discrete bottleneck

**VQ-VAE** (van den Oord et al., 2017) turned waveforms and images into
discrete tokens a decoder can condition on — the line's first answer, and the
bottleneck this topic builds from scratch twice. Its tradeoff is the
codebook's: compression is what makes long sequences affordable, and
compression is what loses detail. The failure this topic reproduces in both
signals is the same one the original paper had to fight: codebook collapse,
where most of the vocabulary goes unused and the model quietly learns to
ignore most of its own codes. **VQ-VAE-2** (Razavi et al., 2019) introduced
the EMA update and the two-stage hierarchy that later fixes build on, and the
voice sub-path's stage 06 measures which half of that fix actually did the
work.

## Audio

**WaveNet** (van den Oord et al., 2016) showed an autoregressive model can
generate raw audio, establishing that the waveform is learnable but expensive
sample-by-sample. **SoundStream** (Zeghidour et al., 2021) introduced residual
vector quantization (RVQ): the first codebook captures the coarse signal and
each next one quantizes the residual, so bitrate becomes a dial.
**EnCodec** (Defossez et al., 2022) added bandwidth control and trained with
adversarial and commitment losses; **DAC** (Kumar et al., 2023) made RVQ
stable at 44.1kHz. **AudioLM** (Borsos et al., 2022) and **VALL-E** (Wang et
al., 2023) trained language models over codec tokens, proving the discrete
route works for speech generation; Whisper (Radford et al., 2022) is the
recognition-side landmark that made a discrete token stream the input to
transcription at production scale. The realtime dialogue line — streaming
ASR, incremental TTS, turn-taking — is where the voice sub-path's latency
contract (p50/p95 per chunk, never an average) comes from.

## Images and video

**DiT** (Peebles & Xie, 2022) scaled diffusion from convolutional U-Nets to
transformers over latent patches; **Sora** (OpenAI, 2024) applied that swap
at video scale, a spacetime latent-patch DiT generating coherent minutes and
establishing that diffusion over video latents is where quality lives.
**VideoPoet** (2023) took the opposite route, a language model over video
tokens, and **Genie** (2024) pushed autoregressive world-model generation —
the line this topic's video sub-path sits on, at a scale many orders of
magnitude smaller. **VideoGPT** (Yan et al., 2021) paired a 3D VQ-VAE with a
causal transformer over the resulting token grid, the exact two-stage shape
the video sub-path's stages 01-02 follow. **CogVideoX** (2024) and **Wan**
(2025) are the open-weight answers on the cost line, trading quality for
feasibility at progressively larger but still finite budgets.

## The cost line

The open line since Sora is compute: a minute of video is hundreds of
latent-patch tokens per frame times dozens of frames, so cost scales
quadratically with resolution and duration. The repo's measured point is the
discipline the line makes necessary: the video sub-path's generation model
trains in 140.9s, a single generation in 0.05s, and the whole pipeline runs
at 8.5% of its declared ceiling — the cost number reported beside every
quality number, because a cost without a quality number and a quality
without a cost number are both incomplete.

## Evidence boundary

Dated and attributed, not measured. The repo anchors — the offline-versus-
streaming gap, the p50/p95 latency split, the codebook-collapse verdicts in
both signals, the video pipeline's 140.9s/0.05s wall-clocks — cite their
runs. The line does not settle which generation route "wins"; it says the
token stream's cost and the collapse risk are the two things any multimodal
choice has to pay for, which is exactly why this topic asks them first.

