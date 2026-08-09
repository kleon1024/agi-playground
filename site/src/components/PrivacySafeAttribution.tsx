import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'counts',
    carries: '480 / 310 / 260',
    label: 'The true counts',
    owns: 'Attribution needs aggregated channel counts — search 480, display 310, email 260 — but privacy forbids publishing them, because an adversary could isolate an individual contribution.',
    handoff: 'Laplace noise at epsilon 2.0 protects the individual and blurs the aggregate.',
  },
  {
    id: 'noise',
    carries: 'display and email flip',
    label: 'The noisy rank',
    owns: 'At epsilon 2.0 the noise range is 100/epsilon = 50, and the draw flips display and email (both 275), so the rank that decides budget changed while the true order was clear.',
    handoff: 'The close pair flips on 12.9% of reports at the stage epsilon.',
  },
  {
    id: 'sweep',
    carries: '81% over 12 weeks',
    label: 'The flip probability',
    owns: 'Epsilon 5.0 (range 20) never flips the 50-count gap; epsilon 2.0 flips the close pair on 12.9% of reports, so twelve weekly reports have an 81% chance of at least one flipped allocation; epsilon 0.25 flips top-1 on 31.6%.',
    handoff: 'The privacy guarantee is unchanged in every row; the decision accuracy is not.',
  },
  {
    id: 'fix',
    carries: 'set epsilon to the gap',
    label: 'The fix',
    owns: 'Set epsilon against the decision-relevant gap, not the smallest count, and coarsen the report: a six-channel report flips on 87.6% of draws against 12.3% for three.',
    handoff: 'More reports dilute the budget: 100 reports at epsilon 0.02 each.',
  },
];

export default function PrivacySafeAttribution(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Noise that flips the order that spends the budget"
      question="Why does the budget follow the order of counts, and noise destroys order first?"
      steps={STEPS}
      loop="Attribution needs aggregated counts (search 480, display 310, email 260) that privacy forbids publishing raw. Laplace noise at epsilon 2.0, range 50, flips display and email, and the close pair flips on 12.9% of reports — an 81% chance over twelve weekly reports that the budget moves on noise. The fix is to set epsilon against the decision-relevant gap and coarsen the report to the noise floor."
    />
  );
}
