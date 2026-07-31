import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'dataset', carries: '800 train / 150 eval motion clips', label: 'Dataset', owns: 'Clip generation and train/eval disjointness.', handoff: '800 train / 150 eval clips, $0, 2.7s.' },
  { id: 'codec', carries: 'a 64-way per-frame token vocabulary', label: 'Video codec', owns: 'Frame-to-token reconstruction quality.', handoff: 'A trained VQ-VAE, retrained in-process by every downstream run.' },
  { id: 'lm', carries: 'a greedy 4-frame completion', label: 'Generation model', owns: 'Beating the frame-repeat baseline on held-out clips.', handoff: 'MSE and exact-match results across 3 seeds.' },
  { id: 'report', carries: 'a MET/NOT MET verdict', label: 'Report', owns: 'Holding all three stages against mission.yaml, mechanically.', handoff: 'A verdict that cannot soften after seeing the numbers.' },
];

export default function Mission08ComputePipeline(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Mission 08 dependency chain -- 152.5s of a declared 1800s ceiling (8.5%)"
      question="Does this repository's compute discipline survive contact with video at all?"
      steps={STEPS}
      loop="The codec is retrained in-process by stage 02 rather than checkpointed, so its cost is paid again downstream -- not free reuse."
    />
  );
}
