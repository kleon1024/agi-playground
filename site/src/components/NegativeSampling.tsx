import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'full',
    carries: 'AUC 0.659 / ECE 0.011',
    label: 'Full set',
    owns: 'A 1:1000 positive rate, so the gradient is mostly easy negatives and the positives barely get a vote.',
    handoff: 'The base rate the model is supposed to report: one positive per thousand.',
  },
  {
    id: 'downsample',
    carries: 'AUC 0.659 / ECE 0.473',
    label: 'Downsample negatives',
    owns: 'Negatives cut 10x so the positives get a vote; pairwise order between positives and the sampled negatives survives.',
    handoff: 'The ranking holds, but the base rate inside the model changes — probabilities inflate by the sampling factor.',
  },
  {
    id: 'correct',
    carries: 'ECE 0.017',
    label: 'Invert the ratio',
    owns: 'Invert the sampling ratio at prediction time so the model probability maps back onto the true base rate.',
    handoff: 'ECE recovers; AUC does not move in any row, because a monotone inflation never breaks pairwise order.',
  },
  {
    id: 'log',
    carries: 'logged ratio',
    label: 'Logging contract',
    owns: 'The correction is only as good as the ratio actually applied at sampling time; a mislogged ratio passes straight through.',
    handoff: 'A ratio assumed is a ratio wrong — the overcorrects detour lands the corrected probability half a decimal off.',
  },
];

export default function NegativeSampling(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One ranking, three calibrations"
      question="Why does downsampling negatives keep AUC and inflate every probability?"
      steps={STEPS}
      loop="AUC is 0.659 in every row — the downsampled model ranks identically — while ECE moves from 0.011 to 0.473 and back to 0.017. Ranking metrics never see the break, and the value tree, auction, and pacing multiply whatever probability they receive, so the inflated scale is a product-wide defect that AUC-based acceptance gates wave through."
    />
  );
}
