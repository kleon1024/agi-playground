import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'capture', carries: 'a 0.512s speech clip', label: 'Capture', owns: 'A real LibriSpeech dev-clean utterance, chunked into the same CLIP_LEN=4096 format the procedural-tone stages already use.', handoff: 'A raw waveform chunk, ready for the unmodified codec.' },
  { id: 'encode', carries: 'a 64-token sequence', label: 'Encode', owns: "Stage 00's Codec, zero code changes, turning the waveform into discrete tokens.", handoff: 'A token sequence, the same vocabulary shape trained on tones or speech alike.' },
  { id: 'network-hop', carries: '8 int64 token ids each way', label: 'Network hop', owns: 'A real Tailscale round trip, Mac client to the remote 4090 host, measured with a stdlib-only echo server.', handoff: 'The same tokens, now measured with a real millisecond cost the in-process stages never had to pay.' },
  { id: 'decode', carries: 'a reconstructed waveform', label: 'Decode', owns: "Stage 01's KV-cache decode loop, unmodified, confirmed logit-identical to full recomputation on this speech vocabulary too.", handoff: 'A reconstructed waveform, scored against the reference clip.' },
];

export default function RealSpeechNetworkPipeline(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Real speech, real network"
      question="What does adding one real network hop cost, next to the mechanism that was already measured in-process?"
      steps={STEPS}
      loop="Local cached decode alone costs p50 ~1.1ms (stage 01). Add the real Tailscale hop measured here — p50 9.66ms, p95 42.46ms — and the network, not the cache, becomes the bottleneck for any deployment that splits capture from decode across machines."
    />
  );
}
