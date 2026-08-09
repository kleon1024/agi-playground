import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'space',
    carries: 'three ties at 0.500',
    label: 'The vector space',
    owns: 'Two towers map query and documents into one space; the ranking is whatever the training data placed near the query, not what token overlap says.',
    handoff: 'The space is the index, and its quality is the data that built it.',
  },
  {
    id: 'stale',
    carries: 'aggregate gap -0.330',
    label: 'The stale snapshot',
    owns: 'Between embedding re-runs the served vectors are stale; the mean gap of -0.330 makes the snapshot look usable.',
    handoff: 'Head queries survive a stale index; the tail does not.',
  },
  {
    id: 'tail',
    carries: 'tail recall 1.000 to 0.400',
    label: 'The tail divergence',
    owns: 'Head recall@5 drops 1.000 to 0.940 (gap -0.060) while tail drops 1.000 to 0.400 (gap -0.600) — every unit of the loss is tail recall.',
    handoff: 'Rare terms with few training examples lose most of their retrieval.',
  },
  {
    id: 'fix',
    carries: 'refresh for the tail',
    label: 'The fix',
    owns: 'Treat embedding freshness as a tail decision: refresh for the tail, or fall back to the hybrid path for queries the stale vectors cannot serve.',
    handoff: 'Hard negative sampling between ranks 101-500 decides tail representation in the first place.',
  },
];

export default function DenseRetrieval(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="An embedding that sees meaning, and a snapshot that loses the tail"
      question="Why does a stale embedding index diverge exactly where recall matters?"
      steps={STEPS}
      loop="The two-tower space is the index, and between re-runs it goes stale: the aggregate gap of -0.330 looks usable while head recall drops 1.000 to 0.940 and tail recall 1.000 to 0.400 — every unit of loss is tail recall. The fix treats freshness as a tail decision: refresh for the tail or fall back to the hybrid path."
    />
  );
}
