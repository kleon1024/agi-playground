import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'log',
    carries: 'shown vs liked',
    label: 'Logged interactions',
    owns: 'What was shown was decided by the previous model, so exposure is confounded with the old score and with position.',
    handoff: 'A popular item is shown more, placed higher, and clicked more for reasons that have nothing to do with liking.',
  },
  {
    id: 'naive',
    carries: 'corr 0.874',
    label: 'Naive on log',
    owns: 'Training on the log as-is learns "shown often" as if it were "liked", strongest exactly where the confound is.',
    handoff: 'Looks fine on the items the old model showed a lot, and is blind everywhere else.',
  },
  {
    id: 'ips',
    carries: 'corr 0.962',
    label: 'IPS reweighting',
    owns: 'Reweight each logged row by the inverse exposure propensity; removes the selection confound, not position.',
    handoff: 'A small noisy propensity inverts to a huge weight — the noisy read collapses to 0.376 before a cap restores it.',
  },
  {
    id: 'random',
    carries: 'corr 0.995',
    label: 'Random exposure',
    owns: 'A small bucket that shows items uniformly; the only data clean of both selection and position bias.',
    handoff: 'The gold reference, bought with real traffic that does not optimize the current policy.',
  },
];

export default function ExposureBias(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Three ways to read the same log"
      question="How much can a model trust what the old model showed?"
      steps={STEPS}
      loop="The naive model ranks well on the items the old model showed a lot and is blind elsewhere; IPS moves quality rank correlation from 0.874 to 0.962 but is high-variance exactly where it matters — a noisy propensity collapses it to 0.376. Random exposure is the only clean reference at 0.995, and its price is traffic that does not optimize the current policy."
    />
  );
}
