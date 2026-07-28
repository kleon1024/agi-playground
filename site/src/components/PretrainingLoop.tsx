import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'batch', carries: 'token IDs, targets, and masks', label: 'Batch', owns: 'Token IDs, targets, masks, and sequence shape.', handoff: 'A deterministic model input.' },
  { id: 'forward', carries: 'logits', label: 'Forward', owns: 'Logits under the current parameters.', handoff: 'Per-token prediction scores.' },
  { id: 'loss', carries: 'one scalar', label: 'Loss', owns: 'How wrong the next-token predictions are.', handoff: 'One scalar objective.' },
  { id: 'backward', carries: 'gradients', label: 'Backward', owns: 'Credit assignment through every parameter path.', handoff: 'Accumulated gradients.' },
  { id: 'update', carries: 'new parameters', label: 'Update', owns: 'Optimizer state, clipping, and learning rate.', handoff: 'A new parameter state.' },
  { id: 'checkpoint', carries: 'a resume point', label: 'Checkpoint', owns: 'Weights, optimizer, scheduler, and exact resume step.', handoff: 'A reproducible continuation point.' },
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
