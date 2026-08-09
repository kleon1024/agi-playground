import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'exposure',
    carries: 'accessories 1% to 9%',
    label: 'Exposure as a budget',
    owns: 'A click-optimal ranker gives audio 59%, video 30%, cable 10%, accessories 1%; a 10% floor moves accessories to a real share at a measured CTR cost (0.0355 to 0.0334).',
    handoff: 'Every fairness decision is a budget decision about how much relevance to spend on a visible tail.',
  },
  {
    id: 'gap',
    carries: '10% floor lands at 9.2%',
    label: 'The declared versus served',
    owns: 'A declared 10% floor lands at 9.2% served exposure, and the gap grows with the floor: at 15% only 12.6% is served.',
    handoff: 'Renormalising after flooring the other categories re-dilutes the group the floor was meant to protect.',
  },
  {
    id: 'definition',
    carries: 'mobile segment misses at 8%',
    label: 'The group definition',
    owns: 'The tail clears its 10% floor across the catalogue (10.1%) while the mobile segment, 70% of traffic, leaves it at 8% — who counts as protected is a policy decision made before the measurement.',
    handoff: 'Position-adjusted CTR moves the tail from 14% to 36% of exposure.',
  },
  {
    id: 'fix',
    carries: 'solve with the floor binding',
    label: 'The fix',
    owns: 'Solve the constrained allocation with the floor binding instead of max-then-renormalise, and measure the protected group served exposure, not the declared floor.',
    handoff: 'The first ten points of floor cost 0.0021 aggregate CTR; the price is a curve, not a flat rate.',
  },
];

export default function FairnessAllocation(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A declared floor that is not the exposure the protected group receives"
      question="Why does the served allocation miss the configured fairness floor?"
      steps={STEPS}
      loop="Exposure is a budget the ranker allocates: unconstrained, audio takes 59% and accessories 1%; a 10% floor moves the tail at 0.0021 aggregate CTR. The declared floor is not the served allocation — 10% lands at 9.2%, and 15% at 12.6%, because renormalising dilutes the group the floor protects. Measure per-group exposure and solve with the floor binding instead of max-then-renormalise."
    />
  );
}
