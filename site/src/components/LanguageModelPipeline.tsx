import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'corpus', label: 'Corpus', owns: 'Text quality, provenance, and splits.', handoff: 'A versioned training shard.' },
  { id: 'tokenizer', label: 'Tokenizer', owns: 'The reversible text-to-ID contract.', handoff: 'Stable token IDs and vocabulary.' },
  { id: 'pretrain', label: 'Base model', owns: 'Next-token representations and checkpoint shape.', handoff: 'A loadable base checkpoint.' },
  { id: 'adapt', label: 'Adapt', owns: 'Instruction behavior and preference objectives.', handoff: 'A policy with explicit behavior changes.' },
  { id: 'serve', label: 'Serve', owns: 'Generation latency, memory, and request scheduling.', handoff: 'A bounded generation API.' },
  { id: 'agent', label: 'Harness', owns: 'Tools, permissions, context, and stop conditions.', handoff: 'Observable trajectories.' },
  { id: 'eval', label: 'Evaluate', owns: 'Tasks, variance, failures, and claim limits.', handoff: 'Evidence that revises the corpus or system.' },
];

export default function LanguageModelPipeline(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Mission 01 dependency chain"
      question="Which artifact becomes the next stage's contract?"
      steps={STEPS}
      loop="A failure discovered by evaluation must be attributed to the owning stage. Otherwise teams change the model when the defect is in data, serving, or the harness."
    />
  );
}
