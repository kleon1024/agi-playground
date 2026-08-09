import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'reorder',
    carries: '4 of 5 positions change',
    label: 'The reorder',
    owns: 'The first stage ranks d1, d2, d3, d4, d5 with cheap features; the reranker reorders to d4, d2, d5, d1, d3 with richer ones.',
    handoff: 'The first stage recalls, the reranker refines — a latency budget split.',
  },
  {
    id: 'k',
    carries: 'evaluated @10, served @3',
    label: 'The k mismatch',
    owns: 'The @10 experiment approves the reranker (aggregate +0.080) while the served @3 report says the page got worse (-0.015).',
    handoff: 'The reranker fixes land in the middle of the list, below the three served slots.',
  },
  {
    id: 'tail',
    carries: 'tail +0.080 @10, -0.080 @3',
    label: 'The head and tail split',
    owns: 'The head stratum agrees at @10 and @3 (delta +0.080/+0.050), while the tail improves +0.080 at @10 and degrades -0.080 at @3.',
    handoff: 'The aggregate approves a fix that only helps the middle of the list.',
  },
  {
    id: 'fix',
    carries: 'report at served k',
    label: 'The fix',
    owns: 'Evaluate the reranker at the served k, audit per position, and slice the experiment by head and tail before shipping.',
    handoff: 'Cross-encoder latency is why the shortlist is short and the served page shorter.',
  },
];

export default function Reranking(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A second ranker that fixes the first, evaluated at a k the page never serves"
      question="Why does the @10 experiment approve a reranker the @3 page reports as worse?"
      steps={STEPS}
      loop="The reranker reorders 4 of 5 positions, but its fixes land in the middle of the list: the @10 experiment approves it (aggregate +0.080) while the served @3 report says the page got worse. The tail improves +0.080 at @10 and degrades -0.080 at @3. The fix is to evaluate at the served k, audit per position, and slice by head and tail."
    />
  );
}
