import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'cut',
    carries: '1500 -> 100',
    label: 'The cut',
    owns: 'The cascade cuts 1,500 candidates to 100 before the expensive ranker; the cut is a hard filter no downstream model can undo.',
    handoff: 'The pre-rank objective decides what survives, so the cut decides what the ranker can rank.',
  },
  {
    id: 'ctr',
    carries: 'top-20 recall 0.35',
    label: 'CTR-optimized pre-rank',
    owns: 'Optimizing clicks keeps the clicky items and ejects the transaction-heavy ones the final ranker values.',
    handoff: 'Only 0.35 of the final top-20 survives; final NDCG 0.967 still looks fine because it measures survivors.',
  },
  {
    id: 'distill',
    carries: 'final NDCG 1.000',
    label: 'Distilled pre-rank',
    owns: 'Distill the final score into the pre-rank as a soft label, so the cut keeps the top of the final ranking inside.',
    handoff: 'Top-20 recall 1.00 and the final ranker sees the items it values.',
  },
  {
    id: 'metric',
    carries: 'top-K recall',
    label: 'Top-K recall at the cut',
    owns: 'The metric that matters across a cascade, because no downstream model re-ranks an item the cut already removed.',
    handoff: 'Distillation inherits the teacher mistakes — audit the teacher when the final ranker changes.',
  },
];

export default function CascadeConsistency(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="The cut decides what the ranker can rank"
      question="What should the cheap pre-rank optimize?"
      steps={STEPS}
      loop="A click-optimized pre-rank keeps only 0.35 of the final top-20 at the cut while final NDCG reads 0.967 — the blind spot is real but invisible on survivors. Distilling the final score into the pre-rank moves top-20 recall to 1.00 and final NDCG to 1.000, at the price of depending on a teacher whose stability and calibration must be audited."
    />
  );
}
