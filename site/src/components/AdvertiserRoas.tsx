import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'lifecycle',
    carries: '8.68 to 4.62',
    label: 'The advertiser lifecycle',
    owns: 'Weekly ROAS decays from 8.68 to 4.62 over four weeks as the already-inclined audience is exhausted — below the 5.0 target.',
    handoff: 'The advertiser leaves at the marginal dollar, not at the plateau.',
  },
  {
    id: 'average',
    carries: 'report clears 5.0',
    label: 'The average report',
    owns: 'Average ROAS stays above the 5.0 target from $1,000 to $3,000 of spend, so the report clears at every spend level.',
    handoff: 'The average mixes dollars that behave differently.',
  },
  {
    id: 'margin',
    carries: 'next dollar returns 1.96',
    label: 'The marginal read',
    owns: 'Marginal ROAS clears the target only on the first $500 increment (5.21) and falls to 1.96 on the last: the report says 5.21x while the next dollar returns 1.96x.',
    handoff: 'A budget decided on the margin stops at $1,500; the average keeps spending.',
  },
  {
    id: 'fix',
    carries: 'decide at the margin',
    label: 'The fix',
    owns: 'Scale and cut against marginal ROAS: a cut from the top loses $980 per $500 where the same cut from the first increment loses $2,604.',
    handoff: 'The marginal number is the expensive one, needing the incrementality experiments stage 30 owns.',
  },
];

export default function AdvertiserRoas(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="An average report that says on target while the next dollar loses"
      question="Why does the average ROAS hide the margin the advertiser walks away on?"
      steps={STEPS}
      loop="Weekly ROAS decays from 8.68 to 4.62, below the 5.0 target, as the inclined audience is exhausted. Average ROAS stays above 5.0 from $1,000 to $3,000 while marginal ROAS clears the target only on the first increment (5.21) and falls to 1.96 on the last — the report says 5.21x while the next dollar returns 1.96x. A budget decided at the margin stops at $1,500."
    />
  );
}
