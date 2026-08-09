import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'zero',
    carries: '75% zero-result rate',
    label: 'The zero-result query',
    owns: 'Three of four queries return nothing: headphones is a vocabulary miss, wireless earbuds a catalog gap, heaphones a missing correction.',
    handoff: 'Every zero is a query the index cannot answer, and the cause decides the fix.',
  },
  {
    id: 'funnel',
    carries: 'aggregate 1.67% conversion',
    label: 'The funnel',
    owns: 'The aggregate funnel looks normal: 1.67% conversion and 5.9% zero-result rate.',
    handoff: 'A failing slice that is a small traffic fraction is invisible in the mean.',
  },
  {
    id: 'slice',
    carries: 'mobile-tail 25% zero',
    label: 'The hidden slice',
    owns: 'Mobile-tail, 11% of traffic, converts at 0.20% with a 25% zero-result rate — a third of the aggregate conversion.',
    handoff: 'A slice whose rate is a third of the aggregate is an incident, not a rounding error.',
  },
  {
    id: 'fix',
    carries: 'break every zero',
    label: 'The fix',
    owns: 'Report the funnel per slice and break every zero into its cause — catalog gap, misspelling, or vocabulary miss — because the same rate hides three failures with three different fixes.',
    handoff: 'Per-slice reporting costs slice attributes on every log line.',
  },
];

export default function SearchMeasurement(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Every zero-result query is a decision"
      question="Why does the funnel look flat while a slice is incident-sized?"
      steps={STEPS}
      loop="The zero-result rate of 75% (3 of 4 queries) hides three causes: vocabulary miss, catalog gap, missing correction. The funnel aggregate of 1.67% conversion looks normal while mobile-tail, 11% of traffic, converts at 0.20% with a 25% zero rate. The fix is per-slice reporting and a cause breakdown for every zero."
    />
  );
}
