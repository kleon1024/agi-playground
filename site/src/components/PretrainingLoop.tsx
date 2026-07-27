import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'batch', label: 'Batch', owns: 'Token IDs, targets, masks, and sequence shape.', handoff: 'A deterministic model input.' },
  { id: 'forward', label: 'Forward', owns: 'Logits under the current parameters.', handoff: 'Per-token prediction scores.' },
  { id: 'loss', label: 'Loss', owns: 'How wrong the next-token predictions are.', handoff: 'One scalar objective.' },
  { id: 'backward', label: 'Backward', owns: 'Credit assignment through every parameter path.', handoff: 'Accumulated gradients.' },
  { id: 'update', label: 'Update', owns: 'Optimizer state, clipping, and learning rate.', handoff: 'A new parameter state.' },
  { id: 'checkpoint', label: 'Checkpoint', owns: 'Weights, optimizer, scheduler, and exact resume step.', handoff: 'A reproducible continuation point.' },
];

export default function PretrainingLoop(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One training step"
      question="Where can a numerically valid run still become unreproducible?"
      steps={STEPS}
      loop="The loop repeats, but the checkpoint is the durable boundary: saving weights without optimizer and scheduler state does not preserve the training trajectory."
    />
  );
}
