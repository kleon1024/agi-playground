import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'baseline',
    carries: 'greedy 0.062-0.078',
    label: 'Baseline collapse',
    owns: 'Stage 01 greedy ignores the board on all 3 seeds while sampled decode shows real signal (0.144-0.210).',
    handoff: 'The deployed policy reads only the argmax token, and the argmax ignores the board.',
  },
  {
    id: 'groups',
    carries: 'greedy 0.024-0.050',
    label: 'Smaller groups',
    owns: 'group_size=4 tests the Fan et al. 2025 finding; degenerate steps rise to 18, 4, 10 and every metric falls below baseline.',
    handoff: 'The trade is measured, not assumed: at this reward shape and scale, smaller groups cost variance the policy needs.',
  },
  {
    id: 'entropy',
    carries: 'greedy 0.078',
    label: 'Entropy bonus',
    owns: 'coef=0.01 raises mid-training entropy 1.3-1.7 nats, yet greedy success stays at baseline.',
    handoff: 'The bonus buys diversity the serving path never sees — it does not move which token wins the argmax.',
  },
  {
    id: 'verdict',
    carries: 'not a fix',
    label: 'The negative finding',
    owns: 'Neither dial is the fix; the sweep narrows the space and names the reward shape as the suspect next.',
    handoff: 'A negative result stated plainly is the finding, not a placeholder for a positive one.',
  },
];

export default function CollapseFix(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Two training-signal dials, one unchanged collapse"
      question="Is stage 01 greedy-decode collapse fixable by tuning the training signal alone?"
      steps={STEPS}
      loop="Smaller groups made every measured number worse across 3 seeds — more degenerate steps, lower greedy and sampled success — and the entropy bonus left both success metrics at baseline while measurably raising mid-training entropy. Both are real negative findings: the collapse resists training-signal dials at this scale, and the honest conclusion points at the reward shape, not a retry of the same dials."
    />
  );
}
