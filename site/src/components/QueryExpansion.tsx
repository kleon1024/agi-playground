import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'distance',
    carries: 'headphones 1 edit away',
    label: 'The correction',
    owns: 'heaphones sits one edit from headphones (and five from the next candidate); the raw query matches nothing in the index, the corrected query matches the catalog.',
    handoff: 'The value of a correction is the recall it recovers, not its distance score.',
  },
  {
    id: 'aggregate',
    carries: 'aggregate +0.233',
    label: 'The aggregate lift',
    owns: 'Over a 24-query log the expansion reports a +0.233 recall lift, as if it applied everywhere.',
    handoff: 'Head queries dominate the average, and the average cannot see who was repaired.',
  },
  {
    id: 'stratum',
    carries: 'all lift is tail',
    label: 'The stratified read',
    owns: 'Head queries recover 0.000 (base and expanded both 1.000) while taking on 1.00 irrelevant hit each; the tail carries all of the +0.467 lift (0.350 to 0.817).',
    handoff: 'Expansion buys tail recall at the price of head precision.',
  },
  {
    id: 'fix',
    carries: 'gate by stratum',
    label: 'The fix',
    owns: 'Gate expansion by stratum instead of shipping it everywhere on the strength of the average; local per-query analysis beats global expansion.',
    handoff: 'The gate costs an audit on every policy change.',
  },
];

export default function QueryExpansion(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A correction that decides which query you meant"
      question="Why is expansion lift concentrated in the tail?"
      steps={STEPS}
      loop="Correction is measured by the recall it recovers: heaphones is one edit from headphones, and the corrected query hits the catalog. Over a 24-query log the aggregate +0.233 lift hides that head queries recover nothing while taking on 1.00 irrelevant hit each, and the tail carries all of the +0.467 lift. The fix is to gate expansion by stratum, not ship it everywhere."
    />
  );
}
