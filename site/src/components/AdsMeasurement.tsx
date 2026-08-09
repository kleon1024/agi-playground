import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'increment',
    carries: 'lift 14.3%, increment 0.4 pts',
    label: 'The increment',
    owns: 'Exposed 0.032 vs control 0.028: the ad actual effect is 0.4 points, not the 0.032 raw click rate.',
    handoff: 'The part the ad actually caused is the increment, not the exposed rate.',
  },
  {
    id: 'noise',
    carries: 'p = 1.000 at n=8,000',
    label: 'Buried in noise',
    owns: 'At 8,000 users per arm the observed lift is 0.0000 and the CI covers zero — the noise floor swallows the signal.',
    handoff: 'The same sample sees a 1-point increment clearly (p < 0.001) where the 0.4-point increment is invisible (p = 0.416).',
  },
  {
    id: 'power',
    carries: 'n=20,000 p=0.040',
    label: 'Sized for the effect',
    owns: 'The CI first excludes zero at 20,000 users per arm, and 80% power needs 28,547 users per arm.',
    handoff: 'The experiment is sized for the effect, and the headline increment is too small for the traffic most campaigns buy.',
  },
  {
    id: 'budget',
    carries: 'half-width 0.47 pts vs 0.4 pts',
    label: 'The budget decision',
    owns: 'A small lift read as a real lift misallocates the next budget; at 10,000 users per arm the honest result is we cannot tell.',
    handoff: 'Attribution without a control group is the click-rate version of the same overcount the increment corrects.',
  },
];

export default function AdsMeasurement(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A lift that paid for the campaign, invisible to the experiment that measured it"
      question="How do you know the ad worked, at the sample sizes a campaign can buy?"
      steps={STEPS}
      loop="The ad actual effect is 0.4 points, and at 8,000 users per arm the observed lift is 0.0000 with the CI covering zero. The CI first excludes zero at 20,000 users per arm — the production-scale spend a large campaign actually reaches — so the honest result at most campaign sizes is we cannot tell, and 80% power needs 28,547 users per arm."
    />
  );
}
