import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'decay',
    carries: '0.050 to 0.002',
    label: 'CTR decays with exposure',
    owns: 'CTR falls from 0.050 on the first exposure to 0.002 on the seventh, so the marginal impression value collapses and the cap is a value decision.',
    handoff: 'A cap at three keeps the high-value exposures; uncapped, delivery burns near-zero click value.',
  },
  {
    id: 'aggregate',
    carries: 'CTR 0.0328',
    label: 'The aggregate curve',
    owns: 'Aggregate CTR across 20,000 impressions reads 0.0328, the standard segment own number, so a cap read off the aggregate looks healthy.',
    handoff: 'The aggregate is the curve the report shows; the dead slice is what it hides.',
  },
  {
    id: 'slice',
    carries: 'power 40.6% dead',
    label: 'The segment that stopped',
    owns: 'The power slice runs at 0.0133 with 40.6% of impressions at or below 0.005, while a global cap 3 sacrifices 28.5 casual clicks to save 7.3 power clicks.',
    handoff: 'Per-segment caps (casual 7, standard 3, power 2) cut 6,152 impressions and lose zero casual clicks.',
  },
  {
    id: 'fix',
    carries: 'per-segment caps',
    label: 'The fix',
    owns: 'Caps keyed to a stable identity counter: fatigue is per segment and delivery is per identity, so a reset counter serves 6,167 extra impressions at a third of the first-three click value.',
    handoff: 'The identity and measurement teams own the counter the cap reads.',
  },
];

export default function FrequencyCapping(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A cap that keeps serving the segment that stopped clicking"
      question="Why does a cap read off the aggregate curve serve the wrong slice?"
      steps={STEPS}
      loop="CTR decays from 0.050 to 0.002 across seven exposures, so the cap is a value decision. Aggregate CTR of 0.0328 looks healthy while the power slice runs at 0.0133 with 40.6% dead impressions; a global cap 3 sacrifices 28.5 casual clicks to save 7.3 power clicks, where per-segment caps (casual 7, standard 3, power 2) cut 6,152 impressions and lose zero casual clicks. The counter is load-bearing, so the cap lives on a stable identity object."
    />
  );
}
