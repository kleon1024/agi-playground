import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'head',
    carries: 'p(order|click)',
    label: 'Order head',
    owns: 'A head trained on clicked impressions estimates p(order|click), not p(order|impression).',
    handoff: 'Read as a marginal, it overstates the order probability on the full exposure space.',
  },
  {
    id: 'broken',
    carries: '649/1,000 violations',
    label: 'Conditional as marginal',
    owns: 'The clicked population converts at a higher rate than the exposure space, so p(order) > p(click) on most impressions.',
    handoff: 'Impossible probabilities served downstream, at an order log-loss of 0.672.',
  },
  {
    id: 'chained',
    carries: 'log-loss 0.501',
    label: 'Chained read',
    owns: 'Multiply the click marginal by the order conditional at score time; monotonicity becomes structural.',
    handoff: 'Zero violations by construction, and the downstream stage receives the marginal it actually blends.',
  },
  {
    id: 'check',
    carries: 'free alert',
    label: 'Standing violation check',
    owns: 'The violation rate needs no labels, so it runs continuously on serving traffic as the gate.',
    handoff: 'Calibration must precede chaining — a 2.25x-overconfident click head manufactures a 0.27 order estimate.',
  },
];

export default function FunnelConsistency(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One head, two reads, impossible numbers"
      question="What happens when a conditional is served as a marginal?"
      steps={STEPS}
      loop="The broken read lands at order log-loss 0.672 with 649 of 1,000 impressions violating the funnel; the chained read drops to 0.501 with zero violations by construction. The chain is only as honest as its inputs, so calibration precedes chaining, and the violation rate runs free on serving traffic as the standing check."
    />
  );
}
