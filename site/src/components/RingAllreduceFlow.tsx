import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'split', carries: 'P local chunks', label: 'Split', owns: "Each rank's local gradient array split into P equal chunks.", handoff: 'P chunks per rank, ready to circulate around the ring.' },
  { id: 'reduce-scatter', carries: 'a running partial sum', label: 'Reduce-scatter', owns: 'P-1 steps of forwarding a running partial sum to the next rank in the ring.', handoff: 'After P-1 steps, each rank holds the fully-reduced value for exactly one chunk.' },
  { id: 'all-gather', carries: 'a finished chunk', label: 'All-gather', owns: "P-1 more steps circulating each rank's finished chunk around the same ring.", handoff: 'Every rank ends up holding the complete reduced result.' },
  { id: 'verify', carries: 'a correctness check', label: 'Verify', owns: "Asserting the ring's result against a plain single-process sum.", handoff: 'A correctness-checked reduced array, trusted before its timing is reported.' },
];

export default function RingAllreduceFlow(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One ring-allreduce"
      question="Where does ring's advantage over star actually come from?"
      steps={STEPS}
      loop="No rank is ever a bottleneck: every rank sends and receives the same amount of data at every one of the 2(P-1) steps. That flat per-rank cost — not a lower total cost — is what beats star as world_size grows, per the measured sweep above."
    />
  );
}
