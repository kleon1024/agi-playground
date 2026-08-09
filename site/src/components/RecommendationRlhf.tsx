import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'pair',
    carries: 'chosen vs rejected',
    label: 'Pairwise preference',
    owns: 'The supervision is which item the user would rather see, not a label on either item.',
    handoff: 'Both items are scored; the sigmoid of the difference is the probability the chosen one wins.',
  },
  {
    id: 'loss',
    carries: 'loss 2.19 total',
    label: 'Bradley-Terry loss',
    owns: 'The weakest pair contributes 1.17 of the 2.19 total, so the model spends most capacity fixing the preference it gets most wrong.',
    handoff: 'Optimize over sampled pairs, not over labels — the RLHF shape.',
  },
  {
    id: 'audit',
    carries: 'tail flips 4/10',
    label: 'Margin-stratified audit',
    owns: 'Pairs are stratified by margin under label noise; near-tie and wide-margin pairs are pooled in the aggregate.',
    handoff: 'Head pairs at margin 1.14 flip 0/10; tail pairs at margin 0.04 flip 4/10.',
  },
  {
    id: 'verdict',
    carries: 'aggregate 0.20 hides it',
    label: 'Stratified verdict',
    owns: 'Every flip is a near tie: label noise decides which item is reported as chosen, and the model learns a wrong gradient.',
    handoff: 'Sample pairs by margin, re-ask low-margin preferences, and evaluate on high-margin held-out pairs.',
  },
];

export default function RecommendationRlhf(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Preferences, margins, and the flips the aggregate hides"
      question="When does the ranker learn a preference that was never really there?"
      steps={STEPS}
      loop="The Bradley-Terry loss spends most of its capacity on the pair it gets most wrong, and the margin-stratified audit shows the failure mode: near-tie pairs flip 4/10 under label noise while wide-margin pairs stay at 0/10. The aggregate flip rate of 0.20 hides that every flip is a near tie, so the fix samples pairs by margin and evaluates on high-margin held-out pairs."
    />
  );
}
