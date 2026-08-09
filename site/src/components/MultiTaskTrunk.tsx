import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'naive',
    carries: 'ctr 0.582 / buy 0.461',
    label: 'Naive shared bottom',
    owns: 'One shared trunk, two losses summed: CTR (~10%) pulls the gradient far harder than purchase (~1%).',
    handoff: 'The sparse task is starved — final gradient norms read CTR 0.484 against buy 0.076.',
  },
  {
    id: 'balanced',
    carries: 'buy 0.660',
    label: 'Gradient-balanced loss',
    owns: 'Re-weighting the purchase loss so the sparse task can move the shared trunk.',
    handoff: 'The sparse task rescues outright: buy AUC 0.461 to 0.660 at a small CTR cost.',
  },
  {
    id: 'gated',
    carries: 'buy 0.564',
    label: 'Gated trunk (MMoE-lite)',
    owns: 'Separating task experts behind a gate — the structural answer that scales when the conflict is not one weight.',
    handoff: 'Lands between the two (buy 0.564, CTR 0.608): better than naive, not as strong as the hand-tuned weight here.',
  },
];

export default function MultiTaskTrunk(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Three trunks over a 10% CTR / 1% purchase cohort"
      question="What happens when one task owns the shared gradient?"
      steps={STEPS}
      loop="The click loss shapes the shared trunk because its loss is bigger and its positives denser: final gradient norms read CTR 0.484 against buy 0.076. Balancing the purchase loss rescues the sparse task outright (buy AUC 0.461 to 0.660); the gated trunk improves on naive without a hand-tuned weight, landing between the two. The conflict is a gradient-allocation problem before it is a structure problem."
    />
  );
}
