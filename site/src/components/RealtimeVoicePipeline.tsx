import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'codec', carries: 'a 64-token discrete sequence', label: 'Audio codec', owns: 'Waveform-to-token reconstruction quality.', handoff: 'A 64-token sequence per clip, decodable back to waveform.' },
  { id: 'decode', carries: 'cached vs. naive completions', label: 'Streaming decode', owns: 'KV-cache correctness and per-chunk latency for audio tokens.', handoff: 'Logit-identical completions plus a latency profile at two scales.' },
  { id: 'report', carries: 'a MET/NOT MET verdict', label: 'Report', owns: 'Holding both results against mission.yaml, mechanically.', handoff: 'A verdict that cannot soften after seeing the numbers.' },
];

export default function RealtimeVoicePipeline(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Mission 07 dependency chain"
      question="Does a mechanism proven for text tokens transfer unchanged to audio tokens?"
      steps={STEPS}
      loop="If streaming decode ever needs a new serving primitive, that finding routes back to the codec's token contract, not to the serving stage's cache logic."
    />
  );
}
