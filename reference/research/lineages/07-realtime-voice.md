---
level: reference
---

# The open-source line behind realtime voice

> Dated survey, 2026-08-06. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this mission's artifact is a waveform in, a discrete token
sequence through a from-scratch codec, and a waveform out — decoded one
chunk at a time. Where did the codec come from, and what did the line trade
to make audio tokens cheap enough for a language model to schedule?

## From waveforms to tokens

**WaveNet** (van den Oord et al., 2016) showed an autoregressive model can
generate raw audio, establishing that the waveform is learnable but
expensive sample-by-sample. **VQ-VAE** (van den Oord et al., 2017) made
audio discrete: an encoder, a vector-quantized codebook, and a decoder, so a
language model can operate over tokens instead of samples — with the known
failure the repo later measures, codebook collapse, where most of the
codebook goes unused.

## Residual quantization

**SoundStream** (Zeghidour et al., 2021) introduced residual vector
quantization (RVQ): the first codebook captures the coarse signal and each
next one quantizes the residual, so bitrate becomes a dial — more levels,
better quality, more tokens. **EnCodec** (Defossez et al., 2022) added
bandwidth control and trained with adversarial and commitment losses for
high-fidelity reconstruction at low bitrates. **DAC** (Kumar et al., 2023)
reworked the training to make RVQ stable at 44.1kHz. The tradeoff along this
line is tokens versus fidelity: RVQ makes quality a slider, and every level
is another token stream the serving loop has to schedule.

## Codec language models and collapse

**AudioLM** (Borsos et al., 2022) and **VALL-E** (Wang et al., 2023) trained
language models over codec tokens, proving the discrete route works for
speech. The stability line is where this repo's mission lands: **VQ-VAE-2**
(2019) introduced EMA updates to fight codebook collapse, and the repo's
codebook-reset stage measures the 2x2 — reset, EMA, both, neither — to find
which half actually did the work on its own seed-dependent failure.

## Streaming

Serving audio means committing to one chunk at a time, and the tradeoff is
the one every realtime system pays: the streaming pass sees less context, so
reconstruction quality and wall-clock both move, reported p50 and p95 rather
than a single average — the repo's offline-versus-streaming comparison is
that gap, measured instead of assumed.

## Evidence boundary

Dated and attributed, not measured. The repo anchors — the offline-versus-
streaming gap, the p50/p95 latency split, the codebook-reset 2x2 verdict —
cite their runs. The line does not settle which codec is best; it says the
token stream's cost and the collapse risk are the two things any codec
choice has to pay for.
