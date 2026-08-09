import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'window',
    carries: '7-day window',
    label: 'Label window',
    owns: 'Defining a conversion label by a fixed window over a young snapshot (0.3-3d).',
    handoff: 'A label that is censored: conversions still in flight are called negatives.',
  },
  {
    id: 'mature',
    carries: '0 mature rows',
    label: 'Mature-only',
    owns: 'Waiting for the window to fully age before training — on a young snapshot there is no mature set to wait for.',
    handoff: 'Starved by definition: no rows, no model.',
  },
  {
    id: 'naive',
    carries: 'pred 0.092',
    label: 'Naive-all',
    owns: 'Keeping every row and eating the 581 in-flight converters as false negatives.',
    handoff: 'CVR under-read on fresh traffic — the dip every launch sees (true 0.132 vs predicted 0.092).',
  },
  {
    id: 'corrected',
    carries: 'pred 0.142',
    label: 'Corrected soft label',
    owns: 'Giving censored rows a soft label from the delay distribution and the base rate, keeping all rows.',
    handoff: 'Freshness stops costing scale: conv AUC 0.672 with predicted 0.142 against a true 0.132.',
  },
];

export default function DelayedFeedbackWindow(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A 7-day window on a 3-day-old snapshot"
      question="Why does the CVR dip on every launch, and what actually fixes it?"
      steps={STEPS}
      loop="Mature-only is starved because there are no mature rows yet; naive-all keeps scale but labels 581 in-flight converters as negatives and under-reads fresh traffic (0.092 against a true 0.132). The corrected scheme keeps all rows and gives censored rows a soft label from the delay distribution and the base rate, so freshness stops costing scale — conv AUC 0.672 with a predicted 0.142."
    />
  );
}
